# MNEMOSYNE.md

Project memory anchor for context compression, handoff, and continuity.

## Current Snapshot

- Date: 2026-08-13
- Active goal: Complete.
- Release: `photos-1-15000`, 30 ZIP assets, all uploaded.
- Gallery: 15,000 assets, all `ready`, with one public WebP URL per image.
- Public site: https://arthurescc.github.io/studio-background-portfolio/
- Verification: Release 30/30 uploaded; catalog 15,000/15,000 ready; mapping errors 0; public image samples returned HTTP 200.

## Stable Decisions

- Gallery card clicks open an image preview dialog. They must not download or navigate to a ZIP.
- `originalUrl` is the per-image GitHub Pages WebP URL; `archiveUrl` is the containing Release ZIP URL.
- Public copy must not expose ingestion, upload, pre-registration, or internal operating instructions.
- Public batch name is `Studio Background Collection`.

## Known Constraints

- Browsers cannot address an individual JPG inside a ZIP. Public per-image URLs therefore point to independently published WebP previews.
- Original JPG files remain stored in 500-image ZIP archives in GitHub Release `photos-1-15000`.

## Verification Commands

- `gh api repos/Arthurescc/studio-background-portfolio/releases/369420032/assets`
- Check `docs/data/catalog.json` for 15,000 unique ready assets and archive range mapping.
- Request public `data/catalog.json` and sample thumbnail URLs after Pages deployment.

## Work Log

### 2026-08-13

- Uploaded and verified all 30 ZIP archives for images 1-15000.
- Imported all images into the public gallery and generated 15,000 WebP previews.
- Removed internal upload panels and internal terminology from the visitor-facing site.
- Changed card interaction from ZIP download to an accessible image preview dialog.
- Corrected all 15,000 `originalUrl` fields to independent public image URLs.
- Latest relevant commits: `23762ab` (preview interaction), `11fbeea` (per-image URLs).
