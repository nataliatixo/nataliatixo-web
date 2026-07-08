# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Wix-to-GitHub-Pages migration for https://nataliatixo.wixsite.com/nataliatixoeng, rebuilt as a Hugo static site. Wix has no export function, so the migration was: mirror the live site with `wget` for content/assets, extract that into Hugo content bundles with a Python script, then deploy via GitHub Pages.

## Current state

Content has been mirrored (`mirror/`, gitignored) and extracted into a working Hugo site (`content/`, `layouts/`, `hugo.toml`), with a minimalistic greyscale/light-grey style pass and full EN/RU blog parity (see below). `hugo server -D` builds cleanly, and the site is deployed via GitHub Actions to the temporary project URL https://nataliatixo.github.io/nataliatixo-web/. Not yet done: uploading the 2 big Wix lecture videos (~650–700 MB each, see README's table) somewhere external and filling in their embed URLs — the other 3 videos were small enough to self-host in their page bundles (`{{< video file="video.mp4" >}}`), and pointing the custom domain `nataliatixo.com` (Pages settings + DNS + switching `baseURL` back, see `hugo.toml`) — the domain switch requires explicit go-ahead since it touches shared/external systems, so ask before doing it. See README.md's status checklist for the up-to-date picture.

**Important:** `content/` now contains hand-authored files that don't exist in the mirror (translations, `translationKey` links — see below) **and** images upgraded to full-res originals fetched from the Wix CDN (`scripts/refetch_originals.py` — the mirror only had small resized variants for ~80 of them). Never `rm -rf content` before re-running `extract_content.py`; the script only overwrites `.md` files it actually generates from mirrored HTML and never overwrites an image that already exists in a bundle, so re-running it in place is safe, but wiping the directory first would destroy the hand-authored content and re-copy the low-res mirror variants over the recovered originals.

## Stack

Hugo (no npm, no third-party theme — hand-written minimal layouts). Local Hugo binary lives at `~/.local/bin/hugo` (installed by downloading the extended release directly, not via apt, since apt required sudo). `hugo.toml` needs `[markup.goldmark.renderer] unsafe = true` because content bodies are raw HTML (see below), not Markdown syntax.

Body images go through `layouts/shortcodes/img.html` (`{{< img src="..." alt="..." >}}`): Hugo's image pipeline emits WebP capped at 1400px with a 700px srcset variant, `width`/`height` attributes, and lazy loading; animated GIFs and srcs that aren't bundle resources pass through untouched. List thumbnails come from `layouts/partials/child-li.html` (400×400 WebP `.Fill`). Processed derivatives land in `resources/_gen` (gitignored; CI caches it via `actions/cache` keyed on `content/**`).

**`relURL`/`relLangURL` gotcha:** input with a leading slash is treated as already server-root-relative and does *not* get the baseURL subpath prefix (`{{ "/" | relLangURL }}` → `/`, a broken link while the site lives under `/nataliatixo-web/`). Always pass prefix-less inputs (`"categories/" | relLangURL`) or use `.Site.Home.RelPermalink`; `layouts/partials/content.html` derives the body-link prefix from `site.BaseURL` for the same reason.

### Bilingual (EN default / RU)

