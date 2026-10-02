"""Build rater/index.html (the rating page) from rater/template.html + catalog.jsonl.

Usage:  python scripts/build_rater.py
The page embeds the catalog; ratings live in the page's own store and are pulled into
ratings.jsonl separately. Rebuild and republish after the catalog changes.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AXES = {"1-image": "Image", "2-interface-print": "Interface & Print", "3-space-object": "Space & Object",
        "4-motion-sound": "Motion & Sound", "5-culture-ideas": "Culture & Ideas", "6-feeds": "Feeds"}

rows = [json.loads(l) for l in (ROOT / "catalog.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
data = [{k: r.get(k) for k in ("id", "title", "url", "axis", "path", "folder", "kind", "nature", "status", "wayback")} for r in rows]
tpl = (ROOT / "rater" / "template.html").read_text(encoding="utf-8")
for marker in ("/*CATALOG*/[]", "/*AXES*/{}"):
    if tpl.count(marker) != 1:
        raise SystemExit(f"template marker {marker!r} must appear exactly once")
js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
html = tpl.replace("/*CATALOG*/[]", js(data)).replace("/*AXES*/{}", js(AXES))
html = html.replace("426 links · loading", f"{len(data)} links · loading")
(ROOT / "rater" / "index.html").write_text(html, encoding="utf-8", newline="\n")
print(f"rater/index.html: {len(data)} links, {len(html) // 1024} KB")
