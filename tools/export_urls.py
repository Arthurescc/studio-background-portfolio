#!/usr/bin/env python3
"""Export the gallery catalog as a formatted Excel workbook and UTF-8 CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import xlsxwriter


HEADERS = [
    "No.",
    "File name",
    "Original image URL",
    "Batch",
    "Batch ZIP URL",
    "Width (px)",
    "Height (px)",
    "Release tag",
    "Source path in ZIP",
]


def asset_rows(catalog: dict) -> list[list[object]]:
    return [
        [
            index,
            asset.get("title") or asset.get("originalName") or "",
            asset.get("originalUrl") or "",
            asset.get("batchName") or "",
            asset.get("archiveUrl") or "",
            int(asset.get("width") or 0),
            int(asset.get("height") or 0),
            asset.get("releaseTag") or "",
            asset.get("sourcePath") or "",
        ]
        for index, asset in enumerate(catalog.get("assets", []), start=1)
    ]


def write_csv(path: Path, rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        writer.writerows(rows)


def write_xlsx(path: Path, catalog: dict, rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = xlsxwriter.Workbook(path, {"constant_memory": True})
    workbook.set_properties(
        {
            "title": "Studio Background Library Photo URL Index",
            "subject": "Direct download URLs for every public background image",
            "author": "Studio Background Library",
            "company": "Arthurescc",
        }
    )
    sheet = workbook.add_worksheet("Photo URLs")
    sheet.hide_gridlines(2)
    sheet.freeze_panes(7, 0)

    title = workbook.add_format(
        {"bold": True, "font_size": 18, "font_color": "#D7FF45", "bg_color": "#131313", "valign": "vcenter"}
    )
    subtitle = workbook.add_format(
        {"italic": True, "font_size": 10, "font_color": "#6F6B64", "bg_color": "#F3F0E9", "valign": "vcenter"}
    )
    summary_label = workbook.add_format({"bold": True, "bg_color": "#D7FF45", "font_color": "#131313"})
    summary_value = workbook.add_format({"bold": True, "bg_color": "#FFFDF8", "align": "right", "num_format": "#,##0"})
    header = workbook.add_format(
        {"bold": True, "font_color": "#FFFFFF", "bg_color": "#131313", "valign": "vcenter", "text_wrap": True}
    )
    text = workbook.add_format({"font_color": "#242424", "valign": "vcenter"})
    integer = workbook.add_format({"font_color": "#242424", "num_format": "#,##0", "align": "right", "valign": "vcenter"})
    hyperlink = workbook.add_format({"font_color": "#0563C1", "underline": True, "valign": "vcenter"})

    sheet.merge_range("A1:I1", "Studio Background Library · Photo URL Index", title)
    sheet.merge_range(
        "A2:I2",
        "One row per image: direct original URL, batch ZIP URL, dimensions, release tag and source path.",
        subtitle,
    )
    sheet.write("A4", "Total photos", summary_label)
    sheet.write_number("B4", len(rows), summary_value)
    sheet.write("A5", "Batches", summary_label)
    sheet.write_number("B5", len(catalog.get("batches", [])), summary_value)
    sheet.write_row("A7", HEADERS, header)
    sheet.set_row(0, 34)
    sheet.set_row(1, 24)
    sheet.set_row(6, 30)

    for row_index, row in enumerate(rows, start=7):
        sheet.write_number(row_index, 0, row[0], integer)
        sheet.write(row_index, 1, row[1], text)
        if row[2]:
            sheet.write_url(row_index, 2, row[2], hyperlink, row[2])
        else:
            sheet.write_blank(row_index, 2, None, text)
        sheet.write(row_index, 3, row[3], text)
        if row[4]:
            sheet.write_url(row_index, 4, row[4], hyperlink, row[4])
        else:
            sheet.write_blank(row_index, 4, None, text)
        sheet.write_number(row_index, 5, row[5], integer)
        sheet.write_number(row_index, 6, row[6], integer)
        sheet.write(row_index, 7, row[7], text)
        sheet.write(row_index, 8, row[8], text)

    if rows:
        last_row = 6 + len(rows)
        sheet.autofilter(6, 0, last_row, len(HEADERS) - 1)

    widths = [9, 32, 62, 26, 62, 13, 13, 22, 42]
    for column, width in enumerate(widths):
        sheet.set_column(column, column, width)

    workbook.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--xlsx", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    rows = asset_rows(catalog)
    write_xlsx(args.xlsx, catalog, rows)
    write_csv(args.csv, rows)
    print(f"Exported {len(rows)} photo URL rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

