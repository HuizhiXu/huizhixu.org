import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAG_ALIASES = {"comfy-ui": "comfyui", "paper": "paper-review", "paperreview": "paper-review"}


def load_local_env(env_path=None):
    env_path = Path(env_path) if env_path is not None else REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def normalize_tags(value):
    raw = value if isinstance(value, list) else str(value).split(",") if value is not None else []
    tags = []
    for item in raw:
        tag = str(item).strip().lower().replace("_", "-").replace(" ", "-")
        tag = TAG_ALIASES.get(tag, tag)
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def atomic_write(path, text):
    """Replace a local state/content file only after the entire write succeeds."""
    import tempfile

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as f:
        temporary = Path(f.name)
        try:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
