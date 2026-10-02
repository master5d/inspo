"""One-time import: Netscape bookmarks.html (folder "Inspo") -> catalog.jsonl.

Usage:  python scripts/import_bookmarks.py <bookmarks.html> [--folder Inspo] [--out catalog.jsonl]

Layout = 5 medium axes + feeds on top, the owner's original folders nested inside.
After the import, catalog.jsonl is the source of truth: new sections are added there,
not re-imported. Re-running refuses to overwrite an existing catalog unless --force.
"""
import argparse, hashlib, json, re, sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

AXES = {
    "image": "1-image",
    "interface": "2-interface-print",
    "space": "3-space-object",
    "motion-sound": "4-motion-sound",
    "ideas": "5-culture-ideas",
    "feeds": "6-feeds",
}

# original path prefix -> (axis, how many leading folders to drop, kind). First match wins.
# "Hobbies" is unwrapped: its children belong to different axes.
RULES = [
    (["Hobbies", "Industrial Design"], "space", 1, "reference"),
    (["Hobbies", "Tiny Homes"], "space", 1, "reference"),
    (["Hobbies", "Mixed Reality (AV)", "VJing", "Soft Sites"], "motion-sound", 1, "tool"),
    (["Hobbies", "Mixed Reality (AV)", "VJing", "Software"], "motion-sound", 1, "tool"),
    (["Hobbies", "Mixed Reality (AV)", "VJing", "Gear"], "motion-sound", 1, "gear"),
    (["Hobbies", "Mixed Reality (AV)"], "motion-sound", 1, "reference"),
    (["Hobbies", "Music", "Apps"], "motion-sound", 1, "tool"),
    (["Hobbies", "Music", "music making"], "motion-sound", 1, "tool"),
    (["Hobbies", "Music", "Server"], "motion-sound", 1, "tool"),
    (["Hobbies", "Music", "Services"], "motion-sound", 1, "tool"),
    (["Hobbies", "Music", "purchase"], "motion-sound", 1, "shop"),
    (["Hobbies", "Music", "Vinyl"], "motion-sound", 1, "shop"),
    (["Hobbies", "Music", "Intuitive Muisc Instruments"], "motion-sound", 1, "shop"),
    (["Hobbies", "Music", "Artists"], "motion-sound", 1, "artist"),
    (["Hobbies", "Music", "Labels"], "motion-sound", 1, "label"),
    (["Hobbies", "Music", "Discovery"], "motion-sound", 1, "gallery"),
    (["Hobbies", "Music"], "motion-sound", 1, "reference"),
    (["Hobbies", "Movies"], "motion-sound", 1, "reference"),
    (["Hobbies", "Photography", "Gear"], "image", 1, "gear"),
    (["Hobbies", "Photography", "Wireless Mics"], "image", 1, "gear"),
    (["Hobbies", "Photography"], "image", 1, "reference"),
    (["Hobbies"], "feeds", 0, "reference"),
    (["Illustrations", "Communities"], "image", 0, "community"),
    (["Illustrations", "Museum Art Collections"], "image", 0, "collection"),
    (["Illustrations"], "image", 0, "artist"),
    (["Photography"], "image", 0, "artist"),
    (["Wallpapers"], "image", 0, "gallery"),
    (["Mems"], "image", 0, "gallery"),
    (["Visual Design", "Insta Posts"], "interface", 0, "tool"),
    (["Visual Design", "Links in bio", "inspo"], "interface", 0, "example"),
    (["Visual Design", "Links in bio"], "interface", 0, "tool"),
    (["Visual Design", "Fonts"], "interface", 0, "foundry"),
    (["Visual Design", "Print"], "interface", 0, "service"),
    (["Visual Design", "Presentation"], "interface", 0, "service"),
    (["Visual Design", "QR Codes"], "interface", 0, "tool"),
    (["Visual Design", "Merch"], "interface", 0, "service"),
    (["Visual Design", "Data Viz"], "interface", 0, "reference"),
    (["Visual Design"], "interface", 0, "tool"),
    (["Web Design"], "interface", 0, "gallery"),
    (["Web Trends"], "interface", 0, "gallery"),
    (["Architecture"], "space", 0, "magazine"),
    (["Installations"], "space", 0, "artist"),
    (["fashion & apparel"], "space", 0, "reference"),
    (["Video Channels"], "motion-sound", 0, "channel"),
    (["YouTube"], "motion-sound", 0, "channel"),
    (["blogs"], "ideas", 0, "magazine"),
    (["Design"], "ideas", 0, "magazine"),
    (["Storytelling"], "ideas", 0, "magazine"),
    (["Futurism"], "ideas", 0, "reference"),
    (["Ads"], "ideas", 0, "gallery"),
    (["Tuts"], "ideas", 0, "course"),
    (["Casual News"], "feeds", 0, "magazine"),
    (["GAG"], "feeds", 0, "magazine"),
    (["News & Media"], "feeds", 0, "magazine"),
]

