#!/usr/bin/env python3
"""
Fetch high-quality coloring pages for VBS 2026 Deliverance project.

Usage:
    python3 fetch_coloring_pages.py

Downloads full-resolution coloring page images from public domain sources
(Sweet Publishing via SuperColoring.com) into assets/coloring/.
These are embedded directly as images in the PDF output.
"""

import os
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
COLORING_DIR = BASE_DIR / "assets" / "coloring"
COLORING_DIR.mkdir(parents=True, exist_ok=True)

# Map of output filename (no extension) -> full-resolution source URL
# Public domain artwork from Sweet Publishing via SuperColoring.com
COLORING_SOURCES = {
    "moses_staff":       "https://cdn.supercoloring.com/coloring/491615/41-god-gave-the-staff-to-moses-coloring-page.png",
    "nile_blood":        "https://cdn.supercoloring.com/coloring/340498/49-plague-of-blood-coloring-page.jpg",
    "red_sea_parting":   "https://cdn.supercoloring.com/coloring/491612/24-moses-parts-the-red-sea-coloring-page.png",
    "moses_pharaoh":     "https://cdn.supercoloring.com/coloring/340497/50-moses-and-aaron-appear-before-pharaoh-coloring-page.jpg",
    "hail_egypt":        "https://cdn.supercoloring.com/coloring/340503/44-plague-of-hail-coloring-page.jpg",
    "red_sea_crossing":  "https://cdn.supercoloring.com/coloring/340511/38-israelites-crossing-the-red-sea-coloring-page.jpg",
    "doorpost":          "https://cdn.supercoloring.com/coloring/2687450/06-02exodus-12-1-13-passover-coloring-page.png",
    "passover_meal":     "https://cdn.supercoloring.com/coloring/2687449/07-02exodus-12-1-13-passover-coloring-page.png",
    "slave_work":        "https://cdn.supercoloring.com/coloring/2687221/25-07exodus-1-8-22-slavery-in-egypt-coloring-page.png",
    "plague_bugs":       "https://cdn.supercoloring.com/coloring/340499/48-plague-of-frogs-coloring-page.jpg",
}


def download_image(url, dest_path):
    """Download an image from URL to local path."""
    if dest_path.exists():
        print(f"  [cached] {dest_path.name}")
        return True

    print(f"  Downloading {url[:80]}...")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            dest_path.write_bytes(data)
        print(f"  [ok] {len(data)} bytes -> {dest_path.name}")
        return True
    except Exception as e:
        print(f"  [error] {e}")
        return False


def main():
    print("=" * 60)
    print("VBS 2026 Coloring Page Downloader")
    print("=" * 60)

    for name, url in COLORING_SOURCES.items():
        ext = url.rsplit(".", 1)[-1].split("?")[0][:4]
        dest = COLORING_DIR / f"{name}.{ext}"
        print(f"\n[{name}]")
        download_image(url, dest)

    print("\n" + "=" * 60)
    print("Done! Run 'python3 generate.py' to regenerate PDFs.")


if __name__ == "__main__":
    main()
