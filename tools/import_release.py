#!/usr/bin/env python3
"""Build a safe, lightweight gallery catalog from ZIP files attached to a release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from PIL import Image, ImageOps, UnidentifiedImageError


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGES_PER_ARCHIVE = 20_000
MAX_MEMBER_BYTES = 300 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 80 * 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 300


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-._").lower()
    return value[:100] or "batch"


def friendly_name(value: str) -> str:
    name = Path(value).stem
    name = re.sub(r"[_-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip() or "Untitled background"


def safe_image_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members: list[zipfile.ZipInfo] = []
    total_size = 0
    for info in archive.infolist():
        path = PurePosixPath(info.filename)
        if info.is_dir() or path.is_absolute() or ".." in path.parts:
            continue
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        if info.file_size > MAX_MEMBER_BYTES:
            raise ValueError(f"Oversized image rejected: {info.filename}")
        if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
            raise ValueError(f"Suspicious compression ratio: {info.filename}")
        total_size += info.file_size
        if total_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
            raise ValueError("Archive expands beyond the configured safety limit")
        members.append(info)
        if len(members) > MAX_IMAGES_PER_ARCHIVE:
            raise ValueError("Archive contains too many images")
    return members


def load_catalog(path: Path, repository_url: str) -> dict:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data.setdefault("assets", [])
            data.setdefault("batches", [])
            data["repositoryUrl"] = repository_url
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"repositoryUrl": repository_url, "generatedAt": None, "batches": [], "assets": []}


def process_archive(
    zip_path: Path,
    tag: str,
    repo: str,
    docs_dir: Path,
    originals_dir: Path,
) -> tuple[dict, list[dict]]:
    batch_id = slugify(f"{tag}-{zip_path.stem}")
    batch_name = friendly_name(zip_path.stem)
    thumb_dir = docs_dir / "thumbnails" / batch_id
    if thumb_dir.exists():
        shutil.rmtree(thumb_dir)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    asset_url = f"https://github.com/{repo}/releases/download/{quote(tag, safe='')}/{quote(zip_path.name)}"
    assets: list[dict] = []

    with zipfile.ZipFile(zip_path) as archive:
        members = safe_image_members(archive)
        for index, info in enumerate(members, start=1):
            digest = hashlib.sha1(info.filename.encode("utf-8", "surrogatepass")).hexdigest()[:14]
            thumb_name = f"{index:05d}-{digest}.webp"
            thumb_path = thumb_dir / thumb_name
            original_name = f"{batch_id}--{index:05d}-{digest}{PurePosixPath(info.filename).suffix.lower()}"
            original_path = originals_dir / original_name
            try:
                with archive.open(info) as source, original_path.open("wb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)
                with Image.open(original_path) as raw:
                    image = ImageOps.exif_transpose(raw)
                    width, height = image.size
                    if width < 2 or height < 2:
                        continue
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
                print(f"Skipping unreadable image {info.filename}: {error}", file=sys.stderr)
                continue

            original_url = f"https://github.com/{repo}/releases/download/{quote(tag, safe='')}/{quote(original_name)}"

            assets.append(
                {
                    "id": f"{batch_id}-{digest}",
                    "title": friendly_name(info.filename),
                    "batchId": batch_id,
                    "batchName": batch_name,
                    "sourcePath": info.filename,
                    "width": width,
                    "height": height,
                    "thumbnail": f"./thumbnails/{batch_id}/{thumb_name}",
                    "originalName": original_name,
                    "originalUrl": original_url,
                    "archiveName": zip_path.name,
                    "archiveUrl": asset_url,
                    "releaseTag": tag,
                    "status": "ready",
                }
            )

    batch = {
        "id": batch_id,
        "name": batch_name,
        "count": len(assets),
        "archiveName": zip_path.name,
        "archiveUrl": asset_url,
        "releaseTag": tag,
        "status": "ready",
    }
    return batch, assets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--docs-dir", default="docs", type=Path)
    parser.add_argument("--originals-dir", required=True, type=Path)
    args = parser.parse_args()

    archives = sorted(args.input_dir.glob("*.zip"))
    if not archives:
        print("No ZIP files found", file=sys.stderr)
        return 2

    catalog_path = args.docs_dir / "data" / "catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    repository_url = f"https://github.com/{args.repo}"
    catalog = load_catalog(catalog_path, repository_url)
    args.originals_dir.mkdir(parents=True, exist_ok=True)

    new_batches: list[dict] = []
    new_assets: list[dict] = []
    replaced_ids: set[str] = set()
    for archive in archives:
        batch, assets = process_archive(
            archive,
            args.tag,
            args.repo,
            args.docs_dir,
            args.originals_dir,
        )
        new_batches.append(batch)
        new_assets.extend(assets)
        replaced_ids.add(batch["id"])

    catalog["batches"] = [b for b in catalog["batches"] if b.get("id") not in replaced_ids] + new_batches
    catalog["assets"] = [a for a in catalog["assets"] if a.get("batchId") not in replaced_ids] + new_assets
    catalog["batches"].sort(key=lambda b: (b.get("releaseTag", ""), b.get("name", "")), reverse=True)
    catalog["assets"].sort(key=lambda a: (a.get("releaseTag", ""), a.get("batchName", ""), a.get("title", "")), reverse=True)
    catalog["generatedAt"] = datetime.now(timezone.utc).isoformat()
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(new_assets)} images from {len(archives)} archive(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
