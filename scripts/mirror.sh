#!/usr/bin/env bash
# Mirrors the live Wix site into ../mirror as a content archive.
# Re-run this once https://nataliatixo.wixsite.com/nataliatixoeng is back up (was HTTP 500 as of 2026-07-07).
set -euo pipefail

cd "$(dirname "$0")/.."

wget --mirror \
  --convert-links \
  --adjust-extension \
  --page-requisites \
  --no-parent \
  --directory-prefix=mirror \
  https://nataliatixo.wixsite.com/nataliatixoeng
