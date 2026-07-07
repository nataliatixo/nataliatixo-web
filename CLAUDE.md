# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Wix-to-GitHub-Pages migration for https://nataliatixo.wixsite.com/nataliatixoeng, rebuilt as a Hugo static site. Wix has no export function, so the migration was: mirror the live site with `wget` for content/assets, extract that into Hugo content bundles with a Python script, then deploy via GitHub Pages.

## Current state

Content has been mirrored (`mirror/`, gitignored) and extracted into a working Hugo site (`content/`, `layouts/`, `hugo.toml`), with a minimalistic greyscale/light-grey style pass and full EN/RU blog parity (see below). `hugo server -D` builds cleanly. Not yet done: uploading the 5 Wix videos somewhere external and filling in their embed URLs, and switching the repo's GitHub Pages source to "GitHub Actions" plus pointing DNS at `nataliatixo.com` — the latter two require explicit go-ahead since they touch shared/external systems, so ask before doing them. See README.md's status checklist for the up-to-date picture.

**Important:** `content/` now contains hand-authored files that don't exist in the mirror (translations, `translationKey` links — see below). Never `rm -rf content` before re-running `extract_content.py`; the script only overwrites files it actually generates from mirrored HTML, so re-running it in place is safe, but wiping the directory first would destroy that hand-authored content.

## Stack

Hugo (no npm, no third-party theme — hand-written minimal layouts). Local Hugo binary lives at `~/.local/bin/hugo` (installed by downloading the extended release directly, not via apt, since apt required sudo). `hugo.toml` needs `[markup.goldmark.renderer] unsafe = true` because content bodies are raw HTML (see below), not Markdown syntax.

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
- Text is cleaned into plain semantic HTML (`p`/`h1-h6`/`a`/`strong`/`em`/`br` only, everything else unwrapped) — Wix's inline styles and wrapper divs are stripped, not preserved.
- Internal links get rewritten from old Wix URLs to new Hugo paths via a slug map built from the manifest (`SLUG_TO_URL` in the script); external links pass through unchanged.
- Images: Wix stores originals as resized variants only (`static.wixstatic.com/media/<id>/v1/fill|fit/w_NNN,.../<id>`, no true full-res original in the static mirror) — the script picks the largest available width per unique media ID and copies it into the page bundle, deduping so the same image isn't copied/emitted twice even if it appears as both a body image and a gallery thumbnail.
- Blog post dates come from the first `data-hook="time-ago"` element on the page; categories/tags are cross-referenced from the `blog-1/categories/*` and `blog-1/hashtags/*` listing pages (built once into a slug → categories/tags map).
- Videos: Wix embeds them as `<video src>` inside `data-hook="video-player"`. Since the decision was to host video externally (not in git/Pages), the script emits a `{{< video note="source: ..." >}}` shortcode placeholder instead of a file — see `layouts/shortcodes/video.html`. Once a video is uploaded (YouTube/Vimeo), replace the shortcode with `{{< video src="https://...embed-url..." >}}` in the affected post(s).

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

## Working here

- `mirror/` is a **content archive only** — raw Wix output full of framework JS and tracking scripts. Never reference it from the live site; it only feeds `extract_content.py`.
- `public/`, `resources/`, `.hugo_build.lock` are gitignored build artifacts — don't hand-edit anything there, it's regenerated by `hugo`.
- Deploy is `.github/workflows/deploy.yml` (push to `main` → Hugo build → GitHub Pages). Enabling it live (Pages source setting, DNS) is an explicit follow-up, not done automatically.
- Anything dynamic on the original Wix site (contact forms, bookings) has no static equivalent and was dropped during extraction — replace with Formspree/mailto if needed.
