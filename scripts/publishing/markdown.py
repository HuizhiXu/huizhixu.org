"""Convert supported Notion blocks without silently discarding content."""
import re


def rich_text(items):
    result = []
    for item in items:
        if item.get("type") == "equation":
            result.append("$" + item["equation"]["expression"] + "$")
            continue
        text = item.get("plain_text", item.get("text", {}).get("content", ""))
        annotations = item.get("annotations", {})
        if annotations.get("code"):
            ticks = "`" * (max([len(s) for s in re.findall(r"`+", text)] or [0]) + 1)
            text = ticks + " " + text + " " + ticks
        for name, delimiter in (("bold", "**"), ("italic", "*"), ("strikethrough", "~~")):
            if annotations.get(name) and text.strip():
                leading = text[:len(text) - len(text.lstrip())]
                trailing = text[len(text.rstrip()):]
                text = leading + delimiter + text.strip() + delimiter + trailing
        if annotations.get("underline"):
            text = "<u>" + text + "</u>"
        href = item.get("href") or (item.get("text", {}).get("link") or {}).get("url")
        if href:
            text = f"[{text}](<{href}>)"
        result.append(text)
    return "".join(result)


def list_blocks(request, page_id):
    blocks, cursor = [], None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        response = request("get", f"/blocks/{page_id}/children", params=params)
        blocks.extend(response.get("results", []))
        if not response.get("has_more"):
            return blocks
        cursor = response["next_cursor"]


def convert_page(page_id, request, image_url):
    def children(block):
        return list_blocks(request, block["id"]) if block.get("has_children") else []

    def render(block):
        kind = block["type"]
        data = block.get(kind, {})
        text = rich_text(data.get("rich_text", []))
        nested = children(block)
        if kind == "table":
            rows = []
            for row in nested:
                if row["type"] != "table_row":
                    raise ValueError("Unexpected child in Notion table")
                cells = [rich_text(cell).replace("|", r"\|").replace("\n", "<br>")
                         for cell in row["table_row"]["cells"]]
                rows.append("| " + " | ".join(cells) + " |")
            if not rows:
                return ""
            separator = "| " + " | ".join(["---"] * data["table_width"]) + " |"
            if data.get("has_column_header"):
                rows.insert(1, separator)
            else:
                rows[:0] = ["| " + " | ".join([""] * data["table_width"]) + " |", separator]
            return "\n".join(rows)
        child_text = "\n\n".join(render(child) for child in nested)
        if kind == "paragraph":
            return text + ("\n\n" + child_text if child_text else "")
        if kind.startswith("heading_"):
            return "#" * int(kind[-1]) + " " + text + ("\n\n" + child_text if child_text else "")
        if kind in {"bulleted_list_item", "numbered_list_item", "to_do"}:
            prefix = {"bulleted_list_item": "- ", "numbered_list_item": "1. ",
                      "to_do": "- [x] " if data.get("checked") else "- [ ] "}[kind]
            lines = text.split("\n")
            result = prefix + lines[0]
            if len(lines) > 1:
                result += "\n" + "\n".join(" " * len(prefix) + line for line in lines[1:])
            if child_text:
                result += "\n\n" + "\n".join(" " * len(prefix) + line for line in child_text.split("\n"))
            return result
        if kind in {"quote", "callout"}:
            body = text + ("\n\n" + child_text if child_text else "")
            return "\n".join("> " + line for line in body.split("\n"))
        if kind == "toggle":
            return text + ("\n\n" + child_text if child_text else "")
        if kind in {"column_list", "column", "synced_block"}:
            if kind == "synced_block" and not nested and data.get("synced_from"):
                return convert_page(data["synced_from"]["block_id"], request, image_url)
            return child_text
        if kind == "code":
            code = "".join(item.get("plain_text", item.get("text", {}).get("content", "")) for item in data["rich_text"])
            fence = "`" * max(3, max([len(s) + 1 for s in re.findall(r"`+", code)] or [3]))
            language = data.get("language", "")
            if language == "plain text":
                language = "text"
            return f"{fence}{language}\n{code}\n{fence}"
        if kind == "image":
            return f"![{rich_text(data.get('caption', []))}](<{image_url(data)}>)"
        if kind == "equation":
            return "$$\n" + data["expression"] + "\n$$"
        if kind == "divider":
            return "---"
        if kind in {"bookmark", "embed", "link_preview"}:
            return f"[{rich_text(data.get('caption', [])) or data['url']}](<{data['url']}>)"
        if kind == "table_of_contents":
            return ""  # Hugo renders its own table of contents.
        raise ValueError(f"不支持的 Notion block: {kind} ({block.get('id', '?')})，停止发布以免丢失内容")

    return "\n\n".join(render(block) for block in list_blocks(request, page_id)) + "\n"
