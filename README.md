# hugoblog — Obsidian → Notion → 博客

个人博客源码仓库，使用 Hugo 构建，部署到 GitHub Pages。

- 博客源码：`HuizhiXu/huizhixu.org`
- 线上站点：`https://huizhixu.github.io`
- 图片仓库：`HuizhiXu/pictures`

## 发布流程总览

```
Obsidian 写文章
    ↓  frontmatter 设 sync_to_notion: true
    ↓  python scripts/obsidian_to_notion.py
Notion 数据库（编辑 / 确认）
    ↓  PublishStatus 改为 Publish 或 Update
GitHub Issue（标题含 notion-ci）
    ↓  CI 自动构建并部署
博客上线
```

---

## 一、前置准备（一次性）

### 本地环境

```bash
cd ~/hugoblog
cp .env.example .env        # 填入真实 token
npm ci                      # Tailwind/PostCSS，Hugo 主题样式构建需要
pip install -r scripts/requirements.txt
# 或 uv sync
```

### `.env` 必填项

| 变量 | 用途 |
|------|------|
| `NOTION_TOKEN` | Notion Integration token |
| `NOTION_DATABASE_ID` | 博客文章数据库 ID |
| `CHECKOUT_TOKEN` | GitHub PAT（读写 repo + 上传图片） |

### GitHub Secrets

在 `HuizhiXu/huizhixu.org` → Settings → Secrets 配置：

- `NOTION_TOKEN`
- `NOTION_DATABASE_ID`
- `CHECKOUT_TOKEN`

### Notion Integration

创建 Integration 并连接到你的文章数据库，需有读写权限。

---

## 二、Obsidian frontmatter

只有 **`sync_to_notion: true`** 的文章才会被同步到 Notion。

### 技术文章（KnowHow 栏目）

```yaml
---
title: 文章标题
date: 2026-05-28
tags: [tech, ai, agent]
series: Agent 工具实践
category: KnowHow
language: Chinese
description: 摘要
publish_status: Draft
md_filename: 20260528-文章名.md
notion_id: xxx              # 首次同步后自动写回
sync_to_notion: true        # 同步成功后自动改回 false
---
```

### 生活文章（Life 栏目）

