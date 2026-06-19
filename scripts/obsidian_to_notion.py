import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import time
import urllib.parse
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import frontmatter
import requests


def load_local_env(env_path: Path = Path(".env")) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_local_env()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
CHECKOUT_TOKEN = os.getenv("CHECKOUT_TOKEN")

OBSIDIAN_SOURCE_DIR = Path(
    os.getenv(
        "OBSIDIAN_SOURCE_DIR",
        "/Users/Sophia/Library/CloudStorage/SynologyDrive-20260618/04_存档与收件箱/01Archive/Published/Book_G",
    )
).expanduser()

GITHUB_REPO = os.getenv("GITHUB_REPO", "HuizhiXu/pictures")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "master")
GITHUB_API_BASE = "https://api.github.com"
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

DEFAULT_LANGUAGE = os.getenv("DEFAULT_NOTION_LANGUAGE", "Chinese")
DEFAULT_CATEGORY = os.getenv("DEFAULT_NOTION_CATEGORY", "KnowHow")
DEFAULT_PUBLISH_STATUS = os.getenv("DEFAULT_PUBLISH_STATUS", "Draft")
PLACEHOLDER_TITLES = {"文章标题", "untitled", "title", "new note"}
TAG_ALIASES = {
    "comfy-ui": "comfyui",
    "paper": "paper-review",
    "paperreview": "paper-review",
}

OBSIDIAN_VAULT_ROOT = Path(
    os.getenv(
        "OBSIDIAN_VAULT_ROOT",
        str(OBSIDIAN_SOURCE_DIR.parent.parent.parent.parent),
    )
).expanduser()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Obsidian Markdown files to Notion.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional Markdown files to sync. Without paths, syncs all files in OBSIDIAN_SOURCE_DIR.",
    )
    return parser.parse_args()


