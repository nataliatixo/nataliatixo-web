#!/usr/bin/env python3
"""Re-fetch full-resolution originals from the Wix CDN for content images the
mirror only captured as small resized variants.

Wix pages reference resized variants (w_147 thumbnails etc.), so the mirror
often lacks the real upload — but the bare https://static.wixstatic.com/media/<id>
URL serves the original. This scans content/ for images narrower than
--min-width, maps each filename back to its Wix media id via the mirror's
media directories, fetches the original, and replaces the bundle file in
place only when the fetched image is strictly wider.

Idempotent; safe to re-run. Only works while the Wix site/CDN is still up,
and needs the mirror/ directory for the filename -> media-id mapping.
Requires ImageMagick's `identify` on PATH. Run before cancelling Wix.

Usage: python3 scripts/refetch_originals.py [--min-width 800]
"""
import argparse
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
MIRROR = REPO / "mirror"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def clean(name: str) -> str:
    """Mirror of resolve_media()'s filename cleaning in extract_content.py."""
    return re.sub(r"[^A-Za-z0-9._-]", "", name.replace("~mv2", ""))


def width_of(path: Path) -> int:
    out = subprocess.run(["identify", "-format", "%w", str(path)],
                         capture_output=True, text=True)
    return int(out.stdout) if out.returncode == 0 and out.stdout.strip().isdigit() else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-width", type=int, default=800,
                    help="try to upgrade images narrower than this (px)")
    args = ap.parse_args()

    id_map = {}
    for media_dir in MIRROR.glob("*/media"):
        for entry in media_dir.iterdir():
            id_map.setdefault(clean(entry.name), entry.name)
    if not id_map:
        raise SystemExit("no mirror media dirs found — mirror/ is required for the id mapping")

    replaced = kept = missing = 0
    with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as f:
        tmp = Path(f.name)
    try:
        for path in sorted(CONTENT.rglob("*")):
            if path.suffix.lower() not in IMAGE_EXTS or not path.is_file():
                continue
            old_w = width_of(path)
            if not old_w or old_w >= args.min_width:
                continue
            media_id = id_map.get(path.name)
            if not media_id:
                print(f"SKIP (no mirror id): {path.relative_to(REPO)}")
                missing += 1
                continue
            url = f"https://static.wixstatic.com/media/{media_id}"
            r = subprocess.run(["curl", "-sf", "-o", str(tmp), url])
            new_w = width_of(tmp)
            if r.returncode == 0 and new_w > old_w:
                shutil.move(tmp, path)
                print(f"OK   {path.relative_to(REPO)}: {old_w} -> {new_w}px")
                replaced += 1
            else:
                kept += 1  # original really is that small (or fetch failed)
            time.sleep(0.5)
    finally:
        tmp.unlink(missing_ok=True)

    print(f"\n{replaced} replaced, {kept} already at original size, {missing} unmapped")


if __name__ == "__main__":
    main()
