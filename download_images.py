#!/usr/bin/env python3
"""Download all images referenced on a Wiktenauer wiki page into ./images.

Usage:
    python download_images.py [PAGE_URL] [OUTPUT_DIR]

Defaults to the Paulus Hector Mair page and ./images.
"""
import os
import re
import sys
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

DEFAULT_URL = "https://wiktenauer.com/wiki/Paulus_Hector_Mair"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; image-downloader/1.0)"}


def to_full_resolution(src: str) -> str:
    """Convert a MediaWiki thumbnail URL into its full-resolution original."""
    match = re.match(r"^(.*/images)/thumb/(.+)/[0-9]+px-[^/]+$", src)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return src


def download_all_images(page_url: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    resp = requests.get(page_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    seen = set()
    downloaded = 0

    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue

        full_url = urljoin(page_url, to_full_resolution(src))
        if full_url in seen:
            continue
        seen.add(full_url)

        filename = unquote(os.path.basename(urlparse(full_url).path))
        if not filename:
            continue
        out_path = os.path.join(output_dir, filename)

        if os.path.exists(out_path):
            print(f"skip (exists): {filename}")
            continue

        try:
            img_resp = requests.get(full_url, headers=HEADERS, timeout=30)
            img_resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"failed: {full_url} ({exc})")
            continue

        with open(out_path, "wb") as f:
            f.write(img_resp.content)

        downloaded += 1
        print(f"downloaded: {filename}")

    print(f"\nDone. {downloaded} new image(s) saved to {output_dir}/")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "images"
    download_all_images(url, out_dir)
