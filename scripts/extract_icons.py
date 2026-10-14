#!/usr/bin/env python3
"""
Простой скрипт для извлечения лаунчер-иконки из APK.

Usage:
    python3 scripts/extract_icons.py apks --out-dir icons
    python3 scripts/extract_icons.py path/to/app.apk --out-dir icons --name myapp

Requirements:
    pip install pillow
"""

import argparse
import io
import os
import zipfile
from typing import List, Tuple

from PIL import Image

ICON_HINTS = (
    "mipmap",
    "drawable",
    "ic_launcher",
    "launcher",
)

def iter_apk_files(apk_path: str) -> List[str]:
    if os.path.isdir(apk_path):
        files = []
        for entry in sorted(os.listdir(apk_path)):
            full = os.path.join(apk_path, entry)
            if os.path.isfile(full) and full.lower().endswith(".apk"):
                files.append(full)
        return files
    return [apk_path]

def find_icon_candidates(apk_zip: zipfile.ZipFile) -> List[Tuple[int, str, bytes]]:
    results: List[Tuple[int, str, bytes]] = []

    for info in apk_zip.infolist():
        name = info.filename.lower()
        if not (name.endswith((".png", ".webp")) and any(hint in name for hint in ICON_HINTS)):
            continue

        try:
            payload = apk_zip.read(info.filename)
            with Image.open(io.BytesIO(payload)) as img:
                img.load()
                width, height = img.size
                area = width * height
                results.append((area, info.filename, payload))
        except Exception:
            continue

    results.sort(key=lambda item: item[0], reverse=True)
    return results

def save_icon(data: bytes, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with Image.open(io.BytesIO(data)) as img:
        rgba = img.convert("RGBA")
        rgba.save(output_path, format="PNG")

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract launcher icon from one or more APK files")
    parser.add_argument("apk", help="Path to a .apk file or a directory containing .apk files")
    parser.add_argument("--out-dir", default="icons", help="Directory to save extracted icons")
    parser.add_argument("--name", default=None, help="Custom output name (without extension)")
    args = parser.parse_args()

    for apk_file in iter_apk_files(args.apk):
        if not os.path.isfile(apk_file):
            print(f"[WARN] Missing file: {apk_file}")
            continue

        try:
            with zipfile.ZipFile(apk_file, "r") as apk_zip:
                candidates = find_icon_candidates(apk_zip)
                if not candidates:
                    print(f"[WARN] No icon found in {apk_file}")
                    continue

                _, source_name, payload = candidates[0]
                base_name = args.name or os.path.splitext(os.path.basename(apk_file))[0]
                output_path = os.path.join(args.out_dir, f"{base_name}.png")
                save_icon(payload, output_path)
                print(f"[OK] {apk_file} -> {output_path} (source: {source_name})")
        except Exception as exc:
            print(f"[ERROR] {apk_file}: {exc}")

if __name__ == "__main__":
    main()