Single `content/` dir shared by both languages (`contentDir` the same for both in `hugo.toml`); English is the unsuffixed file (`index.md`), Russian is `.ru.md`. The ~74 project/bio pages are full EN↔RU pairs from the original mirror. Blog posts were originally single-language on Wix (29 Russian-only, 7 English-only) — full EN/RU parity across all 33 posts was added by hand-translating the missing side (Claude-translated; not proofread by a native speaker, flag this if precision matters for a specific post, especially the experimental/wordplay poems noted inline via translator's-note `<em>` blocks). One pair — `essay-the-case-at-the-border` / `эссе-случай-на-границе` — is the author's own independently-written bilingual pair under two different slugs, linked via a shared `translationKey` front-matter value (see `TRANSLATION_PAIRS` in `extract_content.py`) rather than machine-translated, since a native version already existed.

Language switching is entirely client-side (`layouts/partials/lang-redirect.html` + the toggle script at the bottom of `layouts/partials/footer.html`): first visit checks `navigator.language`, redirects to the Russian translation only if one exists for that exact page (via Hugo's `.Translations`), and remembers the choice in `localStorage['lang-pref']` so it never fights a manual toggle. The toggle itself (in `layouts/partials/header.html`) falls back to the other language's homepage when the current page has no translation.

### Content structure

Four sections (nav: About · Projects · Texts · Archive), organized by what content *is*, not by which Wix app it lived in. Wix's "blog" was really four kinds of content, so its posts were redistributed:

- `content/_index.md` (+ `.ru.md`) — **About**: home page, bio + CV (from the site's `nataliatixoeng.html` root page)
- `content/projects/` — **Projects**: the 26 artistic-object pages + 5 curatorial pages merged flat into one section; each page carries `group: artistic|curatorial` front matter, and `layouts/projects/list.html` renders the two groups under separate headings
- `content/texts/` — **Texts**: writing *by* the author, from the old blog: ~12 poetry/prose bundles (`group: poetry`) + 5 essays/published texts (`group: essays`); `layouts/texts/list.html` groups them
- `content/archive/` — **Archive**: the dated activity log (talks, lectures, conferences, mediations, announcements) plus `random-pictures`; `layouts/archive/list.html` renders one chronological list
- `content/press/` — **Press** (not in the nav): the 4 interviews *about* her; `layouts/index.html` surfaces them as a "Press" list at the bottom of the About page, since press belongs with the bio rather than the activity log

Section membership lives in the extraction script's manifest lists (`ARTISTIC_OBJECTS`/`CURATORIAL`/`TEXTS_POETRY`/`TEXTS_ESSAYS`/`ARCHIVE_POSTS`/`PRESS` in `extract_content.py`) — to move a page between sections, move its slug between lists *and* `git mv` its content bundle. Categories/tags from Wix (`blog-1/categories/*`, `blog-1/hashtags/*`) are still extracted as taxonomy front matter but the `group` param is what drives the section listings.

Each leaf page is a **page bundle** (`index.md` + copied images alongside), not a flat `.md` file, so images stay colocated with their content. Nav menus are defined per-language in `hugo.toml` (`[languages.en.menus]` / `[languages.ru.menus]`) so RU pages get Russian labels.

### Content extraction (`scripts/extract_content.py`)

Run with a venv that has `beautifulsoup4` + `lxml` (not system Python — Debian blocks plain `pip install`). Re-run after re-mirroring; it overwrites `content/`.

What it does, per mirrored HTML page:
- Title from the `<title>` tag (strips the ` | nataliatixo` suffix, capitalizes if all-lowercase).
- Body: for portfolio-style pages, walks `#SITE_PAGES` collecting `data-testid="richTextElement"` (text) and `<img>` (images) in document order. For blog posts (Wix Blog app), walks `data-hook="post-description"` collecting `<p>`/`<img>`.
- Text is cleaned into plain semantic HTML (`p`/headings/`a`/`strong`/`em`/`br` only, everything else unwrapped) — Wix's inline styles and wrapper divs are stripped, not preserved. Wix's `<h1>` (used for big statement/credit text) is demoted to `<p class="lede">` and `<h6>` (captions) to `<p class="caption">`, so the template's page title stays the only `h1` on a page.
- Internal links get rewritten from old Wix URLs to new Hugo paths via a slug map built from the manifest (`SLUG_TO_URL` in the script); external links pass through unchanged.
- Images: Wix pages reference resized variants only (`static.wixstatic.com/media/<id>/v1/fill|fit/w_NNN,.../<id>`), so the mirror has no true full-res originals — the script picks the largest available width per unique media ID and copies it into the page bundle (never overwriting an existing file, which protects the refetched originals), deduping so the same image isn't copied/emitted twice even if it appears as both a body image and a gallery thumbnail. Bodies get `{{< img >}}` shortcode calls, not raw `<img>` tags. Where the mirror's best variant was still small, `scripts/refetch_originals.py` pulled the true original from `https://static.wixstatic.com/media/<id>` (only possible while Wix is up).
- Blog post dates come from the first `data-hook="time-ago"` element on the page; categories/tags are cross-referenced from the `blog-1/categories/*` and `blog-1/hashtags/*` listing pages (built once into a slug → categories/tags map).
- Videos: Wix embeds them as `<video src>` inside `data-hook="video-player"`. Small videos (a few MB) live in the page bundle as a committed `video.mp4` served natively via `{{< video file="video.mp4" >}}` — the script detects the bundled file and emits that form, so re-runs don't revert it. Big videos (the two ~650–700 MB lecture recordings — over GitHub's 100 MB file limit) get a `{{< video note="source: ..." >}}` placeholder instead; once uploaded externally (YouTube/Vimeo), replace it with `{{< video src="https://...embed-url..." >}}`. All three forms are handled by `layouts/shortcodes/video.html`.

`--only slug1,slug2,...` limits a run to specific slugs (matches section slugs, child slugs, or post slugs) — useful for testing template/extraction changes without re-running everything.

### Known content gaps (not extraction bugs — 404 on the live Wix site itself)

Confirmed via literal "404" markers in the ~300KB mirrored HTML shells for these URLs:
- 3 old blog posts at date-prefixed URLs (`post/2018/12/06/...`, `post/2018/12/27/...`) — dropped from the `POSTS` list in the extraction script with a comment explaining why.
- The Russian translations of `kopiya-curatorial-projects`, `kopiya-procartistination-branches`, and `poeticaltexts` — the extraction script detects these automatically (no `<title>`, no body) and skips writing a blank placeholder.

If these need to be recovered, it has to be from the Wix dashboard directly (drafts/originals), not from the mirror.

## Commands

- `hugo server -D` — local dev server.
- `hugo --minify` — production build (what CI runs).
- `./scripts/mirror.sh` — re-mirror the live site into `mirror/` via `wget --mirror --span-hosts --domains=...`. The domain list includes Wix's CDN hosts (`static.wixstatic.com`, `video.wixstatic.com`, etc.) so media is captured alongside HTML, not just page markup. Safe to re-run anytime; it just overwrites the archive.
- `python3 scripts/extract_content.py [--only slug1,slug2]` — (re-)generate `content/` from the mirror. Needs a venv with `beautifulsoup4` + `lxml`.
- `python3 scripts/refetch_originals.py [--min-width 800]` — upgrade content images that are smaller than the Wix CDN's original upload (needs `mirror/` for the filename → media-id mapping, ImageMagick `identify`, and the Wix CDN still being up). Idempotent; run once more right before the Wix subscription is cancelled.
- `./scripts/backup_mirror.sh [output-dir]` — tar `mirror/` into a checksummed archive (~1.5 GB). Run before cancelling Wix and move the archive somewhere durable; `mirror/` exists only on this machine and is the sole offline copy of the originals, including the two big lecture videos.

## Working here

- `mirror/` is a **content archive only** — raw Wix output full of framework JS and tracking scripts. Never reference it from the live site; it only feeds `extract_content.py`.
- `public/`, `resources/`, `.hugo_build.lock` are gitignored build artifacts — don't hand-edit anything there, it's regenerated by `hugo`.
- Deploy is `.github/workflows/deploy.yml` (push to `main` → Hugo build → htmltest internal-link check → GitHub Pages). The link check builds under `linkcheck/<baseURL subpath>/` so root-relative links resolve exactly as on Pages — a link missing the subpath prefix fails CI; the subpath is derived from `baseURL`, so the custom-domain switch needs no workflow edit. Config in `.htmltest.yml` (external links and empty alt text are not checked). Enabling it live (Pages source setting, DNS) is an explicit follow-up, not done automatically.
- Anything dynamic on the original Wix site (contact forms, bookings) has no static equivalent and was dropped during extraction — replace with Formspree/mailto if needed.
