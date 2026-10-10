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
uv sync --frozen            # 使用 uv.lock 中的固定版本
# 如不用 uv：pip install --require-hashes -r scripts/requirements.txt
```

本项目固定使用 **Hugo 0.152.2 extended**（见 `.hugo-version`）、Python 3.12 和 Node.js 22。`npm run build` 会检查 Hugo 版本；更新版本时需要同步修改 `.hugo-version` 并通过测试。

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

把 Hugo 仓库里**全部**已发布文章一次性写回 Obsidian（并可选同步 Notion）：

```bash
python scripts/blog_to_obsidian.py --all --dry-run   # 先预览
python scripts/blog_to_obsidian.py --all --notion    # 157 篇，Notion 状态设为 Published
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

也可以在 Actions 中手动运行 **Notion To Blog**。默认仅构建并发布仓库当前内容；勾选 `sync_notion` 才会同步 Notion 待发布文章。通过 `notion-ci` Issue 触发时仍会同步 Notion。本地 `bash deploy.sh` 会检查工作区及 `origin/master`，然后通过 GitHub CLI 触发同一个工作流（仅发布现有代码）；需要先提交、推送改动并完成 `gh auth login`。`deploy.ps1` 和旧的 `deploy copy.sh` 都委托给这个入口，不再直接操作 `public/.git` 或强制推送。

CI 顺序：测试 → 导出文章和图片 → Hugo 构建及产物检查 → 提交并推送正文 → 发布到 `huizhixu.github.io` → 回写 `Published`。导出、提交、推送或构建失败均会停止发布。导出的文章若因 `draft`、未来日期或过期时间未进入构建结果，也会停止发布并提示检查。多个发布任务串行执行，普通 push / PR 只执行检查，不部署。

导出脚本单独运行时只写本地 Markdown 和 `.sync-state/publish.json`，不会回写 `Published`。`--finalize` 专供部署成功后的步骤使用，禁止提前手动运行。回写会核对文件哈希与 Notion 页面修改时间；导出后又编辑的页面保留待发布状态。

失败后修复原因，再重新运行完整发布工作流。已有文件记录 `notion_id`，同一页面可以安全重新导出；同名且属于另一个页面的文件会报错。工作流保留 `publish-manifest` artifact 供排查。

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
- 同名旧文件没有 `notion_id` 且内容不同，会报错；确认确实需要覆盖后设为 `Update`。
- 导出后编辑了 Notion 页面，回写会拒绝旧版本；重新执行完整工作流即可。

---

## 八、开发与维护

```bash
npm ci
uv sync --frozen
npm test                         # Python 模拟请求测试 + Node 搜索交互测试
npm run build                    # 生产构建
uv run --frozen python scripts/check_site.py public
npm start                        # 本地预览
```

测试使用假数据和临时目录，不读取本地 `.env`，不调用真实 Notion/GitHub API。`scripts/requirements.txt` 是兼容 pip 的锁文件导出，不要单独修改；依赖调整后使用：

```bash
uv lock
uv export --frozen --format requirements-txt --no-dev --no-emit-project --output-file scripts/requirements.txt
```

目录职责：

- `scripts/publishing/`：环境配置、标签规范化、API 请求、图片上传、Notion 转换及正文替换恢复。
- `scripts/*_to_*.py`：同步入口和流程编排。
- `assets/css/`：按原有级联顺序拆分的样式及本站 PostCSS/Tailwind 配置，构建时合并、压缩并添加指纹。
- `assets/js/search.js`：本站搜索逻辑；索引包含纯文本正文、摘要和标签，首次打开搜索时加载。
- `layouts/`：本站实际定制的模板；完全相同的模板和翻译使用主题回退。
- `themes/blist/`：仓库内保留的 Blist 基础主题（包元数据版本 2.1.0，未记录精确上游提交）；后续更新需检查本地覆盖，不应直接覆盖本站 assets。
- `static/`：保持现有原图 URL；通过资源挂载供 Hugo 生成优化图。首页使用 360/720 宽度 WebP，本地正文 JPEG/PNG/WebP 使用两档适配尺寸及懒加载。远程图片只增加懒加载，不在构建时下载。

### 同步中断时如何恢复

更新已有 Notion 页面会先完整写入新正文，再归档旧 blocks；普通失败尝试恢复旧正文并清理本次新增内容。写入请求超时不会盲目重试，因为服务端可能已经成功执行。

若出现“需要核对中断的同步”，查看 `.sync-state/notion/<page-id>.json`：`old_ids` 是原 blocks，`new_ids` 是已确认新增的 blocks，`archive_attempts` 是尝试归档的原 blocks。`append_pending: true` 表示有一批请求结果未知，不能假定没有写入。

在 Notion 中核对页面及历史记录，恢复旧正文、清理本次残留新增内容（也可从 Obsidian 原文重新确认目标内容）。确认后将该日志移到备份位置，再重试同步。未处理的日志会阻止继续替换该页面，避免反复覆盖。同步期间请避免另一进程或人工同时修改同一页面。

转换器支持段落、标题、链接与常见富文本、嵌套列表、待办、引用、callout、toggle、表格、代码、公式和图片。遇到未支持的 block 会报出类型和 ID，并停止发布；不会静默跳过。图片下载或上传失败也会阻止发布，以免留下临时图片链接。

实现参考：[Notion block 更新接口](https://developers.notion.com/reference/update-a-block)、[Hugo 图片处理](https://gohugo.io/content-management/image-processing/)、[uv 的 GitHub Actions 集成](https://docs.astral.sh/uv/guides/integration/github/)。

## 相关文件

| 文件 | 作用 |
|------|------|
| `scripts/blog_to_obsidian.py` | Hugo content → Obsidian，可选继续同步 Notion |
| `scripts/obsidian_to_notion.py` | Obsidian → Notion |
| `scripts/notion_to_blog.py` | Notion → Hugo Markdown |
| `.github/workflows/notion-to-blog.yml` | CI 触发与部署 |
| `.env` | 本地密钥（勿提交 git） |