def require_env() -> None:
    required = {
        "NOTION_TOKEN": NOTION_TOKEN,
        "NOTION_DATABASE_ID": DATABASE_ID,
        "CHECKOUT_TOKEN": CHECKOUT_TOKEN,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError(f"请设置环境变量: {', '.join(missing)}")


def notion_request(
    method: str,
    path: str,
    params: Optional[dict] = None,
    json_data: Optional[dict] = None,
) -> dict:
    url = NOTION_API_BASE + path
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=60,
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as exc:
            retryable = isinstance(
                exc,
                (
                    requests.exceptions.SSLError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                ),
            )
            print(f"[ERR] Notion request failed {method} {url} ({attempt}/{max_retries}): {exc}")
            if hasattr(exc, "response") and exc.response is not None:
                print(f"[ERR] Response: {exc.response.status_code} {exc.response.text}")
            if not retryable or attempt == max_retries:
                raise
            wait_time = 2 ** attempt
            print(f"[INF] 等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    return {}


def get_database_schema() -> Dict[str, str]:
    database = notion_request("get", f"/databases/{DATABASE_ID}")
    return {
        name: details["type"]
        for name, details in database.get("properties", {}).items()
    }


def split_text(content: str, limit: int = 2000) -> List[dict]:
    if not content:
        return []
    return [
        {"type": "text", "text": {"content": content[index : index + limit]}}
        for index in range(0, len(content), limit)
    ]


def first_value(values: Iterable[Any], default: str = "") -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def normalize_tags(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        raw_tags = value
    else:
        raw_tags = str(value).split(",")

    tags = []
    for item in raw_tags:
        tag = str(item).strip().lower().replace("_", "-").replace(" ", "-")
        if tag:
            tags.append(TAG_ALIASES.get(tag, tag))
    return tags


def derive_title(md_path: Path, metadata: dict) -> str:
    title = first_value([metadata.get("title"), metadata.get("Title"), md_path.stem], md_path.stem)
    if title.strip().lower() in PLACEHOLDER_TITLES:
        stem = re.sub(r"^\d{4}-\d{2}-\d{2}\s*", "", md_path.stem).strip()
        return stem or md_path.stem
    return title


def normalize_date(value: Any) -> str:
    if not value:
        return datetime.now().date().isoformat()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def slugify(value: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value.lower()).strip("-")
    return slug or "untitled"


def image_folder_date(metadata: dict, md_path: Path) -> Optional[str]:
    md_filename = first_value([metadata.get("md_filename"), metadata.get("MDFilename"), md_path.name])
    filename_match = re.match(r"^(\d{8})", md_filename)
    if filename_match:
        return filename_match.group(1)

    raw_date = normalize_date(metadata.get("date"))
    date_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", raw_date)
    if date_match:
        return "".join(date_match.groups())
    return None


def github_headers() -> dict:
    return {
        "Authorization": f"Bearer {CHECKOUT_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def upload_to_github(image_data: bytes, image_name: str, folder_date: Optional[str]) -> str:
    file_hash = hashlib.md5(image_data).hexdigest()[:8]
    ext = Path(image_name).suffix
    if not ext:
        ext = mimetypes.guess_extension("image/png") or ".png"

    file_name = f"{file_hash}{ext}"
    file_path = f"{folder_date}/{file_name}" if folder_date else file_name
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{file_path}"

    headers = github_headers()
    check_url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents/{file_path}"
    for attempt in range(1, 4):
        try:
            check_response = requests.get(check_url, headers=headers, timeout=30)
            if check_response.status_code == 200:
                print(f"[INF] 图片已存在: {file_path}")
                return raw_url
            if check_response.status_code != 404:
                check_response.raise_for_status()

            data = {
                "message": f"Upload {image_name}",
                "content": base64.b64encode(image_data).decode(),
                "branch": GITHUB_BRANCH,
            }
            create_response = requests.put(
                check_url,
                headers=headers,
                data=json.dumps(data),
                timeout=30,
            )
            create_response.raise_for_status()
            print(f"[INF] 图片已上传: {file_path}")
            return raw_url
        except requests.exceptions.RequestException as exc:
            print(f"[ERR] 上传图片失败 ({attempt}/3): {image_name}: {exc}")
            if attempt == 3:
                raise
            time.sleep(2**attempt)

    raise RuntimeError(f"上传图片失败: {image_name}")


def is_remote_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def resolve_image_path(raw_path: str, md_path: Path) -> Optional[Path]:
    decoded_path = urllib.parse.unquote(raw_path.strip())
    decoded_path = decoded_path.split("#", 1)[0]

    direct_path = Path(decoded_path).expanduser()
    candidates = []
    if direct_path.is_absolute():
        candidates.append(direct_path)
    else:
        candidates.append(md_path.parent / direct_path)
        candidates.append(OBSIDIAN_SOURCE_DIR / direct_path)

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    basename = Path(decoded_path).name
    if basename:
        search_roots = [OBSIDIAN_SOURCE_DIR, OBSIDIAN_VAULT_ROOT, md_path.parent]
        seen = set()
        for root in search_roots:
            if not root.exists():
                continue
            for candidate in root.rglob(basename):
                if candidate.is_file() and candidate not in seen:
                    seen.add(candidate)
                    return candidate
    return None


def upload_local_image(raw_path: str, md_path: Path, folder_date: Optional[str]) -> Optional[str]:
    if is_remote_url(raw_path):
        return raw_path

    image_path = resolve_image_path(raw_path, md_path)
    if not image_path:
        print(f"[WARN] 找不到本地图片，保留原始路径: {raw_path}")
        return None

    return upload_to_github(image_path.read_bytes(), image_path.name, folder_date)


def replace_obsidian_embeds(content: str, md_path: Path, folder_date: Optional[str]) -> str:
    pattern = re.compile(r"!\[\[([^\]]+)\]\]")

    def replace(match: re.Match) -> str:
        target = match.group(1)
        image_ref, _, alt = target.partition("|")
        url = upload_local_image(image_ref, md_path, folder_date)
        if not url:
            return match.group(0)
        caption = alt.strip() or Path(image_ref).stem
        return f"![{caption}]({url})"

    return pattern.sub(replace, content)


def replace_markdown_images(content: str, md_path: Path, folder_date: Optional[str]) -> str:
    pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

    def replace(match: re.Match) -> str:
        alt = match.group(1)
        raw_target = match.group(2).strip()
        if is_remote_url(raw_target):
            return match.group(0)

        url = upload_local_image(raw_target, md_path, folder_date)
        if not url:
            return match.group(0)
        return f"![{alt}]({url})"

    return pattern.sub(replace, content)


def prepare_markdown_content(content: str, md_path: Path, metadata: dict) -> str:
    folder_date = image_folder_date(metadata, md_path)
    content = replace_obsidian_embeds(content, md_path, folder_date)
    return replace_markdown_images(content, md_path, folder_date)


def image_block(url: str, caption: str = "") -> dict:
    return {
        "object": "block",
        "type": "image",
        "image": {
            "type": "external",
            "external": {"url": url},
            "caption": split_text(caption),
        },
    }


def paragraph_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": split_text(text)},
    }


def markdown_to_blocks(content: str) -> List[dict]:
    blocks: List[dict] = []
    paragraph_lines: List[str] = []
    code_lines: List[str] = []
    in_code = False
    code_language = "plain text"

    def flush_paragraph() -> None:
        if paragraph_lines:
            blocks.append(paragraph_block("\n".join(paragraph_lines).strip()))
            paragraph_lines.clear()

    for line in content.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                blocks.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": code_language,
                            "rich_text": split_text("\n".join(code_lines)),
                        },
                    }
                )
                code_lines.clear()
                in_code = False
                code_language = "plain text"
            else:
                flush_paragraph()
                in_code = True
                code_language = stripped.strip("`").strip() or "plain text"
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            continue

        image_match = re.fullmatch(r"!\[([^\]]*)\]\((https?://[^)]+)\)", stripped)
        if image_match:
            flush_paragraph()
            blocks.append(image_block(image_match.group(2), image_match.group(1)))
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            flush_paragraph()
            level = min(len(heading_match.group(1)), 3)
            blocks.append(
                {
                    "object": "block",
                    "type": f"heading_{level}",
                    f"heading_{level}": {"rich_text": split_text(heading_match.group(2))},
                }
            )
            continue

        bullet_match = re.match(r"^[-*]\s+(.+)$", stripped)
        if bullet_match:
            flush_paragraph()
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": split_text(bullet_match.group(1))},
                }
            )
            continue

        numbered_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if numbered_match:
            flush_paragraph()
            blocks.append(
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": split_text(numbered_match.group(1))},
                }
            )
            continue

        paragraph_lines.append(line)

    if in_code:
        blocks.append(
            {
                "object": "block",
                "type": "code",
                "code": {
                    "language": code_language,
                    "rich_text": split_text("\n".join(code_lines)),
                },
            }
        )
    flush_paragraph()
    return blocks


