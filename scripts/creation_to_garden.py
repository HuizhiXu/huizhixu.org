"""Safely stage one Creation blog draft in the existing Garden database.

This is an opt-in bridge, NOT a publisher. Dry-run is the default; --apply
creates/updates a Garden Draft only. It never changes PublishStatus to Publish
or Update, creates GitHub issues, or starts a deployment.
"""
import argparse
import json
import os
import re
from typing import Callable

from publishing.config import load_local_env
from publishing.http import notion_request
from publishing.markdown import convert_page


def canonical_id(value):
    return str(value or "").replace("-", "").lower()


def property_text(page, name):
    prop = page.get("properties", {}).get(name, {})
    items = prop.get("title") or prop.get("rich_text") or []
    return "".join(part.get("plain_text", part.get("text", {}).get("content", ""))
                   for part in items).strip()


def property_select(page, name):
    return (page.get("properties", {}).get(name, {}).get("select") or {}).get("name")


def source_mentions(page):
    mentions = []
    for part in page.get("properties", {}).get("Article", {}).get("rich_text", []):
        mention = part.get("mention") or {}
        if part.get("type") == "mention" and mention.get("type") == "page":
            mentions.append(canonical_id((mention.get("page") or {}).get("id")))
    return mentions


def check_source(source, expected_database_id):
    parent = source.get("parent") or {}
    source_parent = parent.get("database_id") or parent.get("data_source_id")
    if canonical_id(source_parent) != canonical_id(expected_database_id):
        raise ValueError("The source page is not in the configured Creation Works database")
    title = property_text(source, "作品")
    if not title:
        raise ValueError("Creation page must have a 作品 title")
    platform = property_select(source, "发布平台")
    if platform not in (None, "个人博客"):
        raise ValueError("This bridge accepts only a blog draft, not a social-media version")
    language = {"中文": "Chinese", "英文": "English", "德文": "German"}.get(
        property_select(source, "语言"), "Chinese"
    )
    if not re.fullmatch(r"[0-9a-f]{32}", canonical_id(source.get("id"))):
        raise ValueError("Invalid Creation page id")
    description = property_text(source, "摘要")
    if len(title) > 2000 or len(description) > 2000:
        raise ValueError("Title or description exceeds a Notion rich-text limit")
    return {"title": title, "description": description, "language": language}


def fetch_all_garden(request: Callable, garden_database_id: str):
    pages, cursor = [], None
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        response = request("post", f"/databases/{garden_database_id}/query", json_data=payload)
        pages.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
        if not cursor:
            raise RuntimeError("Garden pagination is incomplete; refusing to create a page")
    return pages


def resolve_garden_page(garden_pages, source_id, title):
    matches = [page for page in garden_pages
               if canonical_id(source_id) in source_mentions(page)]
    if len(matches) > 1:
        raise ValueError("Multiple Garden pages reference this Creation page; fix duplicates first")
    if matches:
        page = matches[0]
        if property_select(page, "PublishStatus") != "Draft":
            raise ValueError("Refusing to edit a non-Draft Garden page")
        return page
    # Old Garden posts have no Creation link; never silently duplicate one.
    same_title = [page for page in garden_pages if property_text(page, "Title") == title]
    if same_title:
        raise ValueError("A Garden article with the same title already exists; link it manually")
    return None


def text_value(value):
    return [{"type": "text", "text": {"content": value}}]


def garden_properties(source_id, fields, category):
    return {
        "Title": {"title": text_value(fields["title"])},
        "Description": {"rich_text": text_value(fields["description"]) if fields["description"] else []},
        "Article": {"rich_text": [{
            "type": "mention",
            "mention": {"type": "page", "page": {"id": source_id}},
        }]},
        "Language": {"select": {"name": fields["language"]}},
        "Category": {"select": {"name": category}},
    }


def stage_one(request, source_id, works_database_id, garden_database_id,
              category="Life", apply=False):
    """Return a plan or stage a Draft. Never marks any article for publication."""
    if category not in ("Life", "KnowHow"):
        raise ValueError("Only Life and KnowHow article categories are supported")
    source = request("get", f"/pages/{source_id}")
    fields = check_source(source, works_database_id)

    # Preflight conversion verifies this particular page has content and only
    # supported blocks. Images use placeholders: no download or upload in dry-run.
    preview = convert_page(source["id"], request,
                           lambda _: "https://example.invalid/image-preview")
    if not preview.strip():
        raise ValueError("Creation page has no article body")

    pages = fetch_all_garden(request, garden_database_id)
    existing = resolve_garden_page(pages, source["id"], fields["title"])
    operation = "update Draft" if existing else "create Draft"
    result = {
        "mode": "apply" if apply else "dry-run",
        "operation": operation,
        "creation_id": source["id"],
        "garden_id": existing.get("id") if existing else None,
        "title": fields["title"],
        "category": category,
        "preview_characters": len(preview),
        "status": "Draft",
    }
    if not apply:
        return result

    props = garden_properties(source["id"], fields, category)
    if existing:
        response = request("patch", f"/pages/{existing['id']}",
                           json_data={"properties": props})
    else:
        props["PublishStatus"] = {"select": {"name": "Draft"}}
        response = request("post", "/pages", json_data={
            "parent": {"database_id": garden_database_id},
            "properties": props,
        })
    result["garden_id"] = response["id"]
    return result


def main():
    parser = argparse.ArgumentParser(description="Stage a single Creation article in Garden")
    parser.add_argument("source_page_id", help="Creation Works page UUID")
    parser.add_argument("--category", choices=("Life", "KnowHow"), default="Life")
    parser.add_argument("--apply", action="store_true",
                        help="Opt in to writing a Garden Draft; never publishes")
    args = parser.parse_args()
    load_local_env()
    token = os.getenv("NOTION_TOKEN")
    works_id = os.getenv("CREATION_DATABASE_ID")
    garden_id = os.getenv("NOTION_DATABASE_ID")
    if not token or not works_id or not garden_id:
        parser.error("NOTION_TOKEN, CREATION_DATABASE_ID and NOTION_DATABASE_ID are required")
    request = lambda method, path, **kw: notion_request(token, method, path, **kw)
    print(json.dumps(stage_one(request, args.source_page_id, works_id, garden_id,
                               category=args.category, apply=args.apply),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
