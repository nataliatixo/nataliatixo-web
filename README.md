# nataliatixo

Migration of https://nataliatixo.wixsite.com/nataliatixoeng off Wix onto GitHub Pages, without losing content.

Wix has no export feature, so this is a two-step migration: mirror the live site for its content/assets, then rebuild as a static site here.

## Status

- [x] Mirror the live Wix site (done 2026-07-07: 123 HTML pages + ~1.5GB media in `mirror/`)
- [x] Review mirrored content, decide structure — Hugo, bilingual EN/RU, ~74 project/bio pages + 33 blog posts
- [x] Rebuild pages here — Hugo site scaffolded, content extracted via `scripts/extract_content.py`
- [x] Restructure into 4 sections — About · Projects · Texts · Archive (Wix's "blog" was mostly archival material, so its posts were split into Texts (writing by the author) and Archive (activity log); interviews/press live at /press/ and are listed on the About page)
- [x] Style pass — minimalistic greyscale/light-grey theme (`static/css/style.css`)
- [x] Full EN/RU blog parity — all 33 posts now exist in both languages (translated by Claude where no native version existed; see `CLAUDE.md` for which posts are original vs. translated)
- [ ] Videos — 5 Wix videos have placeholder markers (`{{< video >}}` shortcode) on their posts; waiting on you to upload them (YouTube/Vimeo) and drop in the URLs
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
5. Only cancel the Wix subscription after everything is verified live.

Note: anything dynamic on the Wix site (contact forms, bookings, member areas) has no static equivalent — forms can move to Formspree/mailto; anything more interactive needs a third-party service or gets dropped.

## Known content gaps

A handful of URLs are broken on the *live* Wix site itself (confirmed via literal "404" markers in the mirrored HTML), not lost in extraction:

- 3 old blog posts under date-prefixed URLs (`post/2018/12/06/...`, `post/2018/12/27/...`)
- The Russian translations of `kopiya-curatorial-projects`, `kopiya-procartistination-branches`, and `poeticaltexts` (English versions are fine)

If these matter, they'd need to be recovered from the Wix dashboard directly — the live site no longer serves them.
