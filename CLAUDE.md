# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## What this is

A Wix-to-GitHub-Pages migration for https://nataliatixo.wixsite.com/nataliatixoeng. Wix has no export function, so the plan (see README.md) is: mirror the live site with `wget` for content/assets, then hand-rebuild it as a static site here, then deploy via GitHub Pages.

## Current state

Nothing has been rebuilt yet — this repo is a scaffold. The live site was returning HTTP 500 as of 2026-07-07; `scripts/mirror.sh` has not successfully run yet.

## Working here

- `mirror/` (once populated by `scripts/mirror.sh`) is a **content archive only** — raw Wix output full of framework JS and tracking scripts. Never deploy it directly; only pull text/images/structure out of it into the real site files at the repo root.
- Once content is extracted, decide plain HTML/CSS vs. a static site generator (Hugo/Astro) based on how much content there actually is (a handful of pages vs. a blog with many posts). Follow the pattern of sibling repos `../bugueno.co` and `../centricity-808-landing` (plain HTML/CSS, no build step, GitHub Pages from repo root) if the site stays small.
- Anything dynamic on the original (contact forms, bookings) has no static equivalent — plan to replace with Formspree/mailto or drop it.
