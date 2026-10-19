"""Offline tests for the opt-in Creation -> Garden draft bridge."""
import importlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from publishing import config

with patch.object(config, "load_local_env"):
    bridge = importlib.import_module("creation_to_garden")

WORKS = "f969f062-0221-45f5-9cec-56cea103a98a"
GARDEN = "211a221e-f6ab-8099-93ed-000b3f6f5616"
SOURCE = "3f9a221ef6ab816590beea957c3eb6cc"


def txt(v):
    return {"type": "text", "plain_text": v}


def source(platform="个人博客"):
    return {
        "id": SOURCE, "parent": {"database_id": WORKS},
        "properties": {
            "作品": {"title": [txt("Test Article")]},
            "摘要": {"rich_text": [txt("A safe test")]},
            "语言": {"select": {"name": "中文"}},
            "发布平台": {"select": {"name": platform}},
        },
    }


def garden(linked=None, title="Test Article", status="Draft"):
    items = []
    if linked:
        items = [{"type": "mention", "mention": {
            "type": "page", "page": {"id": linked}}}]
    return {
        "id": "garden-page",
        "properties": {
            "Title": {"title": [txt(title)]},
            "PublishStatus": {"select": {"name": status}},
            "Article": {"rich_text": items},
        },
    }


class BridgeTests(unittest.TestCase):
    def request(self, pages, source_page=None, paginated=False):
        writes = []
        src = source_page or source()
        def handle(method, path, **kwargs):
            if method == "get" and path == f"/pages/{SOURCE}":
                return src
            if method == "get" and path == f"/blocks/{SOURCE}/children":
                return {"results": [{
                    "id": "paragraph", "type": "paragraph",
                    "paragraph": {"rich_text": [txt("Safe test body")]}
                }], "has_more": False}
            if method == "post" and path == f"/databases/{GARDEN}/query":
                if paginated and not kwargs["json_data"].get("start_cursor"):
                    return {"results": pages[:1], "has_more": True,
                            "next_cursor": "second"}
                return {"results": pages[1:] if paginated else pages,
                        "has_more": False}
            if method in ("post", "patch"):
                writes.append((method, path, kwargs["json_data"]))
                return {"id": "created-garden"}
            raise AssertionError((method, path))
        return handle, writes

    def test_dry_run_never_writes(self):
        call, writes = self.request([])
        plan = bridge.stage_one(call, SOURCE, WORKS, GARDEN)
        self.assertEqual(plan["operation"], "create Draft")
        self.assertEqual(writes, [])

    def test_apply_creates_draft_with_mention(self):
        call, writes = self.request([])
        bridge.stage_one(call, SOURCE, WORKS, GARDEN, apply=True)
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0][1], "/pages")
        self.assertEqual(writes[0][2]["properties"]["PublishStatus"]["select"]["name"], "Draft")
        self.assertEqual(writes[0][2]["properties"]["Article"]["rich_text"][0]["mention"]["page"]["id"], SOURCE)

    def test_repeated_apply_updates_same_draft(self):
        call, writes = self.request([garden(linked=SOURCE)])
        plan = bridge.stage_one(call, SOURCE, WORKS, GARDEN, apply=True)
        self.assertEqual(plan["operation"], "update Draft")
        self.assertEqual(writes[0][1], "/pages/garden-page")
        self.assertNotIn("PublishStatus", writes[0][2]["properties"])

    def test_reject_existing_title_and_non_draft(self):
        for match in (garden(), garden(linked=SOURCE, status="Published")):
            with self.subTest(match=match):
                call, writes = self.request([match])
                with self.assertRaises(ValueError):
                    bridge.stage_one(call, SOURCE, WORKS, GARDEN, apply=True)
                self.assertEqual(writes, [])

    def test_reject_multiple_matches(self):
        call, writes = self.request([garden(linked=SOURCE), garden(linked=SOURCE)])
        with self.assertRaisesRegex(ValueError, "Multiple"):
            bridge.stage_one(call, SOURCE, WORKS, GARDEN)
        self.assertEqual(writes, [])

    def test_reject_social_version(self):
        call, writes = self.request([], source_page=source(platform="小红书"))
        with self.assertRaisesRegex(ValueError, "blog draft"):
            bridge.stage_one(call, SOURCE, WORKS, GARDEN)
        self.assertEqual(writes, [])

    def test_paginated_lookup(self):
        call, writes = self.request([garden(linked=SOURCE), garden(linked=SOURCE)],
                                    paginated=True)
        with self.assertRaisesRegex(ValueError, "Multiple"):
            bridge.stage_one(call, SOURCE, WORKS, GARDEN)
        self.assertEqual(writes, [])


if __name__ == "__main__":
    unittest.main()