# Links that sat directly in the root of "Inspo": placed one by one (owner-approved 2026-10-02).
ROOT = {
    "dailyom.com": ("ideas", ["Consciousness"], "magazine"),
    "highexistence.com": ("ideas", ["Consciousness"], "magazine"),
    "psychedelicadventure.net": ("ideas", ["Consciousness"], "magazine"),
    "realitysandwich.com": ("ideas", ["Consciousness"], "magazine"),
    "thespiritscience.net": ("ideas", ["Consciousness"], "magazine"),
    "themindunleashed.com": ("ideas", ["Consciousness"], "magazine"),
    "pinterest.com": ("ideas", ["Discovery"], "gallery"),
    "tumblr.com": ("ideas", ["Discovery"], "gallery"),
    "mix.com": ("ideas", ["Discovery"], "gallery"),
    "ted.com": ("ideas", ["Ideas & Media"], "magazine"),
    "knife.media": ("ideas", ["Ideas & Media"], "magazine"),
    "vice.com": ("ideas", ["Ideas & Media"], "magazine"),
    "readingdesign.org": ("ideas", ["Design"], "reference"),
    "thisiscolossal.com": ("ideas", ["blogs"], "magazine"),
    "artspace.com": ("image", ["Illustrations"], "gallery"),
    "timewheel.net": ("interface", ["Visual Design", "Data Viz"], "reference"),
    "checkiday.com": ("interface", ["Visual Design", "Insta Posts"], "tool"),
    "electricsheep.org": ("motion-sound", ["Mixed Reality (AV)", "VJing", "Visuals"], "artist"),
    "upworthy.com": ("feeds", ["Casual News"], "magazine"),
    "greatist.com": ("feeds", ["Casual News"], "magazine"),
    "techinsider.ru": ("feeds", ["Casual News"], "magazine"),
}

FIX = {"Intuitive Muisc Instruments": "Intuitive Music Instruments", "Geneology": "Genealogy"}
TRACKING = re.compile(r"(?i)^(utm_.*|fbclid|gclid|mc_eid|mc_cid|yclid|_hsenc|_hsmi)$")


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {"name": "", "folders": [], "links": []}
        self.stack, self.pending, self.cur, self.text, self.opened = [self.root], None, None, "", False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h3":
            self.cur, self.text = ("h3", {"name": "", "folders": [], "links": []}), ""
        elif tag == "a":
            self.cur, self.text = ("a", {"title": "", "url": a.get("href", ""), "add_date": a.get("add_date")}), ""
        elif tag == "dl":
            if self.pending is not None:
                self.stack.append(self.pending); self.pending = None
            elif not self.opened:
                self.opened = True
            else:
                self.stack.append(self.stack[-1])

    def handle_endtag(self, tag):
        if tag == "h3" and self.cur and self.cur[0] == "h3":
            f = self.cur[1]; f["name"] = self.text.strip()
            self.stack[-1]["folders"].append(f); self.pending, self.cur = f, None
        elif tag == "a" and self.cur and self.cur[0] == "a":
            l = self.cur[1]; l["title"] = self.text.strip()
            self.stack[-1]["links"].append(l); self.cur = None
        elif tag == "dl" and len(self.stack) > 1:
            self.stack.pop()

    def handle_data(self, data):
        if self.cur:
            self.text += data


def slug(s: str) -> str:
    s = s.replace("&", "and").replace("|", " ")
    s = re.sub(r"[^\w]+", "-", s, flags=re.U).strip("-").lower()
    return s or "misc"


def clean_url(u: str) -> str:
    s = urlsplit(u)
    q = [(k, v) for k, v in parse_qsl(s.query, keep_blank_values=True) if not TRACKING.match(k)]
    return urlunsplit((s.scheme, s.netloc, s.path, urlencode(q, doseq=True), s.fragment))


def host(u: str) -> str:
    h = (urlsplit(u).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def item_id(u: str) -> str:
    key = clean_url(u).rstrip("/").lower().replace("://www.", "://")
    return f"{slug(host(u))[:40]}-{hashlib.sha256(key.encode()).hexdigest()[:6]}"


def same_page_key(u: str) -> str:
    """Duplicate detection ignores scheme and www: http://www.x.com/ and https://x.com are one
    page (siteInspire came in twice that way, 2026-10-02). The id keeps its original format."""
    s = urlsplit(clean_url(u))
    return f"{host(u)}{s.path.rstrip('/')}?{s.query}".lower()


def place(path):
    if not path:
        return None
    for pre, axis, drop, kind in RULES:
        if path[:len(pre)] == pre:
            return axis, [FIX.get(p, p) for p in path[drop:]], kind
    raise ValueError(f"no rule for {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bookmarks")
    ap.add_argument("--folder", default="Inspo")
    ap.add_argument("--out", default="catalog.jsonl")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists() and not a.force:
        sys.exit(f"{out} exists: catalog.jsonl is the source of truth after import (use --force to redo)")

    p = _Parser(); p.feed(Path(a.bookmarks).read_text(encoding="utf-8", errors="replace"))
    tops = [f for f in p.root["folders"] if f["name"] == a.folder]
    if len(tops) != 1:
        sys.exit(f"expected exactly one top-level folder {a.folder!r}, found {len(tops)}")

    rows, seen, dups = [], set(), []

    def walk(f, path):
        for l in f["links"]:
            u = clean_url(l["url"])
            placed = place(path)
            if placed is None:
                h = host(u)
                if h not in ROOT:
                    raise ValueError(f"root link without a placement: {u}")
                placed = ROOT[h]
            axis, sub, kind = placed
            iid = item_id(u)
            if same_page_key(u) in seen:
                dups.append(u); continue
            seen.add(same_page_key(u))
            added = (datetime.fromtimestamp(int(l["add_date"]), timezone.utc).date().isoformat()
                     if l.get("add_date") else None)
            rows.append({
                "id": iid, "title": l["title"] or host(u), "url": u,
                "axis": AXES[axis], "path": sub,
                "folder": "/".join([AXES[axis]] + [slug(s) for s in sub]),
                "kind": kind, "added": added,
                "origin": "bookmarks:" + "/".join([a.folder] + path),
                "status": "unchecked",
            })
        for c in f["folders"]:
            walk(c, path + [c["name"]])

    walk(tops[0], [])
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"imported {len(rows)} links, {len(dups)} duplicate(s) merged: {dups}")


if __name__ == "__main__":
    main()
