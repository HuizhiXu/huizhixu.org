import os
import re
import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
from notion_client import Client
import requests
import json

# 从环境变量读取配置
CHECKOUT_TOKEN = os.getenv('CHECKOUT_TOKEN')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
POST_DIR = os.getenv('POST_DIR', 'content/chs/know_how')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'HuizhiXu/pictures')
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH', 'main')
GITHUB_API_BASE = 'https://api.github.com'

# 检查必要的环境变量
required_env_vars = {
    'CHECKOUT_TOKEN': CHECKOUT_TOKEN,
    'NOTION_TOKEN': NOTION_TOKEN,
    'NOTION_DATABASE_ID': DATABASE_ID
}

for var_name, var_value in required_env_vars.items():
    if not var_value:
        raise ValueError(f'请设置{var_name}环境变量')



# 初始化 Notion 客户端
client = Client(auth=NOTION_TOKEN)

def get_notion_pages() -> List[Dict[str, Any]]:
    """从Notion数据库获取所有文章页面
    
    Returns:
        页面列表
    """
    pages = []
    has_more = True
    next_cursor = None
    
    while has_more:
        response = client.databases.query(
            database_id=DATABASE_ID,
            start_cursor=next_cursor
        )
        pages.extend(response['results'])
        has_more = response['has_more']
        next_cursor = response['next_cursor']
    
    return pages

