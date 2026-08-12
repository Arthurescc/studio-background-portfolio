#!/usr/bin/env python3
"""Pre-register stable URLs for 1.jpg through 15000.jpg."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


BATCH_ID = "photos-1-15000"
BATCH_NAME = "1.jpg–15000.jpg 预登记"
DEFAULT_COUNT = 15_000


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="Arthurescc/studio-background-portfolio")
    parser.add_argument("--tag", default=BATCH_ID)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--catalog", type=Path, default=Path("docs/data/catalog.json"))
    args = parser.parse_args()

    if args.count < 1 or args.count > DEFAULT_COUNT:
        raise SystemExit(f"count must be between 1 and {DEFAULT_COUNT}")

    catalog = {
        "repositoryUrl": f"https://github.com/{args.repo}",
        "generatedAt": None,
        "batches": [],
        "assets": [],
    }
    if args.catalog.exists():
        try:
            catalog.update(json.loads(args.catalog.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass

    existing = {
        item.get("id"): item
        for item in catalog.get("assets", [])
        if item.get("batchId") == BATCH_ID
    }
    release_url = f"https://github.com/{args.repo}/releases/tag/{quote(args.tag, safe='')}"
    assets = []
    for number in range(1, args.count + 1):
        source_name = f"{number}.jpg"
        original_name = f"photo-{number:05d}.jpg"
        asset_id = f"{BATCH_ID}-{number:05d}"
        prior = existing.get(asset_id, {})
        status = "ready" if prior.get("status") == "ready" else "reserved"
        assets.append(
            {
                "id": asset_id,
                "title": source_name,
                "batchId": BATCH_ID,
                "batchName": BATCH_NAME,
                "sourcePath": source_name,
                "width": int(prior.get("width") or 0),
                "height": int(prior.get("height") or 0),
                "thumbnail": prior.get("thumbnail") or "",
                "originalName": original_name,
                "originalUrl": (
                    f"https://github.com/{args.repo}/releases/download/"
                    f"{quote(args.tag, safe='')}/{quote(original_name)}"
                ),
                "archiveName": prior.get("archiveName") or "待上传 ZIP",
                "archiveUrl": prior.get("archiveUrl") or release_url,
                "releaseTag": args.tag,
                "status": status,
            }
        )

    ready_count = sum(item["status"] == "ready" for item in assets)
    batch = {
        "id": BATCH_ID,
        "name": BATCH_NAME,
        "count": args.count,
        "readyCount": ready_count,
        "archiveName": "一个或多个 ZIP（后续上传）",
        "archiveUrl": release_url,
        "releaseTag": args.tag,
        "status": "ready" if ready_count == args.count else "indexing",
    }

    catalog["repositoryUrl"] = f"https://github.com/{args.repo}"
    catalog["batches"] = [item for item in catalog.get("batches", []) if item.get("id") != BATCH_ID] + [batch]
    catalog["assets"] = [item for item in catalog.get("assets", []) if item.get("batchId") != BATCH_ID] + assets
    catalog["generatedAt"] = datetime.now(timezone.utc).isoformat()
    args.catalog.parent.mkdir(parents=True, exist_ok=True)
    args.catalog.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Pre-registered {len(assets)} fixed photo URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
