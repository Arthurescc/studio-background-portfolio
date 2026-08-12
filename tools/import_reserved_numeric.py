#!/usr/bin/env python3
"""Match numeric JPG filenames in release ZIPs to the pre-registered URL catalog."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from PIL import Image, ImageOps, UnidentifiedImageError

from import_release import safe_image_members


BATCH_ID = "photos-1-15000"
BATCH_NAME = "1.jpg–15000.jpg 预登记"
MAX_NUMBER = 15_000
NUMERIC_JPG = re.compile(r"^([1-9][0-9]{0,4})\.jpg$", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--docs-dir", default="docs", type=Path)
    parser.add_argument("--originals-dir", required=True, type=Path)
    args = parser.parse_args()

    if args.tag != BATCH_ID:
        raise SystemExit(f"This reserved import must use release tag {BATCH_ID}")

    archives = sorted(args.input_dir.glob("*.zip"))
    if not archives:
        raise SystemExit("No ZIP files found")

    catalog_path = args.docs_dir / "data" / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assets = {item.get("id"): item for item in catalog.get("assets", []) if item.get("batchId") == BATCH_ID}
    if len(assets) != MAX_NUMBER:
        raise SystemExit("The 15,000-item reservation catalog is missing; run reserve_numeric_library.py first")

    args.originals_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir = args.docs_dir / "thumbnails" / BATCH_ID
    thumb_dir.mkdir(parents=True, exist_ok=True)
    seen: set[int] = set()
    imported = 0

    for zip_path in archives:
        archive_url = (
            f"https://github.com/{args.repo}/releases/download/"
            f"{quote(args.tag, safe='')}/{quote(zip_path.name)}"
        )
        with zipfile.ZipFile(zip_path) as archive:
            for info in safe_image_members(archive):
                basename = PurePosixPath(info.filename).name
                match = NUMERIC_JPG.fullmatch(basename)
                if not match:
                    print(f"Ignoring non-reserved filename: {info.filename}", file=sys.stderr)
                    continue
                number = int(match.group(1))
                if number > MAX_NUMBER:
                    print(f"Ignoring out-of-range filename: {info.filename}", file=sys.stderr)
                    continue
                if number in seen:
                    raise ValueError(f"Duplicate reserved filename found: {number}.jpg")
                seen.add(number)

                asset_id = f"{BATCH_ID}-{number:05d}"
                original_name = f"photo-{number:05d}.jpg"
                original_path = args.originals_dir / original_name
                thumb_name = f"{number:05d}.webp"
                thumb_path = thumb_dir / thumb_name
                try:
                    with archive.open(info) as source, original_path.open("wb") as target:
                        shutil.copyfileobj(source, target, length=1024 * 1024)
                    with Image.open(original_path) as raw:
                        image = ImageOps.exif_transpose(raw)
                        width, height = image.size
                        if width < 2 or height < 2:
                            raise ValueError("image dimensions are too small")
                        if image.mode not in {"RGB", "RGBA"}:
                            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
                        image.thumbnail((720, 540), Image.Resampling.LANCZOS)
                        if image.mode == "RGBA":
                            canvas = Image.new("RGB", image.size, "#F3F0E9")
                            canvas.paste(image, mask=image.getchannel("A"))
                            image = canvas
                        else:
                            image = image.convert("RGB")
                        image.save(thumb_path, "WEBP", quality=76, method=6)
                except (UnidentifiedImageError, OSError, ValueError) as error:
                    original_path.unlink(missing_ok=True)
                    thumb_path.unlink(missing_ok=True)
                    print(f"Skipping unreadable image {info.filename}: {error}", file=sys.stderr)
                    continue

                item = assets[asset_id]
                item.update(
                    {
                        "title": f"{number}.jpg",
                        "sourcePath": info.filename,
                        "width": width,
                        "height": height,
                        "thumbnail": f"./thumbnails/{BATCH_ID}/{thumb_name}",
                        "originalName": original_name,
                        "originalUrl": (
                            f"https://github.com/{args.repo}/releases/download/"
                            f"{quote(args.tag, safe='')}/{quote(original_name)}"
                        ),
                        "archiveName": zip_path.name,
                        "archiveUrl": archive_url,
                        "releaseTag": args.tag,
                        "status": "ready",
                    }
                )
                imported += 1

    ready_count = sum(item.get("status") == "ready" for item in assets.values())
    for batch in catalog.get("batches", []):
        if batch.get("id") == BATCH_ID:
            batch.update(
                {
                    "name": BATCH_NAME,
                    "count": MAX_NUMBER,
                    "readyCount": ready_count,
                    "archiveName": "一个或多个 ZIP",
                    "archiveUrl": f"https://github.com/{args.repo}/releases/tag/{quote(args.tag, safe='')}",
                    "releaseTag": args.tag,
                    "status": "ready" if ready_count == MAX_NUMBER else "indexing",
                }
            )

    catalog["generatedAt"] = datetime.now(timezone.utc).isoformat()
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Matched {imported} uploaded images; {ready_count}/{MAX_NUMBER} are ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
