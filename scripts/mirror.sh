#!/usr/bin/env bash
# Mirrors the live Wix site into ../mirror as a content archive.
# Wix serves media from separate CDN hosts (static.wixstatic.com etc.), so
# --span-hosts + --domains is needed to pull those alongside the HTML pages.
set -euo pipefail

cd "$(dirname "$0")/.."

wget --mirror \
  --convert-links \
  --adjust-extension \
  --page-requisites \
  --no-parent \
  --span-hosts \
  --domains=nataliatixo.wixsite.com,static.wixstatic.com,video.wixstatic.com,music.wixstatic.com,staticorigin.wixstatic.com \
  --directory-prefix=mirror \
  https://nataliatixo.wixsite.com/nataliatixoeng