def upload_to_github(image_data: bytes, image_name: str) -> str:
    """上传图片到GitHub仓库
    
    Args:
        image_data: 图片数据
        image_name: 图片名称
    Returns:
        GitHub图片URL
    """
    # 生成唯一的文件名
    file_hash = hashlib.md5(image_data).hexdigest()[:8]
    file_ext = os.path.splitext(image_name)[1]
    file_name = f"{file_hash}{file_ext}"
    
    # 设置API请求头
    headers = {
        'Authorization': f'Bearer {CHECKOUT_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        # 检查文件是否已存在
        check_url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents/{file_name}"
        response = requests.get(check_url, headers=headers)
        response.raise_for_status()
        
        if response.status_code == 200:
            # 文件已存在，直接返回URL
            return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{file_name}"
        
        # 文件不存在，创建新文件
        content = base64.b64encode(image_data).decode()
        data = {
            'message': f'Upload {image_name}',
            'content': content,
            'branch': GITHUB_BRANCH
        }
        
        # 发送创建文件请求
        create_url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents/{file_name}"
        response = requests.put(create_url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        
        # 检查响应内容
        response_data = response.json()
        if 'content' not in response_data:
            raise ValueError(f'GitHub API响应异常: {response_data}')
            
        return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{file_name}"
    except requests.exceptions.RequestException as e:
        print(f'上传图片到GitHub失败: {e}')
        if hasattr(e.response, 'json'):
            print(f'错误详情: {e.response.json()}')
        return None
    except Exception as e:
        print(f'上传图片时发生错误: {e}')
        return None

def download_image(url: str) -> Tuple[bytes, str]:
    """下载图片
    
    Args:
        url: 图片URL
    Returns:
        图片数据和文件名
    """
    response = requests.get(url)
    response.raise_for_status()
    
    # 从URL中获取文件名
    file_name = os.path.basename(url)
    if not file_name:
        # 如果URL中没有文件名，使用内容类型生成
        content_type = response.headers.get('content-type', '')
        ext = content_type.split('/')[-1]
        file_name = f"image.{ext}"
    
    return response.content, file_name

def convert_notion_blocks_to_markdown(page_id: str) -> str:
    """将Notion页面内容转换为Markdown格式
    
    Args:
        page_id: Notion页面ID
    Returns:
        Markdown格式的内容
    """
    blocks = []
    has_more = True
    next_cursor = None
    
    # 获取所有blocks
    while has_more:
        response = client.blocks.children.list(
            block_id=page_id,
            start_cursor=next_cursor
        )
        blocks.extend(response['results'])
        has_more = response['has_more']
        next_cursor = response['next_cursor']
    
    # 转换为Markdown
    markdown_content = []
    for block in blocks:
        block_type = block['type']
        if block_type == 'paragraph':
            text = ''.join(text['plain_text'] for text in block['paragraph']['rich_text'])
            markdown_content.append(text + '\n\n')
        elif block_type.startswith('heading_'):
            level = int(block_type[-1])
            text = ''.join(text['plain_text'] for text in block[block_type]['rich_text'])
            markdown_content.append('#' * level + ' ' + text + '\n\n')
        elif block_type == 'code':
            language = block['code'].get('language', '')
            text = ''.join(text['plain_text'] for text in block['code']['rich_text'])
            markdown_content.append(f'```{language}\n{text}\n```\n\n')
        elif block_type == 'bulleted_list_item':
            text = ''.join(text['plain_text'] for text in block['bulleted_list_item']['rich_text'])
            markdown_content.append(f'- {text}\n')
        elif block_type == 'numbered_list_item':
            text = ''.join(text['plain_text'] for text in block['numbered_list_item']['rich_text'])
            markdown_content.append(f'1. {text}\n')
        elif block_type == 'image':
            # 处理图片
            image_block = block['image']
            if image_block['type'] == 'external':
                image_url = image_block['external']['url']
            else:  # file
                image_url = image_block['file']['url']
            
            try:
                # 下载图片
                image_data, image_name = download_image(image_url)
                # 上传到GitHub
                github_url = upload_to_github(image_data, image_name)
                # 添加Markdown图片语法
                caption = ''.join(text['plain_text'] for text in image_block.get('caption', []))
                markdown_content.append(f'![{caption}]({github_url})\n\n')
            except Exception as e:
                print(f'[ERR] 处理图片失败: {str(e)}')
                # 如果处理失败，使用原始URL
                markdown_content.append(f'![image]({image_url})\n\n')
    
    return ''.join(markdown_content)

def save_markdown_file(page: Dict[str, Any], content: str) -> None:
    """保存Markdown文件
    
    Args:
        page: Notion页面信息
        content: Markdown内容
    """
    # 获取页面属性
    properties = page['properties']
    title = ''.join(text['plain_text'] for text in properties['Title']['title'])
    slug = ''.join(text['plain_text'] for text in properties['Slug']['rich_text']) if 'Slug' in properties else title.lower().replace(' ', '-')
    date = properties['Date']['date']['start'] if 'Date' in properties else datetime.now().isoformat()
    tags = [item['name'] for item in properties['Tags']['multi_select']] if 'Tags' in properties else []
    
    # 从 Article 属性获取文章内容
    article_content = ''
    if 'Article' in properties:
        for text in properties['Article']['rich_text']:
            if text['type'] == 'mention' and 'page' in text['mention']:
                # 获取被提及页面的内容
                mentioned_page_id = text['mention']['page']['id']
                article_content = convert_notion_blocks_to_markdown(mentioned_page_id)
            else:
                article_content += text['plain_text']
    else:
        article_content = content
    
    # 创建frontmatter
    frontmatter = f"---\ntitle: \"{title}\"\ndate: {date}\ntags: {tags}\n---\n\n{article_content}"
    
    # 确保目录存在
    os.makedirs(POST_DIR, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(POST_DIR, f"{slug}.md")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f'[INF] 已保存文章: {file_path}')

def calc_md5(content: bytes):
    md5_hash = hashlib.md5()
    md5_hash.update(content)
    return md5_hash.hexdigest()

def get_ext(resp: requests.Response):
    ext = Path(urllib.parse.urlparse(resp.url).path).suffix
    if ext and re.match(r'^\.\w+$', ext):
        return ext
    for i in ['content-type', 'Content-Type']:
        if i not in resp.headers:
            continue
        content_type = resp.headers[i]
        ext = f'.{content_type.split("/")[1]}'
        return ext
    raise ValueError(f'未知的后缀: {resp.url}')


def convert_markdown_to_blocks(content: str) -> List[dict]:
    """将Markdown内容转换为Notion blocks
    
    Args:
        content: Markdown内容
    Returns:
        Notion blocks列表
    """
    # 将内容按行分割
    lines = content.split('\n')
    blocks = []
    current_block = None
    
    for line in lines:
        # 跳过空行
        if not line.strip():
            if current_block:
                blocks.append(current_block)
                current_block = None
            continue
            
        # 处理标题
        if line.startswith('#'):
            level = len(re.match(r'^#+', line).group())
            text = line.lstrip('#').strip()
            if level <= 3:  # Notion只支持h1-h3
                blocks.append({
                    "object": "block",
                    "type": f"heading_{level}",
                    f"heading_{level}": {
                        "rich_text": [{"type": "text", "text": {"content": text}}]
                    }
                })
            continue
            
        # 处理普通段落
        if not current_block:
            current_block = {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                }
            }
        else:
            current_text = current_block["paragraph"]["rich_text"][0]["text"]["content"]
            current_block["paragraph"]["rich_text"][0]["text"]["content"] = f"{current_text}\n{line}"
    
    if current_block:
        blocks.append(current_block)
    
    return blocks

def create_notion_page(page_info: Dict[str, Any]) -> dict:
    """创建 Notion 页面
    
    Args:
        page_info: 页面信息字典，包含标题、日期、标签等
    Returns:
        创建的页面信息
    """
    # 构建页面属性
    properties = {
        "Title": {"title": [{"text": {"content": page_info['title']}}]},
        "Slug": {"rich_text": [{"text": {"content": page_info.get('slug', '')}}]},
        "Date": {"date": {"start": page_info.get('date', datetime.now().isoformat())}},
        "Summary": {"rich_text": [{"text": {"content": page_info.get('summary', '')[:2000]}}]},
        "Tags": {"multi_select": [{"name": tag} for tag in page_info.get('tags', [])]},
        "Status": {"select": {"name": "Draft"}},
        "Type": {"select": {"name": "Post"}},
        "Category": {"select": {"name": "技术分享"}}
    }

    # 将Markdown内容转换为Notion blocks
    children = convert_markdown_to_blocks(markdown_info.content)

    # 创建页面
    try:
        return client.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties,
            children=children
        )
    except Exception as e:
        print(f'[ERR] 创建页面失败: {str(e)}')
        raise

