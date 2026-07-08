# nataliatixo

Migration of https://nataliatixo.wixsite.com/nataliatixoeng off Wix onto GitHub Pages, without losing content.

Wix has no export feature, so this is a two-step migration: mirror the live site for its content/assets, then rebuild as a static site here.

## Status

- [x] Mirror the live Wix site (done 2026-07-07: 123 HTML pages + ~1.5GB media in `mirror/`)
- [x] Review mirrored content, decide structure — Hugo, bilingual EN/RU, ~74 project/bio pages + 33 blog posts
- [x] Rebuild pages here — Hugo site scaffolded, content extracted via `scripts/extract_content.py`
- [x] Restructure into 4 sections — About · Projects · Texts · Archive (Wix's "blog" was mostly archival material, so its posts were split into Texts (writing by the author) and Archive (activity log); interviews/press live at /press/ and are listed on the About page)
- [x] Style pass — minimalistic greyscale/light-grey theme (`assets/css/style.css`)
- [x] Full EN/RU blog parity — all 33 posts now exist in both languages (translated by Claude where no native version existed; see `CLAUDE.md` for which posts are original vs. translated)
- [x] Full-res image recovery (2026-07-08) — the mirror only captured resized variants for 80 images (some as 147px thumbnails); re-fetched the true originals from the Wix CDN via `scripts/refetch_originals.py`
- [x] Performance/SEO pass (2026-07-08) — body images go through an `{{< img >}}` shortcode (WebP, srcset, lazy loading, capped at 1400px); list thumbnails are 400px WebP crops (projects page went from ~10 MB to ~0.4 MB); `hreflang` alternates, Open Graph tags, canonical URLs, per-page descriptions, RSS link, favicon, 404 page; fixed internal links that were missing the `/nataliatixo-web/` subpath prefix (site title, taxonomy links, body links)
- [x] Small videos self-hosted (2026-07-08) — 3 of the 5 Wix videos were under 3 MB, so they live in their page bundles and play via a native `<video>` tag (`{{< video file="video.mp4" >}}`); no external hosting needed. The Wix CDN serves no better renditions than what the mirror captured (probed: other resolutions 403), so these are the best copies that exist.
- [ ] Big videos — the remaining 2 are ~650–700 MB lecture recordings, too big for git/Pages (100 MB file limit); waiting on you to upload them (YouTube/Vimeo) and swap each placeholder for `{{< video src="https://...embed-url..." >}}`:

  | Post | File in mirror | Size |
  |---|---|---|
  | `content/archive/практическое-занятие-для-студентов-школы-интерпретации-современного-искусства-пайдейя/` | `mirror/video.wixstatic.com/video/6253e7_180f68e5497e4588badb4dc8b65b018b/720p/mp4/file.mp4` | 698 MB |
  | `content/archive/рассказ-о-проектах-для-студентов-школы-пайдея/` | `mirror/video.wixstatic.com/video/6253e7_8edb03098c884d7e8540aedf268a3235/720p/mp4/file.mp4` | 644 MB |
- [x] Deploy to GitHub Pages — live at https://nataliatixo.github.io/nataliatixo-web/ (temporary project URL; `baseURL` in `hugo.toml` points there until the custom domain exists)
- [ ] Point custom domain `nataliatixo.com` (set the domain in repo Settings → Pages, configure DNS, switch `baseURL` back — see the comment in `hugo.toml`) and retire the Wix subscription

## Stack

Hugo, hand-written minimal layouts (no third-party theme), minimalistic greyscale design. Bilingual EN (default) / RU via Hugo's multilingual support, with a client-side script that auto-redirects Russian-language browsers on first visit and a manual toggle that persists via `localStorage`. See `CLAUDE.md` for the full content structure and extraction pipeline.

## Local development

```bash
hugo server -D
```

## Migration plan

1. **Extract**: `scripts/mirror.sh` runs `wget --mirror` against the live site into `mirror/` (gitignored — it's a scratch archive, not the deployable site), including Wix's CDN hosts so media downloads alongside HTML. Also manually export anything only in the Wix dashboard: blog drafts, form submissions, full-res media library originals (the mirror only captures web-resolution images, not true originals).
2. **Rebuild**: `scripts/extract_content.py` (Python, BeautifulSoup) parses the mirror and writes Hugo content bundles under `content/`. Re-run it if the mirror is refreshed; it overwrites existing content files.
3. **Deploy**: push to `main` — `.github/workflows/deploy.yml` builds with Hugo and deploys via GitHub Actions. Done: live at the temporary project URL above.
4. **Domain**: set `nataliatixo.com` in repo Settings → Pages, point DNS (A records to GitHub's Pages IPs, CNAME record for `www`), enable HTTPS enforcement, and switch `baseURL` in `hugo.toml` back to `https://nataliatixo.com/`. (`static/CNAME` is just a record of the intended domain — Actions-based deploys ignore that file.)
5. Only cancel the Wix subscription after everything is verified live. **Before cancelling**: (a) re-run `python3 scripts/refetch_originals.py` once more — it pulls full-res originals from the Wix CDN and stops working when Wix goes away; (b) copy `mirror/` (1.5 GB, gitignored, exists only on this machine) somewhere durable — it is the only offline backup of the Wix originals.

Note: anything dynamic on the Wix site (contact forms, bookings, member areas) has no static equivalent — forms can move to Formspree/mailto; anything more interactive needs a third-party service or gets dropped.

## Adding new content (post-migration)

Once the migration settles, the mirror/extraction pipeline is legacy — new content is hand-authored. Each page is a bundle: a directory with `index.md` (+ `index.ru.md` for the Russian version) and its images alongside.

```
content/projects/my-new-work/
├── index.md        # EN
├── index.ru.md     # RU
└── photo1.jpg
```

Front matter: `title`, plus `group: artistic|curatorial` under `projects/` or `group: poetry|essays` under `texts/`; archive posts take a `date`. The migrated bodies are raw HTML paragraphs (`<p>`, `<p class="lede">` for big statement text, `<p class="caption">` for captions), but new pages can be written in plain Markdown — both render fine, so don't feel obliged to write HTML. Images use the shortcode — it handles WebP conversion, responsive sizes, and lazy loading:

```
{{< img src="photo1.jpg" alt="description of the work" >}}
```

Small videos (a few MB) can live in the bundle: `{{< video file="video.mp4" >}}` serves them with a native player. Anything big goes external — upload to YouTube/Vimeo and embed with `{{< video src="https://...embed-url..." >}}`. GitHub blocks files over 100 MB and the whole Pages site should stay under ~1 GB.

## Known content gaps

A handful of URLs are broken on the *live* Wix site itself (confirmed via literal "404" markers in the mirrored HTML), not lost in extraction:

- 3 old blog posts under date-prefixed URLs (`post/2018/12/06/...`, `post/2018/12/27/...`)
- The Russian translations of `kopiya-curatorial-projects`, `kopiya-procartistination-branches`, and `poeticaltexts` (English versions are fine)

If these matter, they'd need to be recovered from the Wix dashboard directly — the live site no longer serves them.
