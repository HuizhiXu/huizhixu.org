import base64
import hashlib
import time
from pathlib import Path
from urllib.parse import quote

import requests


def upload_image(image_data, image_name, folder_date, *, token, repo, branch):
    filename = hashlib.md5(image_data).hexdigest()[:8] + (Path(image_name).suffix or ".png")
    path = f"{folder_date}/{filename}" if folder_date else filename
    url = f"https://api.github.com/repos/{repo}/contents/{quote(path)}"
    raw = f"https://raw.githubusercontent.com/{repo}/{branch}/{quote(path)}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    for attempt in range(3):
        try:
            existing = requests.get(url, headers=headers, params={"ref": branch}, timeout=30)
            if existing.status_code == 200:
                return raw
            if existing.status_code != 404:
                existing.raise_for_status()
            response = requests.put(url, headers=headers, json={
                "message": f"Upload {image_name}", "branch": branch,
                "content": base64.b64encode(image_data).decode(),
            }, timeout=30)
            response.raise_for_status()
            return raw
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))
