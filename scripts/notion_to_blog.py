import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
import frontmatter
import requests
import json


from publishing.config import load_local_env, normalize_tags, atomic_write, REPO_ROOT


load_local_env()

# 从环境变量读取配置
CHECKOUT_TOKEN = os.getenv('CHECKOUT_TOKEN')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

# 语言配置
LANGUAGES = {
    'Chinese': 'chs',
    'German': 'de',
    'English': 'en'
}
DEFAULT_LANGUAGE = 'Chinese'

# 每种语言支持的分类
LANGUAGE_CATEGORIES = {
    'chs': {
        'KnowHow': 'know_how',
        'Life': 'life',
        'Page': 'page'
    },
    'de': {
        'Life': 'life',
        'Page': 'page'
    },
    'en': {
        'Life': 'life',
        'Page': 'page'
    }
}

# 默认分类（针对每种语言）
DEFAULT_CATEGORIES = {
    'chs': 'KnowHow',
    'de': 'Life',
    'en': 'Life'
}

GITHUB_REPO = os.getenv('GITHUB_REPO', 'HuizhiXu/pictures')
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH', 'master')


def require_env():
    missing = [name for name in ('NOTION_TOKEN', 'NOTION_DATABASE_ID', 'CHECKOUT_TOKEN') if not os.getenv(name)]
    if missing:
        raise ValueError('请设置环境变量: ' + ', '.join(missing))


def notion_request(method, path, params=None, json_data=None):
    from publishing.http import notion_request as request
    return request(NOTION_TOKEN, method, path, params=params, json_data=json_data)

def get_notion_pages(page_id=None) -> List[Dict[str, Any]]:
    """Fetch pending Garden articles, optionally scoped to exactly one page ID."""
    if page_id:
        page = notion_request('get', f'/pages/{page_id}')
        parent = page.get('parent') or {}
        if parent.get('database_id') != DATABASE_ID and parent.get('data_source_id') != DATABASE_ID:
            raise ValueError('指定页面不属于 Garden 发布数据库，停止发布')
        status = (page.get('properties', {}).get('PublishStatus', {}).get('select') or {}).get('name')
        if status not in {'Publish', 'Update'}:
            raise ValueError(f'指定页面状态必须是 Publish 或 Update，当前为 {status or "未设置"}')
        return [page]

    pages = []
    has_more = True
    next_cursor = None
    
    # 使用 Notion HTTP API 查询数据库，按分页处理
    while has_more:
        body = {
            "filter": {
                "or": [
                    {"property": "PublishStatus", "select": {"equals": "Publish"}},
                    {"property": "PublishStatus", "select": {"equals": "Update"}}
                ]
            }
        }
        if next_cursor:
            body['start_cursor'] = next_cursor

        response = notion_request('post', f'/databases/{DATABASE_ID}/query', json_data=body)
        # response should contain 'results' and pagination fields
        pages.extend(response.get('results', []))
        has_more = response.get('has_more', False)
        next_cursor = response.get('next_cursor')
    
    return pages

def upload_to_github(image_data, image_name, folder_date=None):
    from publishing.images import upload_image
    return upload_image(image_data, image_name, folder_date,
                        token=CHECKOUT_TOKEN, repo=GITHUB_REPO, branch=GITHUB_BRANCH)

def download_image(url: str) -> Tuple[bytes, str]:
    """下载图片
    
    Args:
        url: 图片URL
    Returns:
        图片数据和文件名的元组，如果下载失败则返回(None, None)
    """
    try:
        print(f"[INF] 开始下载图片: {url}")
        # 设置超时，避免长时间等待
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 从URL中获取文件名
        file_name = os.path.basename(url.split('?')[0])  # 移除URL参数
        
        # 如果URL中没有有效的文件名，使用内容类型和时间戳生成
        if not file_name or '.' not in file_name:
            content_type = response.headers.get('content-type', '')
            ext = content_type.split('/')[-1]
            if ext in ['jpeg', 'png', 'gif', 'webp', 'svg+xml']:
                if ext == 'svg+xml':
                    ext = 'svg'
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                file_name = f"image_{timestamp}.{ext}"
            else:
                # 默认使用png格式
                file_name = f"image_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        
        print(f"[INF] 图片下载成功: {file_name} ({len(response.content)} 字节)")
        return response.content, file_name
    
    except requests.exceptions.Timeout:
        print(f"[ERR] 下载图片超时: {url}")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"[ERR] 下载图片失败: {url}, 错误: {e}")
        return None, None
    except Exception as e:
        print(f"[ERR] 下载图片时发生未知错误: {e}")
        return None, None