```yaml
---
title: 我的柏林初雪
date: 2026-05-28
tags: [life, read]
category: Life
language: Chinese
description: 摘要
publish_status: Draft
md_filename: 20260528-我的柏林初雪.md
sync_to_notion: true
---
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `sync_to_notion` | 同步时必填 | 设为 `true` 才同步；成功后脚本自动改回 `false` |
| `category` | 建议填 | 博客栏目：`KnowHow` / `Life` / `Link` / `Page` |
| `tags` | 可选 | 主题标签，如 `tech`、`ai`、`llm`、`agent`（**不是栏目**） |
| `series` | 可选 | 系列名；同系列文章会显示上一篇 / 下一篇 |
| `publish_status` | 可选 | 同步到 Notion 的初始状态，默认 `Draft` |
| `notion_id` | 自动 | 首次同步后写回，用于后续更新同一页面 |
| `md_filename` | 可选 | 博客文件名，默认用 Obsidian 文件名 |

不写 `category` 时，默认进 **KnowHow**（可在 `.env` 用 `DEFAULT_NOTION_CATEGORY` 修改）。

### 推荐 tags

优先使用稳定的主题标签，避免把年份当 tag：

`tech`、`ai`、`llm`、`agent`、`rag`、`comfyui`、`obsidian`、`paper-review`、`bayesian`、`read`、`life`

### 栏目与目录

| category | 博客栏目 | 写入目录 |
|----------|---------|---------|
| KnowHow | 技术 | `content/chs/know_how/` |
| Life | 生活 | `content/chs/life/` |
| Page | 独立页面 | `content/chs/page/` |

### 图片

- `![[图片.png]]` 或 `![](本地路径)` 同步时会上传到 `HuizhiXu/pictures`
- 按文件名开头的 `YYYYMMDD` 分文件夹存放

---

## 三、Obsidian → Notion

```bash
cd ~/hugoblog
source .env
python scripts/obsidian_to_notion.py
```

| 情况 | 行为 |
|------|------|
| `sync_to_notion: true` | 同步到 Notion（新建或更新） |
| 未设 / `false` | 跳过 |
| 同步成功后 | 写回 `notion_id`，`sync_to_notion` 改回 `false` |

同步后 Notion 的 `PublishStatus` 默认为 **Draft**，不会触发博客发布。

---

## 四、Hugo content → Obsidian → Notion

如果你直接在博客仓库的 `content/...` 里修改了文章，可以先同步回 Obsidian，再继续同步到 Notion：

```bash
cd ~/hugoblog
python scripts/blog_to_obsidian.py content/chs/page/about.md --notion
```

如果一次改了多篇文章（例如批量改 tags），可以同步 git 中所有已改动的 `content/**/*.md`：

```bash
python scripts/blog_to_obsidian.py --changed --notion
```

脚本会：

| 行为 | 说明 |
|------|------|
| 写回 Obsidian | 优先按 `notion_id` 找已有笔记，其次按文件名匹配；找不到则新建 |
| 设置同步标记 | 自动写入 `sync_to_notion: true`、`md_filename`、`language`、`category` |
| 可选同步 Notion | 加 `--notion` 时只会把本次写回的 Obsidian 文件继续同步到 Notion |
| Notion 防重复 | 没有 `notion_id` 时，会先按 `MDFilename` 查找已有 Notion 页面，找到则更新 |

只想先看看会写到哪里，不真正改文件：

```bash
python scripts/blog_to_obsidian.py --changed --dry-run
```

---

## 五、Notion → 博客

### 1. 在 Notion 改发布状态

| PublishStatus | 含义 |
|---------------|------|
| Draft | 草稿，CI 不处理 |
| **Publish** | 新文章，准备发布 |
| **Update** | 已发布文章，强制覆盖更新 |
| Published | CI 成功后自动设置 |

### 2. 触发 CI

在 [HuizhiXu/huizhixu.org](https://github.com/HuizhiXu/huizhixu.org/issues/new) 新建 Issue，**标题含 `notion-ci`**，必须本人创建。

CI 会自动：拉取 Notion 文章 → 生成 Markdown → 上传图片 → Hugo 构建 → 部署到 `huizhixu.github.io`。

---

## 六、日常速查

### 发新文章

```
1. Obsidian 写好，设 sync_to_notion: true
2. python scripts/obsidian_to_notion.py
3. Notion 检查 → PublishStatus 改为 Publish
4. GitHub 建 notion-ci issue
```

### 修改已发布文章

```
1. Obsidian 改文，设 sync_to_notion: true
2. python scripts/obsidian_to_notion.py
3. Notion → PublishStatus 改为 Update
4. 建 notion-ci issue
```

### 只同步到 Notion、不上博客

```
设 sync_to_notion: true → 运行脚本
保持 PublishStatus = Draft
```

### 直接在博客仓库改了文章

```
1. 单篇：python scripts/blog_to_obsidian.py content/chs/page/about.md --notion
2. 多篇：python scripts/blog_to_obsidian.py --changed --notion
3. Notion 检查 → PublishStatus 改为 Update
4. 建 notion-ci issue
```

### 批量改 tags

```
1. python scripts/blog_to_obsidian.py --changed --dry-run
2. 确认列表没问题后：python scripts/blog_to_obsidian.py --changed --notion
3. Notion 检查 → PublishStatus 改为 Update
4. 建 notion-ci issue
```

---

## 七、常见问题

**运行脚本后没进 Notion**
- 是否设了 `sync_to_notion: true`？

**博客有标题但正文为空**
- 已在 2026-06 修复（Notion `Article` 字段为空时误读问题）
- 补救：Notion 改 `Update` → 重新建 `notion-ci` issue

**CI 跑了但没更新**
- `PublishStatus` 是否为 `Publish` / `Update`？
- 同名文件已存在且状态是 `Publish`（非 `Update`）→ 会跳过

---

## 相关文件

| 文件 | 作用 |
|------|------|
| `scripts/blog_to_obsidian.py` | Hugo content → Obsidian，可选继续同步 Notion |
| `scripts/obsidian_to_notion.py` | Obsidian → Notion |
| `scripts/notion_to_blog.py` | Notion → Hugo Markdown |
| `.github/workflows/notion-to-blog.yml` | CI 触发与部署 |
| `.env` | 本地密钥（勿提交 git） |
