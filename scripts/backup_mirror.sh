#!/usr/bin/env bash
# Archive mirror/ — the only offline copy of the original Wix site — into a
# single verifiable tarball. Run this BEFORE cancelling the Wix subscription,
# then copy the tarball somewhere durable (external drive, cloud storage).
#
# Usage: ./scripts/backup_mirror.sh [output-dir]   (default: repo parent dir)
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
MIRROR="$REPO/mirror"
OUT_DIR="${1:-$(dirname "$REPO")}"
STAMP="$(date +%Y%m%d)"
ARCHIVE="$OUT_DIR/nataliatixo-wix-mirror-$STAMP.tar.gz"

if [ ! -d "$MIRROR" ]; then
  echo "error: $MIRROR does not exist — nothing to back up" >&2
  exit 1
fi

echo "Archiving mirror/ ($(du -sh "$MIRROR" | cut -f1)) to $ARCHIVE ..."
tar -czf "$ARCHIVE" -C "$REPO" mirror
# Checksum by basename so `sha256sum -c` works wherever the pair ends up.
(cd "$OUT_DIR" && sha256sum "$(basename "$ARCHIVE")" > "$(basename "$ARCHIVE").sha256")

echo
echo "Done:"
du -h "$ARCHIVE" "$ARCHIVE.sha256"
echo
echo "Verify a copy later with:  sha256sum -c $(basename "$ARCHIVE").sha256"
echo "Now move both files somewhere durable (external drive / cloud storage)."
