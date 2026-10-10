#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ -n "$(git status --porcelain)" ]]; then
  echo '请先提交并推送本地改动；发布使用 GitHub 上的 master。' >&2
  exit 1
fi
git fetch origin master
if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/master)" ]]; then
  echo '当前提交与 origin/master 不一致，请先同步。' >&2
  exit 1
fi
gh workflow run notion-to-blog.yml --ref master -f sync_notion=false
echo '已启动统一发布流程。可用 gh run list --workflow notion-to-blog.yml 查看结果。'
