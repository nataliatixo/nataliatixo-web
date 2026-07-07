# nataliatixo

Migration of https://nataliatixo.wixsite.com/nataliatixoeng off Wix onto GitHub Pages, without losing content.

Wix has no export feature, so this is a two-step migration: mirror the live site for its content/assets, then rebuild as a static site here.

## Status

- [ ] Mirror the live Wix site (blocked: site was returning HTTP 500 as of 2026-07-07 — retry `scripts/mirror.sh`)
- [ ] Review mirrored content, decide structure (plain HTML vs. static site generator) once we can see how many pages/posts exist
- [ ] Rebuild pages here
- [ ] Deploy to GitHub Pages
- [ ] Point custom domain (if any) and retire the Wix subscription

## Migration plan

1. **Extract**: `scripts/mirror.sh` runs `wget --mirror` against the live site into `mirror/` (gitignored — it's a scratch archive, not the deployable site). Also manually export anything only in the Wix dashboard: blog drafts, form submissions, full-res media library originals.
2. **Rebuild**: pull text/images out of `mirror/` into a clean structure here. Pandoc can do a first-pass HTML→Markdown conversion for blog posts if there are many.
3. **Deploy**: push to a repo with GitHub Pages enabled (Settings → Pages → source).
4. **Domain**: if using a custom domain, add a `CNAME` file, point DNS (A records to GitHub's Pages IPs, CNAME for `www`), enable HTTPS enforcement.
5. Only cancel the Wix subscription after everything is verified live.

Note: anything dynamic on the Wix site (contact forms, bookings, member areas) has no static equivalent — forms can move to Formspree/mailto; anything more interactive needs a third-party service or gets dropped.
