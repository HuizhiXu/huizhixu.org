import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import frontmatter


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


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = REPO_ROOT / "content"
OBSIDIAN_SOURCE_DIR = Path(
    os.getenv(
        "OBSIDIAN_SOURCE_DIR",
        "/Users/Sophia/Library/CloudStorage/SynologyDrive-20260618/04_存档与收件箱/01Archive/Published/Book_G",
    )
).expanduser()

LANGUAGE_BY_CODE = {
    "chs": "Chinese",
    "de": "German",
    "en": "English",
}

CATEGORY_BY_SECTION = {
    "know_how": "KnowHow",
    "life": "Life",
    "page": "Page",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync Hugo content Markdown files back to Obsidian, then optionally to Notion."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Hugo content Markdown files, for example content/chs/page/about.md.",
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Sync changed/new tracked or untracked content Markdown files from git status.",
    )
    parser.add_argument(
        "--notion",
        action="store_true",
        help="Run scripts/obsidian_to_notion.py after writing Obsidian files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be written without changing files.",
    )
    return parser.parse_args()


def iter_obsidian_markdown() -> Iterable[Path]:
    if not OBSIDIAN_SOURCE_DIR.exists():
        return []
    return OBSIDIAN_SOURCE_DIR.rglob("*.md")


def read_post(path: Path) -> frontmatter.Post:
    return frontmatter.loads(path.read_text(encoding="utf-8"))


def normalize_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def git_status_entries() -> List[tuple[str, str]]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "-z", "--", "content"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=False,
    )
    fields = result.stdout.split(b"\0")
    entries: List[tuple[str, str]] = []
    index = 0
    while index < len(fields):
        field = fields[index]
        index += 1
        if not field:
            continue

        status = field[:2].decode("ascii", errors="replace")
        path = field[3:].decode("utf-8")

        if "R" in status or "C" in status:
            if index >= len(fields):
                break
            new_path = fields[index].decode("utf-8")
            index += 1
            path = new_path

        entries.append((status, path))
    return entries


def changed_content_markdown_files() -> List[Path]:
    paths: List[Path] = []
    seen = set()
    for status, raw_path in git_status_entries():
        if "D" in status:
            continue
        path = normalize_path(raw_path)
        try:
            path.relative_to(CONTENT_ROOT)
        except ValueError:
            continue
        if path.name == "_index.md" or path.suffix.lower() != ".md" or not path.exists():
            continue
        if path in seen:
            continue
        seen.add(path)
        paths.append(path)
    return paths


def content_parts(source_path: Path) -> tuple[str, str]:
    try:
        relative = source_path.relative_to(CONTENT_ROOT)
    except ValueError as exc:
        raise ValueError(f"文件不在 Hugo content 目录下: {source_path}") from exc

    if len(relative.parts) < 3:
        raise ValueError(f"无法从路径推断语言和栏目: {source_path}")

    lang_code, section = relative.parts[0], relative.parts[1]
    return lang_code, section


def infer_language_and_category(source_path: Path) -> tuple[str, str]:
    lang_code, section = content_parts(source_path)
    language = LANGUAGE_BY_CODE.get(lang_code, "Chinese")
    category = CATEGORY_BY_SECTION.get(section, "KnowHow")
    return language, category


def build_obsidian_index() -> Dict[str, Dict[str, Path]]:
    by_notion_id: Dict[str, Path] = {}
    by_filename: Dict[str, Path] = {}

    for md_path in iter_obsidian_markdown():
        by_filename.setdefault(md_path.name, md_path)
        try:
            post = read_post(md_path)
        except Exception as exc:
            print(f"[WARN] 跳过无法读取 frontmatter 的 Obsidian 文件: {md_path}: {exc}")
            continue

        notion_id = str(post.metadata.get("notion_id", "")).strip()
        if notion_id:
            by_notion_id.setdefault(notion_id, md_path)

        md_filename = str(post.metadata.get("md_filename", "")).strip()
        if md_filename:
            by_filename.setdefault(md_filename, md_path)

    return {"by_notion_id": by_notion_id, "by_filename": by_filename}


def choose_destination(
    source_path: Path,
    post: frontmatter.Post,
    index: Dict[str, Dict[str, Path]],
) -> Path:
    notion_id = str(post.metadata.get("notion_id", "")).strip()
    if notion_id and notion_id in index["by_notion_id"]:
        return index["by_notion_id"][notion_id]

    md_filename = str(post.metadata.get("md_filename", "")).strip() or source_path.name
    if md_filename in index["by_filename"]:
        return index["by_filename"][md_filename]

    if source_path.name in index["by_filename"]:
        return index["by_filename"][source_path.name]

    return OBSIDIAN_SOURCE_DIR / md_filename


def merge_existing_notion_id(destination: Path, post: frontmatter.Post) -> None:
    if post.metadata.get("notion_id") or not destination.exists():
        return

    try:
        existing_post = read_post(destination)
    except Exception:
        return

    notion_id = existing_post.metadata.get("notion_id")
    if notion_id:
        post.metadata["notion_id"] = notion_id


def prepare_post(source_path: Path, post: frontmatter.Post) -> frontmatter.Post:
    language, category = infer_language_and_category(source_path)
    post.metadata["language"] = post.metadata.get("language") or language
    post.metadata["category"] = post.metadata.get("category") or category
    post.metadata["md_filename"] = post.metadata.get("md_filename") or source_path.name
    post.metadata["publish_status"] = post.metadata.get("publish_status") or "Draft"
    post.metadata["sync_to_notion"] = True
    return post


def sync_file(source_path: Path, index: Dict[str, Dict[str, Path]], dry_run: bool) -> Optional[Path]:
    if not source_path.exists():
        raise FileNotFoundError(f"找不到文件: {source_path}")
    if source_path.suffix.lower() != ".md":
        raise ValueError(f"只支持 Markdown 文件: {source_path}")

    post = read_post(source_path)
    destination = choose_destination(source_path, post, index)
    merge_existing_notion_id(destination, post)
    post = prepare_post(source_path, post)

    action = "更新" if destination.exists() else "创建"
    print(f"[INF] {action} Obsidian 文件: {destination}")

    if dry_run:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(frontmatter.dumps(post), encoding="utf-8")
    return destination


def run_obsidian_to_notion(destinations: List[Path]) -> None:
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "obsidian_to_notion.py"),
        *[str(path) for path in destinations],
    ]
    print(f"[INF] 运行 Notion 同步: {' '.join(command)}")
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> None:
    args = parse_args()
    if not args.paths and not args.changed:
        raise ValueError("请指定 Markdown 文件，或使用 --changed 同步 git 中已改动的 content Markdown")
    if not OBSIDIAN_SOURCE_DIR.exists():
        raise FileNotFoundError(f"找不到 Obsidian 目录: {OBSIDIAN_SOURCE_DIR}")

    source_paths = [normalize_path(path) for path in args.paths]
    if args.changed:
        changed_paths = changed_content_markdown_files()
        print(f"[INF] 从 git 状态找到 {len(changed_paths)} 篇已改动的 content Markdown")
        seen = set(source_paths)
        for path in changed_paths:
            if path not in seen:
                source_paths.append(path)
                seen.add(path)

    index = build_obsidian_index()
    destinations = []
    for source_path in source_paths:
        destination = sync_file(source_path, index, args.dry_run)
        if destination:
            destinations.append(destination)

    if args.notion:
        if args.dry_run:
            print("[INF] dry-run 模式，不运行 Notion 同步")
        else:
            run_obsidian_to_notion(destinations)

    print("[INF] Hugo content 同步到 Obsidian 完成")


if __name__ == "__main__":
    main()
