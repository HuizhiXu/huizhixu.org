import hashlib
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from publishing import config
from publishing.http import notion_request
from publishing.markdown import convert_page
from publishing.replace import replace_blocks
import requests

# Import entrypoints without loading the user's credentials.
with patch.object(config, 'load_local_env'):
    blog = importlib.import_module('notion_to_blog')
    obsidian = importlib.import_module('obsidian_to_notion')
    backfill = importlib.import_module('blog_to_obsidian')
from check_site import check_manifest


def text(value, **kwargs):
    return {'type': 'text', 'plain_text': value, **kwargs}


def block(kind, value='', **kwargs):
    return {'id': kind, 'type': kind, kind: {'rich_text': [text(value)]}, **kwargs}


class ConversionTests(unittest.TestCase):
    def convert(self, blocks, nested=None):
        nested = nested or {}
        def request(method, path, **kwargs):
            return {'results': blocks if path == '/blocks/page/children' else nested[path], 'has_more': False}
        return convert_page('page', request, lambda data: 'https://example.com/image.png')

    def test_links_annotations_quote(self):
        paragraph = block('paragraph')
        paragraph['paragraph']['rich_text'] = [text('Example', href='https://example.com', annotations={'bold': True})]
        result = self.convert([paragraph, block('quote', 'A quotation')])
        self.assertIn('[**Example**](<https://example.com>)', result)
        self.assertIn('> A quotation', result)

    def test_nested_list(self):
        parent = block('numbered_list_item', 'Parent', has_children=True)
        result = self.convert([parent], {'/blocks/numbered_list_item/children': [block('bulleted_list_item', 'Child')]})
        self.assertIn('1. Parent\n\n   - Child', result)

    def test_table_without_header_preserves_first_row(self):
        table = {'id': 'table', 'type': 'table', 'has_children': True,
                 'table': {'table_width': 2, 'has_column_header': False}}
        row = {'type': 'table_row', 'table_row': {'cells': [[text('A|B')], [text('C')]]}}
        result = self.convert([table], {'/blocks/table/children': [row]})
        self.assertIn('| --- | --- |\n| A\\|B | C |', result)

    def test_table_with_header(self):
        table = {'id': 'table', 'type': 'table', 'has_children': True,
                 'table': {'table_width': 1, 'has_column_header': True}}
        rows = [{'type': 'table_row', 'table_row': {'cells': [[text(t)]]}} for t in ['Header', 'Value']]
        self.assertIn('| Header |\n| --- |\n| Value |', self.convert([table], {'/blocks/table/children': rows}))

    def test_code_fence_preserves_backticks(self):
        code = block('code', '```example```')
        code['code']['language'] = 'plain text'
        self.assertIn('````text\n```example```\n````', self.convert([code]))

    def test_unknown_block_stops_export(self):
        with self.assertRaisesRegex(ValueError, '不支持'):
            self.convert([block('unsupported')])

    def test_pagination(self):
        request = Mock(side_effect=[{'results': [block('paragraph', 'First')], 'has_more': True, 'next_cursor': 'next'},
                                    {'results': [block('paragraph', 'Last')], 'has_more': False}])
        result = convert_page('page', request, Mock())
        self.assertIn('First', result)
        self.assertIn('Last', result)
        self.assertEqual(request.call_args.kwargs['params']['start_cursor'], 'next')


class ReplacementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.calls = []
        self.children = Mock(return_value=[{'id': 'old'}])
        self.blocks = [block('paragraph', str(i)) for i in range(101)]
        self.batch = 0

    def request(self, method, path, json_data):
        self.calls.append((path, json_data))
        if path.endswith('/children'):
            self.batch += 1
            return {'results': [{'id': f'new-{self.batch}-{i}'} for i in range(len(json_data['children']))]}
        return {}

    def run_replace(self, request=None):
        replace_blocks('page', self.blocks, {}, request or self.request, self.children, self.temp.name)

    def test_old_blocks_archived_only_after_all_batches(self):
        self.run_replace()
        paths = [path for path, _ in self.calls]
        self.assertEqual(paths[:3], ['/blocks/page/children', '/blocks/page/children', '/blocks/old'])
        self.assertFalse(list(Path(self.temp.name).glob('*.json')))

    def test_rejected_second_batch_preserves_old_and_cleans_new(self):
        def request(method, path, json_data):
            if path.endswith('/children') and self.batch == 1:
                response = requests.Response()
                response.status_code = 400
                raise requests.HTTPError(response=response)
            return self.request(method, path, json_data)
        with self.assertRaises(requests.HTTPError):
            self.run_replace(request)
        self.assertNotIn(('/blocks/old', {'archived': True}), self.calls)
        self.assertIn(('/blocks/new-1-0', {'archived': True}), self.calls)
        self.assertFalse(list(Path(self.temp.name).glob('*.json')))

    def test_timeout_keeps_journal_and_blocks_blind_retry(self):
        request = Mock(side_effect=requests.Timeout('uncertain write'))
        with self.assertRaises(requests.Timeout):
            self.run_replace(request)
        journal = json.loads((Path(self.temp.name) / 'page.json').read_text())
        self.assertTrue(journal['append_pending'])
        with self.assertRaisesRegex(RuntimeError, '上次同步未完成'):
            self.run_replace()
        self.assertEqual(request.call_count, 1)

    def test_property_failure_restores_old_content_before_cleanup(self):
        def request(method, path, json_data):
            if path == '/pages/page':
                raise RuntimeError('property failure')
            return self.request(method, path, json_data)
        with self.assertRaises(RuntimeError):
            self.run_replace(request)
        restore = self.calls.index(('/blocks/old', {'archived': False}))
        cleanup = self.calls.index(('/blocks/new-1-0', {'archived': True}))
        self.assertLess(restore, cleanup)

    def test_failed_restore_keeps_replacement_and_journal(self):
        def request(method, path, json_data):
            if path == '/pages/page' or json_data == {'archived': False}:
                raise RuntimeError('outage')
            return self.request(method, path, json_data)
        with self.assertRaises(RuntimeError):
            self.run_replace(request)
        self.assertNotIn(('/blocks/new-1-0', {'archived': True}), self.calls)
        self.assertTrue((Path(self.temp.name) / 'page.json').exists())


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(blog, 'REPO_ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.page = {'id': 'page', 'last_edited_time': 'v1', 'properties': {
            'Title': {'title': [text('Title')]}, 'PublishStatus': {'select': {'name': 'Publish'}},
            'MDFilename': {'rich_text': [text('article.md')]}}}
        self.network = patch('requests.request', side_effect=AssertionError('No real network allowed'))
        self.network.start()
        self.addCleanup(self.network.stop)

    def manifest(self):
        path = self.root / 'content/chs/know_how/article.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('article')
        manifest = self.root / 'publish.json'
        manifest.write_text(json.dumps({'complete': True, 'pages': [{'id': 'page', 'last_edited_time': 'v1',
            'path': str(path.relative_to(self.root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}]}))
        return manifest

    def test_export_does_not_mark_published(self):
        with patch.object(blog, 'convert_notion_blocks_to_markdown', return_value='Body'), patch.object(blog, 'notion_request') as request:
            entry = blog.process_notion_page(self.page)
        request.assert_not_called()
        self.assertTrue((self.root / entry['path']).exists())

    def test_export_retry_updates_same_page(self):
        with patch.object(blog, 'convert_notion_blocks_to_markdown', side_effect=['First', 'Second']):
            blog.process_notion_page(self.page)
            entry = blog.process_notion_page(self.page)
        self.assertIn('Second', (self.root / entry['path']).read_text())

    def test_update_keeps_hugo_metadata(self):
        with patch.object(blog, 'convert_notion_blocks_to_markdown', return_value='Body'):
            entry = blog.process_notion_page(self.page)
            path = self.root / entry['path']
            path.write_text(path.read_text().replace('title: Title', 'title: Title\nmath: true'))
            blog.process_notion_page(self.page)
        self.assertIn('math: true', path.read_text())

    def test_filename_traversal_rejected(self):
        self.page['properties']['MDFilename']['rich_text'] = [text('../outside.md')]
        with self.assertRaises(ValueError):
            blog.save_markdown_file(self.page, 'Body')

    def test_finalize_after_success(self):
        manifest = self.manifest()
        with patch.object(blog, 'notion_request', return_value=self.page) as request:
            blog.finalize(manifest)
        self.assertEqual(request.call_args.args[0], 'patch')
        self.assertEqual(request.call_args.kwargs['json_data']['properties']['PublishStatus']['select']['name'], 'Published')

    def test_changed_notion_page_not_finalized(self):
        manifest = self.manifest()
        self.page['last_edited_time'] = 'v2'
        with patch.object(blog, 'notion_request', return_value=self.page) as request, self.assertRaises(RuntimeError):
            blog.finalize(manifest)
        self.assertEqual(request.call_count, 1)

    def test_changed_local_content_not_finalized(self):
        manifest = self.manifest()
        (self.root / 'content/chs/know_how/article.md').write_text('changed')
        with patch.object(blog, 'notion_request') as request, self.assertRaises(RuntimeError):
            blog.finalize(manifest)
        request.assert_not_called()

    def test_failed_export_invalidates_manifest_and_exits(self):
        manifest = self.manifest()
        with patch.object(sys, 'argv', ['notion_to_blog.py', '--manifest', str(manifest)]), \
             patch.object(blog, 'require_env'), patch.object(blog, 'get_notion_pages', return_value=[self.page]), \
             patch.object(blog, 'process_notion_page', side_effect=ValueError('unsupported')), self.assertRaises(RuntimeError):
            blog.main()
        self.assertFalse(json.loads(manifest.read_text())['complete'])
        with self.assertRaises(ValueError):
            blog.finalize(manifest)


class RequestTests(unittest.TestCase):
    def test_ambiguous_append_not_retried(self):
        with patch('publishing.http.requests.request', side_effect=requests.Timeout) as request:
            with self.assertRaises(requests.Timeout):
                notion_request('test', 'patch', '/blocks/page/children', json_data={'children': []})
        self.assertEqual(request.call_count, 1)

    def test_read_retries_and_uses_timeout(self):
        response = Mock(text='{}', status_code=200)
        response.json.return_value = {}
        with patch('publishing.http.requests.request', side_effect=[requests.Timeout, response]) as request, patch('publishing.http.time.sleep'):
            self.assertEqual(notion_request('test', 'get', '/pages/page'), {})
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args.kwargs['timeout'], 60)


class PipelineTests(unittest.TestCase):
    def test_backfill_reports_failed_child_process(self):
        with patch.object(backfill.subprocess, 'run', return_value=Mock(returncode=1)), self.assertRaises(RuntimeError):
            backfill.run_obsidian_to_notion([Path('article.md')])

    def test_manifest_rejects_excluded_page(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / 'manifest.json'
            manifest.write_text(json.dumps({'complete': True, 'pages': [{'path': 'content/future.md'}]}))
            with patch('check_site.subprocess.check_output', return_value='path,permalink\n'), self.assertRaisesRegex(ValueError, '未进入发布列表'):
                check_manifest(directory, manifest)

    def test_manifest_requires_actual_built_page(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'complete': True, 'pages': [{'path': 'content/post.md'}]}))
            with patch('check_site.subprocess.check_output', return_value='path,permalink\ncontent/post.md,https://example.com/post/\n'):
                with self.assertRaisesRegex(ValueError, '缺少构建产物'):
                    check_manifest(root, manifest)
                (root / 'post').mkdir()
                (root / 'post/index.html').write_text('post')
                check_manifest(root, manifest)


if __name__ == '__main__':
    unittest.main()