def process_notion_page(page: Dict[str, Any]) -> None:
    """处理单个Notion页面
    
    Args:
        page: Notion页面信息
    """
    try:
        # 获取页面ID
        page_id = page['id']
        
        # 检查页面属性
        if 'properties' not in page:
            print(f'[ERR] 页面缺少properties字段: {page_id}')
            return
            
        properties = page['properties']
        if 'Title' not in properties or not properties['Title']['title']:
            print(f'[ERR] 页面缺少标题: {page_id}')
            return
        
        # 获取并转换内容
        content = convert_notion_blocks_to_markdown(page_id)
        
        # 保存为Markdown文件
        save_markdown_file(page, content)
        
    except KeyError as e:
        print(f'[ERR] 处理页面失败: 缺少必要字段 {str(e)}')
    except Exception as e:
        print(f'[ERR] 处理页面失败: {str(e)}')
        import traceback
        print(traceback.format_exc())

def main():
    """主函数"""
    try:
        # 获取所有页面
        print('[INF] 正在从Notion获取页面...')
        pages = get_notion_pages()
        print(f'[INF] 获取到 {len(pages)} 个页面')
        
        # 处理每个页面
        for page in pages:
            process_notion_page(page)
        
        print('[INF] 处理完成')
        
    except Exception as e:
        print(f'[ERR] 程序执行失败: {str(e)}')

if __name__ == "__main__":
    main()