def build_page_info(md_path: Path, post: frontmatter.Post) -> Dict[str, Any]:
    metadata = dict(post.metadata)
    title = derive_title(md_path, metadata)
    category = first_value(
        [metadata.get("category"), metadata.get("Category")],
        DEFAULT_CATEGORY,
    )
    md_filename = first_value([metadata.get("md_filename"), metadata.get("MDFilename")], md_path.name)

    return {
        "title": title,
        "slug": first_value([metadata.get("slug"), metadata.get("Slug")], slugify(md_path.stem)),
        "date": normalize_date(metadata.get("date")),
        "tags": normalize_tags(metadata.get("tags")),
        "description": first_value([metadata.get("description"), metadata.get("summary")]),
        "series": first_value([metadata.get("series"), metadata.get("Series")]),
        "category": category,
        "language": first_value([metadata.get("language"), metadata.get("Language")], DEFAULT_LANGUAGE),
        "publish_status": first_value(
            [metadata.get("publish_status"), metadata.get("PublishStatus")],
            DEFAULT_PUBLISH_STATUS,
        ),
        "status": first_value([metadata.get("status"), metadata.get("Status")], "Draft"),
        "type": first_value([metadata.get("type"), metadata.get("Type")], "Post"),
        "md_filename": md_filename,
        "notion_id": first_value([metadata.get("notion_id"), metadata.get("notion_page_id")]),
        "source_file": str(md_path),
    }


def rich_text_property(value: str) -> dict:
    return {"rich_text": split_text(value)}


def select_property(value: str) -> dict:
    return {"select": {"name": value}} if value else {"select": None}