def convert_notion_blocks_to_markdown(page_id, folder_date=None):
    from publishing.markdown import convert_page

    def image_url(data):
        url = data[data['type']]['url']
        image_data, image_name = download_image(url)
        if image_data is None:
            raise RuntimeError('图片下载失败，停止发布以免保留临时链接')
        return upload_to_github(image_data, image_name, folder_date)

    return convert_page(page_id, notion_request, image_url)

def save_markdown_file(page: Dict[str, Any], content: str, folder_date=None) -> str:
    """
    保存Markdown文件
    
    Args:
        page: Notion页面信息
        content: Markdown内容
    Returns:
        文件名（如果有MDFilename属性）或None
    """
    # 获取页面属性
    properties = page['properties']
    title = ''.join(text['plain_text'] for text in properties['Title']['title'])
    slug = ''.join(text['plain_text'] for text in properties['Slug']['rich_text']) if 'Slug' in properties else title.lower().replace(' ', '-')
    original_date = (properties.get('Date', {}).get('date') or {}).get('start') or datetime.now().isoformat()
    tags = normalize_tags([item['name'] for item in properties['Tags']['multi_select']]) if 'Tags' in properties else []
    
    # 获取语言
    language = DEFAULT_LANGUAGE
    if 'Language' in properties and properties['Language']['select']:
        language = properties['Language']['select']['name']
    
    # 获取语言代码
    lang_code = LANGUAGES.get(language, LANGUAGES[DEFAULT_LANGUAGE])
    
    # 获取分类
    category = DEFAULT_CATEGORIES[lang_code]
    if 'Category' in properties and properties['Category']['select']:
        category = properties['Category']['select']['name']
        
    # 确保分类在该语言中可用
    if category not in LANGUAGE_CATEGORIES[lang_code]:
        print(f'[WARN] 分类 {category} 在语言 {language} 中不可用，使用默认分类 {DEFAULT_CATEGORIES[lang_code]}')
        category = DEFAULT_CATEGORIES[lang_code]
    
    # 确定保存目录
    post_dir = str(REPO_ROOT / 'content' / lang_code / LANGUAGE_CATEGORIES[lang_code][category])
    print(f'[INF] 语言: {language}, 分类: {category}, 保存目录: {post_dir}')
    
    # 检查是否有MDFilename属性
    md_filename = None
    date = original_date  # 默认使用原始日期
    
    if 'MDFilename' in properties and properties['MDFilename']['rich_text']:
        md_filename = ''.join(text['plain_text'] for text in properties['MDFilename']['rich_text'])
        print(f"[INF] 使用MDFilename属性作为文件名: {md_filename}")
        
        # 尝试从MDFilename中提取日期（假设格式为YYYYMMDD开头）
        date_match = re.match(r'^(\d{8})', md_filename)
        if date_match:
            date_str = date_match.group(1)
            try:
                # 将YYYYMMDD格式转换为YYYY-MM-DD格式
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                
                # 从原始日期中提取时间部分（如果有）
                time_part = ""
                if 'T' in original_date:
                    time_part = original_date.split('T')[1]
                
                # 组合新的日期时间
                if time_part:
                    date = f"{year}-{month}-{day}T{time_part}"
                else:
                    date = f"{year}-{month}-{day}"
                    
                print(f"[INF] 从MDFilename中提取到日期: {date}")
            except Exception as e:
                print(f"[WARN] 从MDFilename提取日期失败: {e}，使用原始日期: {original_date}")
                date = original_date
    
    # 从 Article 属性获取文章内容；如果 Article 为空，则使用页面正文内容
    article_content = ''
    if 'Article' in properties and properties['Article'].get('rich_text'):
        for text in properties['Article']['rich_text']:
            if text['type'] == 'mention' and 'page' in text['mention']:
                # 获取被提及页面的内容
                mentioned_page_id = text['mention']['page']['id']
                article_content = convert_notion_blocks_to_markdown(mentioned_page_id, folder_date)
            else:
                article_content += text['plain_text']
    else:
        article_content = content
    
    # 获取Description属性（如果有）
    description = ""
    if 'Description' in properties and properties['Description']['rich_text']:
        description = ''.join(text['plain_text'] for text in properties['Description']['rich_text'])
        print(f"[INF] 从Notion获取到Description: {description}")

    series = ""
    if 'Series' in properties and properties['Series']['rich_text']:
        series = ''.join(text['plain_text'] for text in properties['Series']['rich_text'])
    
    # 使用结构化 frontmatter 生成 YAML，避免标题或摘要里的特殊字符破坏格式。
    metadata = {
        "title": title,
        "date": date,
        "tags": tags,
        "description": description,
        "notion_id": page["id"],
    }
    if series:
        metadata["series"] = series
    post = frontmatter.Post(article_content, **metadata)
    markdown_text = frontmatter.dumps(post)
    
    # 确保目录存在
    os.makedirs(post_dir, exist_ok=True)
    
    # 确定文件名
    if md_filename:
        # 使用MDFilename属性作为文件名
        file_path = os.path.join(post_dir, md_filename)
    else:
        # 使用slug作为文件名
        file_path = os.path.join(post_dir, f"{slug}.md")
    
    file_path = Path(file_path)
    if file_path.parent.resolve() != Path(post_dir).resolve() or file_path.suffix.lower() != '.md':
        raise ValueError('MDFilename 必须是当前栏目的 Markdown 文件名')

    if file_path.exists():
        existing = frontmatter.loads(file_path.read_text(encoding='utf-8'))
        owner = existing.get('notion_id')
        status = (properties.get('PublishStatus', {}).get('select') or {}).get('name')
        if owner and owner != page['id']:
            raise ValueError(f'文件属于另一个 Notion 页面: {file_path}')
        if status != 'Update' and owner != page['id'] and existing.content != post.content:
            raise ValueError(f'文件已存在且内容不同，请确认后使用 Update: {file_path}')
        # Preserve Hugo-only metadata such as math, aliases, and thumbnails.
        existing.metadata.update(metadata)
        existing.content = article_content
        markdown_text = frontmatter.dumps(existing)
    atomic_write(file_path, markdown_text)
    print(f'[INF] 已保存文章: {file_path}')
    return str(file_path.relative_to(REPO_ROOT))


