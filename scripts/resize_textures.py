"""
Downscale the NASA Blue Marble monthly textures so they fit in the GitHub repo.

Usage:
    1. Put the original images in textures/original/  (january.jpg ... december.jpg)
    2. pip install Pillow
    3. python scripts/resize_textures.py

The resized copies are written to textures/ (the folder the app loads from).
textures/original/ is git-ignored, so the full-size files never get committed.
"""
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # Blue Marble 16K images exceed Pillow's default safety limit

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "textures" / "original"
DST = ROOT / "textures"
TARGET_WIDTH = 5400
JPEG_QUALITY = 85

MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Folder not found: {SRC}")

    for month in MONTHS:
        matches = [p for p in SRC.iterdir() if p.stem.lower() == month]
        if not matches:
            print(f"  missing: {month}")
            continue

        with Image.open(matches[0]) as img:
            img = img.convert("RGB")
            ratio = TARGET_WIDTH / img.width
            resized = img.resize((TARGET_WIDTH, round(img.height * ratio)), Image.LANCZOS)
            out = DST / f"{month}.jpg"
            resized.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
            print(f"  {month}: {out.stat().st_size / 1_000_000:.1f} MB")


if __name__ == "__main__":
    main()