def build_properties(page_info: Dict[str, Any], schema: Dict[str, str]) -> dict:
    candidates = {
        "Title": ("title", {"title": split_text(page_info["title"])}),
        "Slug": ("rich_text", rich_text_property(page_info["slug"])),
        "Date": ("date", {"date": {"start": page_info["date"]}}),
        "Tags": (
            "multi_select",
            {"multi_select": [{"name": tag} for tag in page_info["tags"]]},
        ),
        "Description": ("rich_text", rich_text_property(page_info["description"])),
        "Summary": ("rich_text", rich_text_property(page_info["description"])),
        "Series": ("rich_text", rich_text_property(page_info["series"])),
        "Language": ("select", select_property(page_info["language"])),
        "Category": ("select", select_property(page_info["category"])),
        "PublishStatus": ("select", select_property(page_info["publish_status"])),
        "Status": ("select", select_property(page_info["status"])),
        "Type": ("select", select_property(page_info["type"])),
        "MDFilename": ("rich_text", rich_text_property(page_info["md_filename"])),
        "Source File": ("rich_text", rich_text_property(page_info["source_file"])),
    }

    properties = {}
    for name, (expected_type, value) in candidates.items():
        if schema.get(name) == expected_type:
            properties[name] = value
    return properties


def batched(items: List[dict], size: int = 100) -> Iterable[List[dict]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def append_blocks(page_id: str, blocks: List[dict]) -> None:
    for batch in batched(blocks):
        notion_request(
            "patch",
            f"/blocks/{page_id}/children",
            json_data={"children": batch},
        )


def list_child_blocks(page_id: str) -> List[dict]:
    children = []
    has_more = True
    cursor = None
    while has_more:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        response = notion_request("get", f"/blocks/{page_id}/children", params=params)
        children.extend(response.get("results", []))
        has_more = response.get("has_more", False)
        cursor = response.get("next_cursor")
    return children


def ensure_page_active(page_id: str) -> bool:
    try:
        page = notion_request("get", f"/pages/{page_id}")
    except requests.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            print(f"[WARN] Notion 页面不存在，将重新创建: {page_id}")
            return False
        raise

    if page.get("archived"):
        print(f"[INF] Notion 页面已归档，正在恢复: {page_id}")
        notion_request("patch", f"/pages/{page_id}", json_data={"archived": False})
    return True


def archive_existing_blocks(page_id: str) -> None:
    for child in list_child_blocks(page_id):
        if child.get("archived"):
            continue
        try:
            notion_request("patch", f"/blocks/{child['id']}", json_data={"archived": True})
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 400:
                print(f"[WARN] 跳过无法归档的 block: {child['id']}")
                continue
            raise


def query_database(filter_body: dict) -> List[dict]:
    response = notion_request(
        "post",
        f"/databases/{DATABASE_ID}/query",
        json_data={
            "filter": filter_body,
            "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
            "page_size": 10,
        },
    )
    return response.get("results", [])


def find_existing_page_id(page_info: Dict[str, Any], schema: Dict[str, str]) -> Optional[str]:
    """Find an existing Notion page before creating a new one.

    Local Hugo files may not have a notion_id. MDFilename is the stable key that
    prevents tag-only edits from creating duplicate Notion rows.
    """
    candidates = []
    md_filename = page_info.get("md_filename", "").strip()
    if md_filename and schema.get("MDFilename") == "rich_text":
        candidates.append(
            (
                "MDFilename",
                md_filename,
                {"property": "MDFilename", "rich_text": {"equals": md_filename}},
            )
        )

    title = page_info.get("title", "").strip()
    if title and schema.get("Title") == "title":
        candidates.append(
            (
                "Title",
                title,
                {"property": "Title", "title": {"equals": title}},
            )
        )

    for property_name, value, filter_body in candidates:
        matches = query_database(filter_body)
        if not matches:
            continue
        page_id = matches[0]["id"]
        if len(matches) > 1:
            print(
                f"[WARN] Notion 中 {property_name}={value} 匹配到 {len(matches)} 个页面，"
                f"将更新最早创建的页面: {page_id}"
            )
        else:
            print(f"[INF] 按 {property_name} 找到已有 Notion 页面: {value} ({page_id})")
        return page_id

    return None


def create_or_update_page(page_info: Dict[str, Any], blocks: List[dict], schema: Dict[str, str]) -> str:
    properties = build_properties(page_info, schema)
    notion_id = page_info.get("notion_id")
    if notion_id and ensure_page_active(notion_id):
        print(f"[INF] 更新 Notion 页面: {page_info['title']} ({notion_id})")
        archive_existing_blocks(notion_id)
        notion_request("patch", f"/pages/{notion_id}", json_data={"properties": properties})
        append_blocks(notion_id, blocks)
        return notion_id

    if notion_id:
        print(f"[INF] 原 Notion 页面不可用，重新创建: {page_info['title']}")
    else:
        notion_id = find_existing_page_id(page_info, schema)
        if notion_id and ensure_page_active(notion_id):
            print(f"[INF] 更新已有 Notion 页面: {page_info['title']} ({notion_id})")
            archive_existing_blocks(notion_id)
            notion_request("patch", f"/pages/{notion_id}", json_data={"properties": properties})
            append_blocks(notion_id, blocks)
            return notion_id

    print(f"[INF] 创建 Notion 页面: {page_info['title']}")
    page = notion_request(
        "post",
        "/pages",
        json_data={
            "parent": {"database_id": DATABASE_ID},
            "properties": properties,
        },
    )
    page_id = page["id"]
    append_blocks(page_id, blocks)
    return page_id


def wants_sync(metadata: dict) -> bool:
    value = metadata.get("sync_to_notion")
    if value is None:
        value = metadata.get("sync")
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).lower() in {"true", "yes", "1", "update", "sync"}


