"""Append ratings exported from the rating page's store to ratings.jsonl.

Usage:  python scripts/pull_ratings.py <export_dir>
<export_dir> holds one JSON file per rating document (the store's `ratings` collection,
as written by the rating page). ratings.jsonl is append-only and the last line per id wins,
so only ratings that differ from the current last line are appended. Unknown ids are
reported and skipped. Exit 1 if any file could not be read.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("nature", "verdict", "why", "dims", "poles", "roles", "star")


def main():
    src = Path(sys.argv[1])
    known = {json.loads(l)["id"] for l in (ROOT / "catalog.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    rpath = ROOT / "ratings.jsonl"
    last = {}
    for l in rpath.read_text(encoding="utf-8").splitlines() if rpath.exists() else []:
        if l.strip():
            r = json.loads(l); last[r["id"]] = r
    new, bad, unknown = [], 0, []
    for f in sorted(src.rglob("*.json")):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            bad += 1; continue
        doc = doc.get("data", doc)  # tolerate the store's {id, data, version} envelope
        rid = doc.get("id") or f.stem
        if rid not in known:
            unknown.append(rid); continue
        row = {"id": rid, **{k: doc.get(k) for k in FIELDS}, "ts": doc.get("ts")}
        if not row["verdict"] and not any(row[k] for k in ("dims", "poles", "roles", "star", "why")):
            continue  # cleared rating: nothing to record
        if rid in last and all(last[rid].get(k) == row[k] for k in FIELDS):
            continue
        new.append(row)
    with rpath.open("a", encoding="utf-8", newline="\n") as fh:
        for r in sorted(new, key=lambda r: r.get("ts") or ""):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"appended {len(new)} rating(s); unchanged skipped; unknown ids {unknown}; unreadable {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
