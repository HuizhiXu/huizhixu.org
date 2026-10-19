# Creation → Garden draft bridge (experimental)

This is a safe first step toward using Creation as the single writing interface for the Hugo blog.

**No automatic publishing is implemented here.** The script neither sets
`PublishStatus=Publish/Update`, triggers GitHub Actions, nor writes to the
Hugo content repository. It creates/updates **Garden Drafts only**, and only
when explicitly run with `--apply`. Without that flag it performs a read-only
dry-run.

## Prerequisites

Existing local blog Python environment and `.env` credentials:
- `NOTION_TOKEN`: integration with access to both databases and both source pages
- `NOTION_DATABASE_ID`: existing Garden publication database ID
- `CREATION_DATABASE_ID`: **Works data source/database ID** (single-source Works DB)

In this workspace the Works database ID is
`7bd26a58-a03a-4e30-9d58-ef975846c6b3`.
The existing Garden database ID is
`211a221e-f6ab-806b-ad42-d2505f023813`.

## Preview one blog draft

```bash
uv run --frozen python scripts/creation_to_garden.py <creation-page-uuid>
```

The preflight checks:
- The source belongs to Creation Works and is a blog version
- The source body can be converted by the current Hugo Markdown converter
- Garden has no ambiguous link or exact-title collision
- Existing linked Garden pages are **Draft** (never overwrite published work)

Image conversion is preflighted with placeholders; a dry-run does **not**
verify external image accessibility or upload any picture.

## Opt in to save the Garden Draft

```bash
uv run --frozen python scripts/creation_to_garden.py <creation-page-uuid> --category Life --apply
```

This stores a **Notion page mention** in Garden's existing `Article` property
pointing back to Creation. Future calls find that same Garden Draft by mention,
so they do not create another item; the Hugo exporter already knows how to
dereference this kind of Article mention.

**Important:** Editing the Creation source later changes the text the existing
Garden blog exporter would read. The existing Garden status must stay Draft
until the later publishing integration is built and verified.

## Not included yet

- A Creation publish button/approval mechanism
- A single-article scoped GitHub Actions deployment
- Automatic publishing status/result/URL callbacks to Publishing
- Production validation of image uploads, markdown formatting and rollback

Do **not** use the normal `notion-ci` issue trigger as a test of this bridge.
That trigger scans all Garden Publish/Update items and deploys the site.