def write_sync_state(md_path: Path, post: frontmatter.Post, notion_id: str) -> None:
    changed = False
    if post.metadata.get("notion_id") != notion_id:
        post.metadata["notion_id"] = notion_id
        changed = True
    if post.metadata.get("sync_to_notion") is not False:
        post.metadata["sync_to_notion"] = False
        changed = True
    if changed:
        md_path.write_text(frontmatter.dumps(post), encoding="utf-8")
        print(f"[INF] 已写回 notion_id，并关闭 sync_to_notion: {md_path}")


def should_skip(md_path: Path) -> bool:
    return any(part.startswith(".") for part in md_path.relative_to(OBSIDIAN_SOURCE_DIR).parts)


def normalize_markdown_path(raw_path: str) -> Path:
    md_path = Path(raw_path).expanduser()
    if not md_path.is_absolute():
        md_path = Path.cwd() / md_path
    md_path = md_path.resolve()
    if not md_path.exists():
        raise FileNotFoundError(f"找不到 Markdown 文件: {md_path}")
    if md_path.suffix.lower() != ".md":
        raise ValueError(f"只支持 Markdown 文件: {md_path}")
    return md_path


def should_skip_path(md_path: Path) -> bool:
    try:
        return should_skip(md_path)
    except ValueError:
        return False


def sync_markdown_file(md_path: Path, schema: Dict[str, str]) -> None:
    post = frontmatter.loads(md_path.read_text(encoding="utf-8"))
    page_info = build_page_info(md_path, post)

    if not wants_sync(post.metadata):
        if page_info.get("notion_id"):
            print(f"[INF] 跳过已同步文章（未标记 sync_to_notion）: {md_path.name}")
        else:
            print(f"[INF] 跳过新文章（未标记 sync_to_notion）: {md_path.name}")
        return

    print(f"[INF] 处理文章: {md_path}")
    prepared_content = prepare_markdown_content(post.content, md_path, post.metadata)
    blocks = markdown_to_blocks(prepared_content)
    notion_id = create_or_update_page(page_info, blocks, schema)
    write_sync_state(md_path, post, notion_id)


def main() -> None:
    args = parse_args()
    require_env()
    if not OBSIDIAN_SOURCE_DIR.exists():
        raise FileNotFoundError(f"找不到 Obsidian 目录: {OBSIDIAN_SOURCE_DIR}")

    schema = get_database_schema()
    if args.paths:
        markdown_files = [normalize_markdown_path(path) for path in args.paths]
        print(f"[INF] 指定同步 {len(markdown_files)} 篇 Markdown")
    else:
        markdown_files = sorted(OBSIDIAN_SOURCE_DIR.rglob("*.md"))
        print(f"[INF] 找到 {len(markdown_files)} 篇 Markdown")

    for md_path in markdown_files:
        if should_skip_path(md_path):
            continue
        sync_markdown_file(md_path, schema)

    print("[INF] Obsidian 同步到 Notion 完成")


if __name__ == "__main__":
    main()
