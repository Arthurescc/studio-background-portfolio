#!/usr/bin/env python3
"""Reserve deterministic per-image URLs from ZIP filenames before image extraction."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from import_release import friendly_name, load_catalog, safe_image_members, slugify


def reserve_archive(zip_path: Path, tag: str, repo: str) -> tuple[dict, list[dict]]:
    import zipfile

    batch_id = slugify(f"{tag}-{zip_path.stem}")
    batch_name = friendly_name(zip_path.stem)
    archive_url = f"https://github.com/{repo}/releases/download/{quote(tag, safe='')}/{quote(zip_path.name)}"
    assets: list[dict] = []

    with zipfile.ZipFile(zip_path) as archive:
        members = safe_image_members(archive)
        for index, info in enumerate(members, start=1):
            digest = hashlib.sha1(info.filename.encode("utf-8", "surrogatepass")).hexdigest()[:14]
            suffix = PurePosixPath(info.filename).suffix.lower()
            original_name = f"{batch_id}--{index:05d}-{digest}{suffix}"
            original_url = f"https://github.com/{repo}/releases/download/{quote(tag, safe='')}/{quote(original_name)}"
            assets.append(
                {
                    "id": f"{batch_id}-{digest}",
                    "title": friendly_name(info.filename),
                    "batchId": batch_id,
                    "batchName": batch_name,
                    "sourcePath": info.filename,
                    "width": 0,
                    "height": 0,
                    "thumbnail": "",
                    "originalName": original_name,
                    "originalUrl": original_url,
                    "archiveName": zip_path.name,
                    "archiveUrl": archive_url,
                    "releaseTag": tag,
                    "status": "reserved",
                }
            )

    return (
        {
            "id": batch_id,
            "name": batch_name,
            "count": len(assets),
            "archiveName": zip_path.name,
            "archiveUrl": archive_url,
            "releaseTag": tag,
            "status": "indexing",
        },
        assets,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--docs-dir", default="docs", type=Path)
    args = parser.parse_args()

    archives = sorted(args.input_dir.glob("*.zip"))
    if not archives:
        raise SystemExit("No ZIP files found")

    catalog_path = args.docs_dir / "data" / "catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog(catalog_path, f"https://github.com/{args.repo}")
    new_batches: list[dict] = []
    new_assets: list[dict] = []
    replaced_ids: set[str] = set()

    for archive in archives:
        batch, assets = reserve_archive(archive, args.tag, args.repo)
        new_batches.append(batch)
        new_assets.extend(assets)
        replaced_ids.add(batch["id"])

    catalog["batches"] = [item for item in catalog["batches"] if item.get("id") not in replaced_ids] + new_batches
    catalog["assets"] = [item for item in catalog["assets"] if item.get("batchId") not in replaced_ids] + new_assets
    catalog["batches"].sort(key=lambda item: (item.get("releaseTag", ""), item.get("name", "")), reverse=True)
    catalog["assets"].sort(key=lambda item: (item.get("releaseTag", ""), item.get("batchName", ""), item.get("sourcePath", "")), reverse=True)
    catalog["generatedAt"] = datetime.now(timezone.utc).isoformat()
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Reserved {len(new_assets)} image URLs from {len(archives)} archive(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
