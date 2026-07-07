#!/usr/bin/env python3
"""
Extract content from the Wix mirror (mirror/) into Hugo content bundles
(content/). Run with the venv that has beautifulsoup4 + lxml installed.

Usage: python3 extract_content.py [--only slug1,slug2,...]
"""
import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

REPO = Path(__file__).resolve().parent.parent
MIRROR_HOST = REPO / "mirror" / "nataliatixo.wixsite.com"
SITE = MIRROR_HOST / "nataliatixoeng"
CONTENT = REPO / "content"

BLOCK_TAGS = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]
MEDIA_ID_RE = re.compile(r"media/([^/]+)/")
WIDTH_RE = re.compile(r"w_(\d+)")


# ---------------------------------------------------------------- helpers --

def load(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")


def page_title(soup: BeautifulSoup) -> str:
    t = soup.find("title")
    text = (t.get_text() if t else "").strip()
    if "|" in text:
        parts = [p.strip() for p in text.split("|")]
        if parts and parts[-1].lower() == "nataliatixo":
            text = " | ".join(parts[:-1]).strip()
    text = text or "Untitled"
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def esc_attr(text: str) -> str:
    return esc(text).replace('"', "&quot;")


def yaml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ------------------------------------------------------------- media copy --

def resolve_media(src: str, dest_dir: Path, used: dict) -> str | None:
    """Resolve a Wix media src to the best locally-mirrored resolution,
    copy it into dest_dir, and return its clean local filename."""
    m = re.search(r"([a-z.]+\.wixstatic\.com)/media/([^/]+)/", src)
    if not m:
        return None
    host, media_id = m.group(1), m.group(2)
    if media_id in used:
        return used[media_id]

    media_root = MIRROR_HOST.parent / host / "media"
    variant_dir = media_root / media_id
    candidates = [p for p in variant_dir.rglob("*") if p.is_file()] if variant_dir.is_dir() else []
    flat_file = media_root / media_id
    if flat_file.is_file():
        candidates.append(flat_file)
    if not candidates:
        return None

    def width_of(p: Path) -> int:
        wm = WIDTH_RE.search(str(p))
        return int(wm.group(1)) if wm else 0

    best = max(candidates, key=width_of)
    clean_name = re.sub(r"[^A-Za-z0-9._-]", "", media_id.replace("~mv2", ""))
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / clean_name
    if not dest_path.exists():
        shutil.copy(best, dest_path)
    used[media_id] = clean_name
    return clean_name


# ---------------------------------------------------------- HTML cleaning --

ZWSP = "​"


def rewrite_href(href: str) -> str:
    m = re.match(r"^https?://([^/]+)/?(.*)$", href)
    if m:
        host, rest = m.group(1), m.group(2)
        if host not in ("nataliatixo.wixsite.com", "www.nataliatixo.com", "nataliatixo.com"):
            return href
        if host == "nataliatixo.wixsite.com":
            rest = re.sub(r"^nataliatixoeng/?", "", rest)
        path = rest
    else:
        path = re.sub(r"^(\.\./)+", "", href)
        path = re.sub(r"^nataliatixoeng/", "", path)

    is_ru = bool(re.search(r"(\?|%3[Ff])lang=ru", path))
    stem = re.split(r"\?|%3[Ff]", path)[0]
    stem = stem[:-5] if stem.endswith(".html") else stem
    stem = stem.strip("/")

    m = re.match(r"^blog-1/hashtags/(.+)$", stem)
    if m:
        return f"/ru/tags/{m.group(1)}/" if is_ru else f"/tags/{m.group(1)}/"
    m = re.match(r"^blog-1/categories/(.+)$", stem)
    if m:
        return f"/ru/categories/{m.group(1)}/" if is_ru else f"/categories/{m.group(1)}/"

    if stem.startswith("post/"):
        slug = stem[len("post/"):]
        target = SLUG_TO_URL.get(f"post:{slug}")
    else:
        target = SLUG_TO_URL.get(stem)

    if not target:
        return href
    en_url, ru_url = target
    return ru_url if (is_ru and ru_url) else en_url


def clean_inline(node) -> str:
    out = []
    for child in getattr(node, "contents", []):
        if isinstance(child, NavigableString):
            out.append(esc(str(child)))
        elif child.name == "br":
            out.append("<br>")
        elif child.name == "a" and child.get("href"):
            out.append(f'<a href="{esc_attr(rewrite_href(child["href"]))}">{clean_inline(child)}</a>')
        elif child.name in ("b", "strong"):
            out.append(f"<strong>{clean_inline(child)}</strong>")
        elif child.name in ("i", "em"):
            out.append(f"<em>{clean_inline(child)}</em>")
        else:
            out.append(clean_inline(child))
    text = "".join(out).replace(ZWSP, "")
    return re.sub(r"[ \t]+", " ", text).strip()


def clean_block(node) -> list[tuple[str, str]]:
    """Return [(dedup_key, html), ...] for each paragraph-like block in node."""
    blocks = node.find_all(BLOCK_TAGS)
    if not blocks:
        inline = clean_inline(node)
        if not inline:
            return []
        return [(inline.lower(), f"<p>{inline}</p>")]
    out = []
    for b in blocks:
        tag = b.name if b.name.startswith("h") else "p"
        inline = clean_inline(b)
        if inline:
            out.append((inline.lower(), f"<{tag}>{inline}</{tag}>"))
    return out


def video_placeholder(node) -> str:
    src = node.get("src", "")
    m = re.search(r"([a-z.]+\.wixstatic\.com)/video/([^/]+)/", src)
    note = f"source: {m.group(1)}/video/{m.group(2)}/" if m else "source: unknown"
    return f'{{{{< video note="{esc_attr(note)}" >}}}}'


def extract_media_and_text(nodes, dest_dir: Path) -> str:
    used = {}
    emitted_images = set()
    parts = []
    seen_text = set()
    for node in nodes:
        if node.name == "img":
            local = resolve_media(node.get("src", ""), dest_dir, used)
            if local and local not in emitted_images:
                emitted_images.add(local)
                alt = node.get("alt", "") or ""
                parts.append(f'<img src="{local}" alt="{esc_attr(alt)}">')
        elif node.name == "video":
            parts.append(video_placeholder(node))
        else:
            for key, html in clean_block(node):
                if key not in seen_text:
                    seen_text.add(key)
                    parts.append(html)
    return "\n\n".join(parts)


def extract_project_body(soup: BeautifulSoup, dest_dir: Path) -> str:
    container = soup.find(id="SITE_PAGES")
    if not container:
        return ""
    nodes = container.find_all(
        lambda t: (t.get("data-testid") == "richTextElement" and not t.find_parent(id="SITE_HEADER") and not t.find_parent(id="SITE_FOOTER"))
        or (t.name in ("img", "video") and not t.find_parent(attrs={"data-testid": "richTextElement"}))
    )
    return extract_media_and_text(nodes, dest_dir)


def extract_post_body(soup: BeautifulSoup, dest_dir: Path) -> str:
    container = soup.find(attrs={"data-hook": "post-description"})
    if not container:
        return ""
    nodes = container.find_all(lambda t: t.name in ("p", "img", "video") and not (t.name == "img" and t.find_parent("p")))
    return extract_media_and_text(nodes, dest_dir)


def post_date(soup: BeautifulSoup) -> str | None:
    tag = soup.find(attrs={"data-hook": "time-ago"})
    if not tag:
        return None
    try:
        return datetime.strptime(tag.get_text(strip=True), "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


# ----------------------------------------------------------- file writers --

def write_bundle(dir_path: Path, filename: str, title: str, body: str, extra_front_matter: str = ""):
    dir_path.mkdir(parents=True, exist_ok=True)
    front = f"---\ntitle: {yaml_str(title)}\n{extra_front_matter}---\n\n"
    (dir_path / filename).write_text(front + body + "\n", encoding="utf-8")


def project_page(rel_html: str, dest_dir: Path, filename: str, extra_front_matter: str = ""):
    path = SITE / rel_html
    if not path.exists():
        print(f"  MISSING {rel_html}", file=sys.stderr)
        return
    soup = load(path)
    title = page_title(soup)
    body = extract_project_body(soup, dest_dir)
    if not body and soup.find("title") is None:
        # Wix serves a 404 shell for this URL (no <title>, no body) - skip it
        # rather than write a blank placeholder page.
        print(f"  SKIP (404 on live site): {rel_html}", file=sys.stderr)
        return
    write_bundle(dest_dir, filename, title, body, extra_front_matter)


# Posts that are independently-written EN/RU pairs of the same piece under
# different slugs (the author published them as two separate Wix blog posts
# rather than one bilingual post) - linked via translationKey rather than
# machine-translated, since a native version already exists.
TRANSLATION_PAIRS = {
    "essay-the-case-at-the-border": "case-at-the-border",
    "эссе-случай-на-границе": "case-at-the-border",
}


def post_page(rel_html: str, dest_dir: Path, categories: list[str], tags: list[str], slug: str = "", group: str = ""):
    path = SITE / rel_html
    if not path.exists():
        print(f"  MISSING {rel_html}", file=sys.stderr)
        return
    soup = load(path)
    title = page_title(soup)
    body = extract_post_body(soup, dest_dir)
    date = post_date(soup)
    fm = ""
    if group:
        fm += f"group: {group}\n"
    if date:
        fm += f"date: {date}\n"
    if categories:
        fm += "categories: [" + ", ".join(yaml_str(c) for c in categories) + "]\n"
    if tags:
        fm += "tags: [" + ", ".join(yaml_str(t) for t in tags) + "]\n"
    if slug in TRANSLATION_PAIRS:
        fm += f"translationKey: {yaml_str(TRANSLATION_PAIRS[slug])}\n"
    # Language is decided by actual content, not the (sometimes Latin-script)
    # URL slug - e.g. the post at /post/information is titled "Информационное"
    # and is entirely in Russian despite its English-looking slug.
    filename = "index.ru.md" if is_cyrillic(title + body) else "index.md"
    write_bundle(dest_dir, filename, title, body, fm)


# --------------------------------------------------------------- manifest --

ARTISTIC_OBJECTS = [
    "academy", "babushka-s", "behing-the", "cover", "cube-not-cube", "daily-news",
    "dialog", "figuresmillion", "frames", "heaven", "monotype", "no-words-no-war",
    "on-line", "planets", "rooms", "rooms-1", "scale-experiments", "somethingnew",
    "sometimes-behave-so-strangely", "the-blue-serie", "the-decay-time-of-mettastable-state",
    "the-google-it", "track-track", "under-ground", "verbatim-1", "you-can-touch-it",
]

CURATORIAL = [
    "artgarbage-coop", "communication-management-unit", "kopiya-curatorial-projects",
    "kopiya-procartistination-branches", "tracktrack-exhibitions",
]

# Wix blog posts, redistributed into the site's Texts and Archive sections
# by what they actually are, not the Wix app they lived in:
# - texts/poetry: creative writing (poems, prose pieces)
# - texts/essays: essays and published texts written by the author
# - archive: dated activity log (talks, lectures, announcements, mediations)
#   plus interviews *about* the author (press, not authored texts).
#
# NOTE: post/2018/12/06/presentation-of-babushkas-project-in-dk-rose,
# post/2018/12/06/review-of-exhibition-letter-to-future, and
# post/2018/12/27/presentation-about-digital-artdigest are 404 on the
# live Wix site itself (confirmed via literal "404" markers in the
# mirrored HTML) - dropped rather than extracted as empty placeholders.

TEXTS_POETRY = [
    "post/cтих-война-как",
    "post/essay-the-case-at-the-border",
    "post/information",
    "post/весна-не-наступает-экспериментальная-поэзия",
    "post/планеты",
    "post/послушайте-экспериментальная-поэзия",
    "post/постапокалиптическое-стихотворение-сети-для-сетьсолидарности-поэтыпротивпыток-всепротивпыток",
    "post/случай-во-время-городского-праздника",
    "post/стихи-перевертыши",
    "post/стих-человек-это",
    "post/стих-экспликация-к-выставке-кожаные-ублюдки-действие-у",
    "post/эссе-случай-на-границе",
]

TEXTS_ESSAYS = [
    "post/блиц-внесение-поправок-в-федеральный-закон-об-образовании-для-spectate-ru",
    "post/онлайн-платформы-как-гибридные-формы-выставок-вcтупление",
    "post/татьяна-кирьянова-екатерина-соколовская-и-наталья-тихонова-справочник",
    "post/текст-к-выставке-таты-гориан-ужас-вы-находитесь-здесь-для-aroundart-org",
    "post/экспликация-к-выставке-кожаные-ублюдки-действие-у",
]

ARCHIVE_POSTS = [
    "post/artist-talk-в-студии-studio-4-413-для-студентов-школы-пайдейя",
    "post/publication-in-final-documentation-after-dwelling-on-the-threshold-worshop-in-nida-art-colony",
    "post/studio-studies-project-for-curatorial-forum",
    "post/конференция-цифровое-и-человеческое",
    "post/лекция-онлайн-платформы-как-гибридные-формы-выставок-в-целинном",
    "post/медиация-по-выставке-pangardenia-в-рамках-ars-electronica-в-air-itmo-gallery-с-инсталляцией-цветок",
    "post/отмена-показа-наблюдать-и-пунктировать-горизонты",
    "post/практическое-занятие-для-студентов-школы-интерпретации-современного-искусства-пайдейя",
    "post/презентация-с-картинками-для-портфолио-ревью",
    "post/прокартистинаторский-бранч-в-галерее-люда",
    "post/рассказ-о-проектах-для-студентов-школы-пайдея",
    "post/участие-в-конференции-дар-и-труд-в-искусстве",
]

# Interviews *about* the author - live at /press/<slug>/ (a section kept out
# of the nav) and are surfaced as a "Press" list on the About page.
PRESS = [
    "post/2019/12/13/статья-интервью-для-aroundartorg-с-михаилом-степановым",
    "post/беседа-с-михаилом-степановым-для-aroundart-org-часть-вторая",
    "post/интервью-для-artuzel-про-видео-арт-клуб",
    "post/интервью-для-крапивы",
]


def build_slug_map() -> dict[str, tuple[str, str | None]]:
    m: dict[str, tuple[str, str | None]] = {
        "nataliatixoeng": ("/", "/ru/"),
        "artisticprojects": ("/projects/", "/ru/projects/"),
        "curatorial": ("/projects/", "/ru/projects/"),
        "poetical": ("/texts/", "/ru/texts/"),
        "blog-1": ("/archive/", "/ru/archive/"),
        "random-pictures": ("/archive/random-pictures/", "/ru/archive/random-pictures/"),
    }
    for slug in ARTISTIC_OBJECTS + CURATORIAL:
        m[slug] = (f"/projects/{slug}/", f"/ru/projects/{slug}/")
    for rel in TEXTS_POETRY + TEXTS_ESSAYS:
        slug = rel.split("/")[-1]
        m[f"post:{slug}"] = (f"/texts/{slug}/", None)
    for rel in ARCHIVE_POSTS:
        slug = rel.split("/")[-1]
        m[f"post:{slug}"] = (f"/archive/{slug}/", None)
    for rel in PRESS:
        slug = rel.split("/")[-1]
        m[f"post:{slug}"] = (f"/press/{slug}/", None)
    return m


SLUG_TO_URL = build_slug_map()


def is_cyrillic(text: str) -> bool:
    return bool(re.search("[а-яА-Я]", text))


def normalize_post_slug(href: str) -> str:
    tail = href.split("/post/")[-1].rstrip("/").split("?")[0]
    if tail.endswith(".html"):
        tail = tail[:-5]
    return tail.split("/")[-1]


def load_category_membership() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    membership: dict[str, list[str]] = {}

    def add(slug_key, value):
        membership.setdefault(slug_key, []).append(value)

    # Wix also had "english" and "русский" category listings, deliberately not
    # extracted: language is handled by the EN/RU site split, not a taxonomy.
    for cat in ["poetical", "research"]:
        path = SITE / "blog-1" / "categories" / f"{cat}.html"
        if not path.exists():
            continue
        soup = load(path)
        for a in soup.find_all("a", href=True):
            if "/post/" in a["href"]:
                add(normalize_post_slug(a["href"]), cat)

    tags_map = {}
    for fname in ["research", "texts"]:
        path = SITE / "blog-1" / "hashtags" / f"{fname}.html"
        if not path.exists():
            continue
        soup = load(path)
        for a in soup.find_all("a", href=True):
            if "/post/" in a["href"]:
                tags_map.setdefault(normalize_post_slug(a["href"]), []).append(fname)

    return membership, tags_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="comma-separated slugs to limit extraction to (for validation runs)")
    args = parser.parse_args()
    only = set(args.only.split(",")) if args.only else None

    def wanted(slug):
        return only is None or slug in only

    # --- home page ---
    if wanted("home"):
        print("home")
        soup_en = load(MIRROR_HOST / "nataliatixoeng.html")
        soup_ru = load(MIRROR_HOST / "nataliatixoeng?lang=ru.html")
        body_en = extract_project_body(soup_en, CONTENT)
        body_ru = extract_project_body(soup_ru, CONTENT)
        write_bundle(CONTENT, "_index.md", "About", body_en)
        write_bundle(CONTENT, "_index.ru.md", "О себе", body_ru)

    # --- projects (artistic objects + curatorial, one section) ---
    projects_dir = CONTENT / "projects"
    if wanted("projects"):
        print("projects")
        write_bundle(projects_dir, "_index.md", "Projects", "")
        write_bundle(projects_dir, "_index.ru.md", "Проекты", "")

    for group, children in [("artistic", ARTISTIC_OBJECTS), ("curatorial", CURATORIAL)]:
        for child in children:
            if not wanted(child):
                continue
            child_dir = projects_dir / child
            print(" ", child)
            project_page(f"{child}.html", child_dir, "index.md", f"group: {group}\n")
            project_page(f"{child}?lang=ru.html", child_dir, "index.ru.md", f"group: {group}\n")

    # --- texts + archive + press ---
    if wanted("texts-index"):
        print("texts-index")
        write_bundle(CONTENT / "texts", "_index.md", "Texts", "")
        write_bundle(CONTENT / "texts", "_index.ru.md", "Тексты", "")
    if wanted("archive-index"):
        print("archive-index")
        write_bundle(CONTENT / "archive", "_index.md", "Archive", "")
        write_bundle(CONTENT / "archive", "_index.ru.md", "Архив", "")
    if wanted("press-index"):
        print("press-index")
        write_bundle(CONTENT / "press", "_index.md", "Press", "")
        write_bundle(CONTENT / "press", "_index.ru.md", "Пресса", "")

    if wanted("random-pictures"):
        print("random-pictures")
        rp_dir = CONTENT / "archive" / "random-pictures"
        project_page("random-pictures.html", rp_dir, "index.md")
        project_page("random-pictures?lang=ru.html", rp_dir, "index.ru.md")

    categories_map, tags_map = load_category_membership()

    for section, group, rels in [
        ("texts", "poetry", TEXTS_POETRY),
        ("texts", "essays", TEXTS_ESSAYS),
        ("archive", "", ARCHIVE_POSTS),
        ("press", "", PRESS),
    ]:
        for rel in rels:
            slug = rel.split("/")[-1]
            if not wanted(slug):
                continue
            print("post:", slug)
            post_dir = CONTENT / section / slug
            cats = categories_map.get(slug, [])
            tags = tags_map.get(slug, [])
            post_page(f"{rel}.html", post_dir, cats, tags, slug=slug, group=group)


if __name__ == "__main__":
    main()
