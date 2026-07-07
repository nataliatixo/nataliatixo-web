# nataliatixo

Migration of https://nataliatixo.wixsite.com/nataliatixoeng off Wix onto GitHub Pages, without losing content.

Wix has no export feature, so this is a two-step migration: mirror the live site for its content/assets, then rebuild as a static site here.

## Status

- [x] Mirror the live Wix site (done 2026-07-07: 123 HTML pages + ~1.5GB media in `mirror/`)
- [x] Review mirrored content, decide structure — Hugo, bilingual EN/RU, ~74 project/bio pages + 33 blog posts
- [x] Rebuild pages here — Hugo site scaffolded, content extracted via `scripts/extract_content.py`
- [ ] Deploy to GitHub Pages (workflow ready in `.github/workflows/deploy.yml`; Pages source still needs to be switched to "GitHub Actions" in repo Settings — not done yet, needs your go-ahead)
- [ ] Point custom domain `nataliatixo.com` (CNAME file already in `static/CNAME`; DNS not configured yet) and retire the Wix subscription

## Stack

Hugo, hand-written minimal layouts (no third-party theme). Bilingual EN (default) / RU via Hugo's multilingual support, with a client-side script that auto-redirects Russian-language browsers on first visit and a manual toggle that persists via `localStorage`. See `CLAUDE.md` for the full content structure and extraction pipeline.

## Local development

```bash
hugo server -D
```

## Migration plan

1. **Extract**: `scripts/mirror.sh` runs `wget --mirror` against the live site into `mirror/` (gitignored — it's a scratch archive, not the deployable site), including Wix's CDN hosts so media downloads alongside HTML. Also manually export anything only in the Wix dashboard: blog drafts, form submissions, full-res media library originals (the mirror only captures web-resolution images, not true originals).
2. **Rebuild**: `scripts/extract_content.py` (Python, BeautifulSoup) parses the mirror and writes Hugo content bundles under `content/`. Re-run it if the mirror is refreshed; it overwrites existing content files.
3. **Deploy**: push to `main` — `.github/workflows/deploy.yml` builds with Hugo and deploys via GitHub Actions. Requires: repo Settings → Pages → Source → "GitHub Actions" (one-time, not yet done).
4. **Domain**: `static/CNAME` already contains `nataliatixo.com`. Still needed: point DNS (A records to GitHub's Pages IPs, CNAME record for `www`), then enable HTTPS enforcement in Pages settings.
5. Only cancel the Wix subscription after everything is verified live.

Note: anything dynamic on the Wix site (contact forms, bookings, member areas) has no static equivalent — forms can move to Formspree/mailto; anything more interactive needs a third-party service or gets dropped.

## Known content gaps

A handful of URLs are broken on the *live* Wix site itself (confirmed via literal "404" markers in the mirrored HTML), not lost in extraction:

- 3 old blog posts under date-prefixed URLs (`post/2018/12/06/...`, `post/2018/12/27/...`)
- The Russian translations of `kopiya-curatorial-projects`, `kopiya-procartistination-branches`, and `poeticaltexts` (English versions are fine)

If these matter, they'd need to be recovered from the Wix dashboard directly — the live site no longer serves them.
