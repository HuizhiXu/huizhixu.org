import time

import requests


def notion_request(token, method, path, params=None, json_data=None):
    """Do not retry ambiguous writes: appending blocks is not idempotent."""
    read_only = method.lower() == "get" or path.endswith("/query")
    for attempt in range(3):
        try:
            response = requests.request(
                method, "https://api.notion.com/v1" + path,
                headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28",
                         "Content-Type": "application/json"},
                params=params, json=json_data, timeout=60,
            )
        except (requests.ConnectionError, requests.Timeout):
            if not read_only or attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))
            continue
        if attempt < 2 and (response.status_code == 429 or (read_only and response.status_code >= 500)):
            time.sleep(float(response.headers.get("Retry-After", 2 ** (attempt + 1))))
            continue
        response.raise_for_status()
        return response.json() if response.text else {}
