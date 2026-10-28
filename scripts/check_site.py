"""Validate generated multilingual search URLs and fingerprinted local assets."""
import json
import argparse
import csv
import io
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse, urljoin


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.index = None
        self.styles = []
        self.feature_images = []
        self.masthead = False
        self.feature_articles = 0
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id') == 'site-search':
            self.index = attrs['data-index-url']
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.styles.append(attrs['href'])
        classes = attrs.get('class', '').split()
        if 'journal-masthead' in classes:
            self.masthead = True
        if tag == 'article' and 'journal-feature' in classes:
            self.feature_articles += 1
        if tag == 'img' and 'journal-feature-image' in classes:
            self.feature_images.append(attrs)
        if tag == 'script' and 'search-bundle' in attrs.get('src', ''):
            self.scripts.append(attrs['src'])


def check_manifest(root, manifest):
    state = json.loads(Path(manifest).read_text())
    if not state.get('complete'):
        raise ValueError('Export did not complete')
    output = subprocess.check_output(['hugo', 'list', 'published'], text=True)
    pages = {row['path']: row['permalink'] for row in csv.DictReader(io.StringIO(output))}
    for entry in state['pages']:
        if entry['path'] not in pages:
            raise ValueError(f"导出文章未进入发布列表，请检查 draft、未来日期和 expiryDate: {entry['path']}")
        path = Path(root) / unquote(urlparse(pages[entry['path']]).path.lstrip('/'))
        if not ((path / 'index.html').is_file() or path.is_file()):
            raise ValueError(f"导出文章缺少构建产物: {path}")
        entry["permalink"] = pages[entry["path"]]
    # Persist the verified permalink so post-deploy callbacks can write the
    # exact public URL back to Notion rather than reconstructing it from a slug.
    Path(manifest).write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check(root):
    root = Path(root)
    for language in ('', 'en', 'de'):
        page = Page()
        page.feed((root / language / 'index.html').read_text())
        assert page.index, f'Missing search URL: {language}'
        base_url = f'/{language}/' if language else '/'
        def local(url):
            return root / unquote(urlparse(urljoin(base_url, url)).path.lstrip('/'))
        index = local(page.index)
        data = json.loads(index.read_text())
        assert isinstance(data, list), index
        for item in data:
            assert all(key in item for key in ('title', 'contents', 'summary', 'permalink')), item
            path = root / unquote(urlparse(item['permalink']).path.lstrip('/'))
            assert (path / 'index.html').exists() or path.is_file(), path
        assert any('/custom.' in url for url in page.styles), 'Custom CSS needs a fingerprint'
        assert page.scripts, 'Missing search bundle'
        assert page.masthead, f'Missing journal masthead: {language}'
        assert page.feature_articles == 1, f'Expected one lead article: {language}'
        for attrs in page.feature_images:
            assert 'width' in attrs and 'height' in attrs, 'Feature image needs dimensions'
            assert attrs.get('alt'), 'Feature image needs alt text'
            image = local(attrs['src'])
            assert image.exists() and image.stat().st_size < 200_000, image
        print(f'{language or "chs"}: search {len(data)} pages, {len(page.feature_images)} optimized feature images; OK')
    for path in root.rglob('*.html'):
        page = Page()
        page.feed(path.read_text())
        if page.index:
            assert page.masthead, f'Missing journal masthead: {path}'
            url = urljoin('/' + str(path.relative_to(root)), page.index)
            target = root / unquote(urlparse(url).path.lstrip('/'))
            assert target.is_file(), (path, page.index)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', nargs='?', default='public')
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    check(args.root)
    if args.manifest:
        check_manifest(args.root, args.manifest)
