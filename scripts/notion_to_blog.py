import os
import re
import base64
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from notion_client import Client
import requests
import json

# 从环境变量读取配置
CHECKOUT_TOKEN = os.getenv('CHECKOUT_TOKEN')
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
POST_DIR = os.getenv('POST_DIR', 'content/chs/know_how')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'HuizhiXu/pictures')
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH', 'master')
GITHUB_API_BASE = 'https://api.github.com'

# 全局变量，用于存储当前处理的文章的日期（从MDFilename中提取）
CURRENT_IMAGE_FOLDER_DATE = None

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
        GitHub图片URL或None（如果上传失败）
    """
    # 生成唯一的文件名
    file_hash = hashlib.md5(image_data).hexdigest()[:8]
    file_ext = os.path.splitext(image_name)[1]
    file_name = f"{file_hash}{file_ext}"
    
    # 确定文件路径（是否包含日期文件夹）
    file_path = file_name
    raw_url_path = file_name
    
    # 如果有日期信息，则创建日期文件夹
    if CURRENT_IMAGE_FOLDER_DATE:
        file_path = f"{CURRENT_IMAGE_FOLDER_DATE}/{file_name}"
        raw_url_path = f"{CURRENT_IMAGE_FOLDER_DATE}/{file_name}"
        print(f"[INF] 使用日期文件夹 {CURRENT_IMAGE_FOLDER_DATE} 存储图片")
    
    print(f"[INF] 准备上传图片 {file_path} 到 GitHub 仓库 {GITHUB_REPO}")
    
    # 设置API请求头
    headers = {
        'Authorization': f'Bearer {CHECKOUT_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # 最大重试次数
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 检查文件是否已存在
            check_url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents/{file_path}"
            print(f"[INF] 检查文件是否存在: {check_url}")
            response = requests.get(check_url, headers=headers)
            
            # 如果文件存在，直接返回URL
            if response.status_code == 200:
                print(f"[INF] 文件 {file_path} 已存在于GitHub仓库中")
                return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{raw_url_path}"
            
            # 如果是404错误，说明文件不存在，继续创建
            if response.status_code != 404:
                response.raise_for_status()
            
            # 文件不存在，创建新文件
            print(f"[INF] 文件 {file_path} 不存在，准备创建")
            content = base64.b64encode(image_data).decode()
            data = {
                'message': f'Upload {image_name}',
                'content': content,
                'branch': GITHUB_BRANCH
            }
            
            # 发送创建文件请求
            create_url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents/{file_path}"
            print(f"[INF] 发送创建文件请求: {create_url}")
            response = requests.put(create_url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            
            # 检查响应内容
            response_data = response.json()
            if 'content' not in response_data:
                print(f"[WARN] GitHub API响应异常: {response_data}")
                raise ValueError(f'GitHub API响应异常: {response_data}')
            
            print(f"[INF] 文件 {file_path} 成功上传到GitHub")
            return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{raw_url_path}"
            
        except requests.exceptions.RequestException as e:
            retry_count += 1
            error_msg = f'上传图片到GitHub失败 (尝试 {retry_count}/{max_retries}): {e}'
            print(f"[ERR] {error_msg}")
            
            # 提取详细错误信息
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    print(f"[ERR] 错误详情: {error_details}")
                    
                    # 检查是否是认证问题
                    if e.response.status_code == 401:
                        print(f"[ERR] 认证失败! 请检查CHECKOUT_TOKEN是否有效且具有足够权限")
                    # 检查是否是仓库不存在
                    elif e.response.status_code == 404:
                        print(f"[ERR] 仓库或路径不存在! 请检查GITHUB_REPO={GITHUB_REPO}和GITHUB_BRANCH={GITHUB_BRANCH}是否正确")
                except:
                    print(f"[ERR] 无法解析错误响应: {e.response.text if hasattr(e.response, 'text') else 'No response text'}")
            
            # 如果还有重试机会，等待后重试
            if retry_count < max_retries:
                wait_time = 2 ** retry_count  # 指数退避
                print(f"[INF] 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"[ERR] 已达到最大重试次数 ({max_retries})，上传失败")
                return None
                
        except Exception as e:
            print(f"[ERR] 上传图片时发生未知错误: {e}")
            return None
    
    return None

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
            image_type = image_block['type']
            print(f"[INF] 处理图片块，类型: {image_type}")
            
            if image_type == 'external':
                image_url = image_block['external']['url']
                print(f"[INF] 处理外部图片: {image_url}")
            else:  # file
                image_url = image_block['file']['url']
                print(f"[INF] 处理Notion托管图片: {image_url}")
            
            try:
                # 下载图片
                print(f"[INF] 开始下载并处理图片...")
                image_data, image_name = download_image(image_url)
                
                # 检查下载是否成功
                if image_data is None or image_name is None:
                    print(f"[WARN] 图片下载失败，将使用原始URL")
                    caption = ''.join(text['plain_text'] for text in image_block.get('caption', []))
                    markdown_content.append(f'![{caption}]({image_url})\n\n')
                    continue
                
                # 上传到GitHub
                print(f"[INF] 图片下载成功，准备上传到GitHub")
                github_url = upload_to_github(image_data, image_name)
                
                # 检查上传是否成功
                if github_url is None:
                    print(f"[WARN] 图片上传到GitHub失败，将使用原始URL")
                    caption = ''.join(text['plain_text'] for text in image_block.get('caption', []))
                    markdown_content.append(f'![{caption}]({image_url})\n\n')
                else:
                    # 添加Markdown图片语法
                    caption = ''.join(text['plain_text'] for text in image_block.get('caption', []))
                    print(f"[INF] 图片处理成功，使用GitHub URL: {github_url}")
                    markdown_content.append(f'![{caption}]({github_url})\n\n')
            except Exception as e:
                print(f'[ERR] 处理图片时发生未捕获的异常: {str(e)}')
                # 如果处理失败，使用原始URL
                caption = ''.join(text['plain_text'] for text in image_block.get('caption', []))
                markdown_content.append(f'![image]({image_url})\n\n')
    
    return ''.join(markdown_content)

def save_markdown_file(page: Dict[str, Any], content: str) -> None:
    """保存Markdown文件
    
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
    original_date = properties['Date']['date']['start'] if 'Date' in properties else datetime.now().isoformat()
    tags = [item['name'] for item in properties['Tags']['multi_select']] if 'Tags' in properties else []
    
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
    
    # 获取Description属性（如果有）
    description = ""
    if 'Description' in properties and properties['Description']['rich_text']:
        description = ''.join(text['plain_text'] for text in properties['Description']['rich_text'])
        print(f"[INF] 从Notion获取到Description: {description}")
    
    # 创建frontmatter
    frontmatter = f"---\ntitle: \"{title}\"\ndate: {date}\ntags: {tags}\ndescription: \"{description}\"\n---\n\n{article_content}"
    
    # 确保目录存在
    os.makedirs(POST_DIR, exist_ok=True)
    
    # 确定文件名
    if md_filename:
        # 使用MDFilename属性作为文件名
        file_path = os.path.join(POST_DIR, md_filename)
    else:
        # 使用slug作为文件名
        file_path = os.path.join(POST_DIR, f"{slug}.md")
    
    # 保存文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f'[INF] 已保存文章: {file_path}')
    
    # 返回使用的文件名，用于后续处理
    return md_filename

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
        
        # 检查发布状态
        publish_status = None
        if 'PublishStatus' in properties:
            if 'select' in properties['PublishStatus'] and properties['PublishStatus']['select']:
                publish_status = properties['PublishStatus']['select']['name']
                print(f'[INF] 页面发布状态: {publish_status}')
            else:
                print(f'[WARN] PublishStatus 属性存在但不是 select 类型或为空: {page_id}')
                # 如果没有设置 PublishStatus，默认处理所有页面
                # 可以根据需要修改此行为
                publish_status = 'Publish'  # 默认值
                print(f'[INF] 使用默认发布状态: {publish_status}')
        else:
            print(f'[WARN] 页面没有设置 PublishStatus 属性，使用默认值: {page_id}')
            # 如果没有 PublishStatus 属性，默认处理所有页面
            publish_status = 'Publish'  # 默认值
            print(f'[INF] 使用默认发布状态: {publish_status}')
        
        # 根据发布状态决定是否处理页面
        if publish_status not in ['Publish', 'Update']:
            print(f'[INF] 页面不需要发布或更新，跳过: {page_id}')
            return
        
        # 检查是否有MDFilename属性，并提取日期
        md_filename = None
        image_folder_date = None
        if 'MDFilename' in properties and properties['MDFilename']['rich_text']:
            md_filename = ''.join(text['plain_text'] for text in properties['MDFilename']['rich_text'])
            # 尝试从MDFilename中提取日期（假设格式为YYYYMMDD开头）
            date_match = re.match(r'^(\d{8})', md_filename)
            if date_match:
                image_folder_date = date_match.group(1)
                print(f"[INF] 从MDFilename中提取到日期: {image_folder_date}")
        
        # 设置全局变量，供图片上传函数使用
        global CURRENT_IMAGE_FOLDER_DATE
        CURRENT_IMAGE_FOLDER_DATE = image_folder_date
        
        # 获取并转换内容
        content = convert_notion_blocks_to_markdown(page_id)
        
        # 保存为Markdown文件
        save_markdown_file(page, content)
        
        # 更新页面状态为Published
        try:
            # 只有当原始状态是 Publish 或 Update 时才更新状态
            if publish_status in ['Publish', 'Update']:
                # 检查 PublishStatus 属性是否存在且是 select 类型
                if 'PublishStatus' in properties and ('select' in properties['PublishStatus'] or properties['PublishStatus'].get('type') == 'select'):
                    client.pages.update(
                        page_id=page_id,
                        properties={
                            'PublishStatus': {
                                'select': {
                                    'name': 'Published'
                                }
                            }
                        }
                    )
                    print(f'[INF] 已更新页面状态为Published: {page_id}')
                else:
                    print(f'[WARN] 无法更新页面状态：PublishStatus 属性不存在或不是 select 类型: {page_id}')
            else:
                print(f'[INF] 页面状态不是 Publish 或 Update，不更新状态: {page_id}')
        except Exception as e:
            print(f'[WARN] 更新页面状态失败: {str(e)}')
            import traceback
            print(traceback.format_exc())
        
        # 重置全局变量
        CURRENT_IMAGE_FOLDER_DATE = None
        
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