def process_notion_page(page):
    """Export one page; only the deployment finalizer may mark it Published."""
    properties = page['properties']
    if not properties.get('Title', {}).get('title'):
        raise ValueError(f"页面缺少标题: {page['id']}")
    status = (properties.get('PublishStatus', {}).get('select') or {}).get('name')
    if status not in {'Publish', 'Update'}:
        return None
    filename = ''.join(t['plain_text'] for t in properties.get('MDFilename', {}).get('rich_text', []))
    match = re.match(r'^(\d{8})', filename)
    folder_date = match.group(1) if match else None
    content = convert_notion_blocks_to_markdown(page['id'], folder_date)
    path = save_markdown_file(page, content, folder_date)
    return {'id': page['id'], 'last_edited_time': page['last_edited_time'],
            'path': path, 'sha256': hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()}


def _page_mention_id(page, property_name):
    for item in page.get('properties', {}).get(property_name, {}).get('rich_text', []):
        mention = item.get('mention') or {}
        if item.get('type') == 'mention' and mention.get('type') == 'page':
            return mention.get('page', {}).get('id')
    return None


def _notion_title(value):
    return {'title': [{'type': 'text', 'text': {'content': value}}]}


def _sync_creation_publication(source_id, permalink, published_date):
    """Idempotently update the Creation blog row and its Publishing record."""
    creation_database_id = os.getenv('CREATION_DATABASE_ID')
    publishing_database_id = os.getenv('PUBLISHING_DATABASE_ID')
    if not creation_database_id or not publishing_database_id:
        raise ValueError('Creation callback requires CREATION_DATABASE_ID and PUBLISHING_DATABASE_ID')

    source = notion_request('get', f'/pages/{source_id}')
    parent = source.get('parent') or {}
    source_parent = parent.get('database_id') or parent.get('data_source_id')
    if str(source_parent).replace('-', '').lower() != str(creation_database_id).replace('-', '').lower():
        raise ValueError('Garden Article mention points outside the configured Creation database')
    props = source.get('properties', {})
    platform = (props.get('发布平台', {}).get('select') or {}).get('name')
    if platform != '个人博客':
        raise ValueError('Refusing to write blog publication results to a non-blog Creation row')

    notion_request('patch', f'/pages/{source_id}', json_data={'properties': {
        '进度': {'select': {'name': '已发布'}},
        '发布日期': {'date': {'start': published_date}},
        '发布链接': {'url': permalink},
    }})

    # Find an existing Publishing record by the linked Works page, creating one
    # only if none exists. This keeps callbacks safe to retry after partial errors.
    records, cursor = [], None
    while True:
        payload = {'page_size': 100}
        if cursor:
            payload['start_cursor'] = cursor
        response = notion_request('post', f'/databases/{publishing_database_id}/query', json_data=payload)
        records.extend(response.get('results', []))
        if not response.get('has_more'):
            break
        cursor = response.get('next_cursor')
        if not cursor:
            raise RuntimeError('Publishing pagination is incomplete; refusing to create a duplicate')
    linked = []
    for record in records:
        relations = record.get('properties', {}).get('对应稿件', {}).get('relation', [])
        if any(str(item.get('id', '')).replace('-', '').lower() == str(source_id).replace('-', '').lower()
               for item in relations):
            linked.append(record)
    if len(linked) > 1:
        raise ValueError('Multiple Publishing records link to this Creation row; fix duplicates first')

    record_props = {
        '记录': _notion_title(''.join(part.get('plain_text', '') for part in source.get('properties', {}).get('作品', {}).get('title', [])) + '｜博客发布'),
        '对应稿件': {'relation': [{'id': source_id}]},
        '平台': {'select': {'name': '个人博客'}},
        '状态': {'select': {'name': '已发布'}},
        '发布日期': {'date': {'start': published_date}},
        '发布链接': {'url': permalink},
    }
    if linked:
        notion_request('patch', f"/pages/{linked[0]['id']}", json_data={'properties': record_props})
    else:
        notion_request('post', '/pages', json_data={
            'parent': {'database_id': publishing_database_id},
            'properties': record_props,
        })


