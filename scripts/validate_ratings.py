"""Check ratings.jsonl against the chip schema (CHIPS.md) before anything downstream reads it.

Usage:  python scripts/validate_ratings.py [ratings.jsonl]
Every line is checked on its own (the last line per id is what the lab's bridge consumes, but a
broken earlier line still means the file is not what the page wrote). Findings are printed one
per line with the line number; exit 1 if any line fails, 0 otherwise. Nothing is modified.

The lab (NAUTILUS core/desops/scripts/taste_catalog.py) carries a taste verdict with a `why`
into its ledger only when `dims` is non-empty and the axis maps to a medium (axes 1-4); this
script does not enforce those lab-side rules, it enforces the catalog's own schema.
"""
import json, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NATURES = ("taste", "utility")
VERDICTS = {"taste": ("core", "take", "watch", "archive", "reject"), "utility": ("keep", "archive", "drop")}
NEEDS_WHY = ("core", "take", "reject", "keep")
DIMS = ("form/proportion", "color/light", "type/letter", "rhythm/space",
        "material/texture", "motion/time", "mood/narrative", "contrast/hierarchy")
POLES = {"air-density": ("air", "density"), "grid-break": ("grid", "break"), "hand-machine": ("hand", "machine"),
         "warm-cold": ("warm", "cold"), "quiet-loud": ("quiet", "loud"), "organic-geometric": ("organic", "geometric"),
         "sacred-utilitarian": ("sacred", "utilitarian"), "retro-future": ("retro", "future"),
         "minimal-excess": ("minimal", "excess"), "single-collage": ("single idea", "collage")}
ROLES = {"taste": ("reference", "sweep", "tool", "ideas", "learn", "community", "shop"),
         "utility": ("sweep", "tool", "ideas", "learn", "community", "shop")}
KEYS = {"id", "ts", "nature", "verdict", "why", "dims", "poles", "roles", "star"}


def check(r, known, default_nature):
    """Return a list of problems for one rating object."""
    out = []
    if not isinstance(r, dict):
        return ["not a JSON object"]
    extra = set(r) - KEYS
    if extra:
        out.append(f"unknown fields {sorted(extra)}")
    rid = r.get("id")
    if not isinstance(rid, str) or not rid:
        return out + ["missing id"]
    if rid not in known:
        out.append(f"id {rid!r} is not in catalog.jsonl")
    nature = r.get("nature") or default_nature.get(rid) or "taste"
    if nature not in NATURES:
        out.append(f"nature {nature!r} not in {NATURES}")
        nature = "taste"
    verdict = r.get("verdict")
    if verdict is not None and verdict not in VERDICTS[nature]:
        out.append(f"verdict {verdict!r} is not a {nature} verdict {VERDICTS[nature]}")
    why = r.get("why")
    if why is not None and not isinstance(why, str):
        out.append("why must be a string")
    if verdict in NEEDS_WHY and not (isinstance(why, str) and why.strip()):
        out.append(f"verdict {verdict} needs a why")
    dims = r.get("dims") or []
    if not isinstance(dims, list) or any(d not in DIMS for d in dims):
        out.append(f"dims {dims!r}: list of up to three of {DIMS}")
    elif len(dims) > 3 or len(dims) != len(set(dims)):
        out.append(f"dims {dims!r}: up to three, no repeats")
    elif dims and nature != "taste":
        out.append("dims are for taste objects only")
    poles = r.get("poles") or {}
    if not isinstance(poles, dict):
        out.append("poles must be an object pair -> side")
    else:
        for pair, side in poles.items():
            if pair not in POLES:
                out.append(f"unknown pole pair {pair!r}")
            elif side not in POLES[pair]:
                out.append(f"pole {pair}: side {side!r} not in {POLES[pair]}")
        if poles and nature != "taste":
            out.append("poles are for taste objects only")
    roles = r.get("roles") or []
    if not isinstance(roles, list) or any(x not in ROLES[nature] for x in roles):
        out.append(f"roles {roles!r}: subset of {ROLES[nature]} for a {nature} object")
    if "star" in r and r["star"] is not None and not isinstance(r["star"], bool):
        out.append("star must be true/false")
    ts = r.get("ts")
    if ts is not None:
        try:
            datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except ValueError:
            out.append(f"ts {ts!r} is not ISO time")
    return out


def main():
    rpath = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "ratings.jsonl"
    rows = [json.loads(l) for l in (ROOT / "catalog.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    known = {r["id"] for r in rows}
    default_nature = {r["id"]: r.get("nature", "taste") for r in rows}
    if not rpath.exists():
        print(f"{rpath.name}: no file, 0 ratings")
        return 0
    bad = total = 0
    for i, line in enumerate(rpath.read_text(encoding="utf-8").split("\n"), 1):
        if not line.strip():
            continue
        total += 1
        try:
            r = json.loads(line)
        except ValueError as e:
            bad += 1; print(f"{rpath.name}:{i}: not JSON ({e})"); continue
        problems = check(r, known, default_nature)
        if problems:
            bad += 1
            for p in problems:
                print(f"{rpath.name}:{i} ({r.get('id', '?') if isinstance(r, dict) else '?'}): {p}")
    print(f"{total} rating line(s), {bad} with problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