def finalize(manifest):
    state = json.loads(manifest.read_text(encoding='utf-8'))
    if not state.get('complete'):
        raise ValueError('导出未完成，不能回写发布状态')
    failures = []
    published_date = datetime.now().astimezone().date().isoformat()
    for entry in state['pages']:
        try:
            path = (REPO_ROOT / entry['path']).resolve()
            if not path.is_relative_to((REPO_ROOT / 'content').resolve()):
                raise ValueError('Invalid manifest content path')
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('导出的文件已变化，不能标记发布成功')
            permalink = entry.get('permalink')
            if not permalink:
                raise ValueError('Manifest lacks a verified permalink; rebuild and validate before callback')
            page = notion_request('get', f"/pages/{entry['id']}")
            status = (page['properties'].get('PublishStatus', {}).get('select') or {}).get('name')
            if status != 'Published':
                if page['last_edited_time'] != entry['last_edited_time'] or status not in {'Publish', 'Update'}:
                    raise ValueError('导出后 Notion 页面发生变化，保留当前状态等待下次发布')

            source_id = _page_mention_id(page, 'Article')
            if source_id:
                _sync_creation_publication(source_id, permalink, published_date)

            # Mark Garden Published last, so a failed callback remains retryable.
            if status != 'Published':
                notion_request('patch', f"/pages/{entry['id']}", json_data={
                    'properties': {'PublishStatus': {'select': {'name': 'Published'}}}})
        except Exception as exc:
            failures.append(entry['id'])
            print(f"[ERR] 回写失败 {entry['id']}: {exc}")
    if failures:
        raise RuntimeError(f'{len(failures)} 个页面未完成发布结果回写，请重新运行发布流程')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Export Notion pages; finalize only after deployment succeeds.')
    parser.add_argument('--manifest', type=Path, default=REPO_ROOT / '.sync-state/publish.json')
    parser.add_argument('--page-id', help='Process exactly one Garden page; refuses pages not in Publish/Update state')
    parser.add_argument('--finalize', action='store_true', help='Mark the manifest pages Published after a successful deployment')
    args = parser.parse_args()
    require_env()
    if args.finalize:
        finalize(args.manifest)
        return
    # Invalidate an earlier manifest before doing any work.
    atomic_write(args.manifest, json.dumps({'pages': [], 'complete': False}))
    exported, failures = [], []
    for page in get_notion_pages(args.page_id):
        try:
            entry = process_notion_page(page)
            if entry:
                exported.append(entry)
        except Exception as exc:
            failures.append(page['id'])
            print(f"[ERR] 导出失败 {page['id']}: {exc}")
    if failures:
        raise RuntimeError(f'{len(failures)} 个页面导出失败，停止发布')
    atomic_write(args.manifest, json.dumps({'pages': exported, 'complete': True}, ensure_ascii=False, indent=2))
    print(f'[INF] 已导出 {len(exported)} 篇文章，部署成功后才能回写 Published')


if __name__ == '__main__':
    main()
