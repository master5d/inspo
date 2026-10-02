"""Re-check every link in catalog.jsonl and record the result in place.

Usage:  python scripts/check_links.py [--catalog catalog.jsonl] [--only-status dead,unchecked]

status:
  alive      - answers 2xx/3xx on the same site
  redirected - lands on another site (final_url recorded; the link itself is kept)
  moved      - a deep link that now lands on another site's front page: the page is gone
  blocked    - 401/403/429/503: the site refuses robots, we could not verify (NOT the same as alive)
  (a hand-set `pin` overrides the verdict; the robot's answer is kept in `observed`)
  dead       - 404/410, other errors, or unreachable
For dead and moved links the closest Wayback Machine snapshot (to the date the link was saved)
is stored in `wayback`. A link that only switched http->https or www is updated in place.
Exit code: 0 - every link got a verdict; 3 - some checks could not run at all (network down).
"""
import argparse, concurrent.futures as cf, json, socket, ssl, sys, urllib.error, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126 Safari/537.36 inspo-linkcheck",
      "Accept": "text/html,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.8"}
CTX = ssl.create_default_context()


def _host(u):
    h = (urllib.parse.urlsplit(u).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def _path(u):
    return urllib.parse.urlsplit(u).path.rstrip("/")


def fetch(url):
    try:
        req = urllib.request.Request(url, headers=UA, method="GET")
        with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
            r.read(2048)
            return r.status, r.geturl(), None
    except urllib.error.HTTPError as e:
        return e.code, url, None
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, ssl.SSLError, OSError, ValueError) as e:
        return None, None, f"{type(e).__name__}: {str(getattr(e, 'reason', e))[:120]}"


def _wayback_once(url, ts):
    params = {"url": url}
    if ts:
        params["timestamp"] = ts
    q = "https://archive.org/wayback/available?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(q, headers=UA), timeout=25, context=CTX) as r:
            snap = json.load(r).get("archived_snapshots", {}).get("closest") or {}
            u = snap.get("url") if snap.get("available") else None
            return u.replace("http://web.archive.org/", "https://web.archive.org/", 1) if u else None
    except Exception:  # noqa: BLE001 - archive.org is best effort
        return None


def _wayback_cdx(url, ts):
    """The CDX index is the ground truth; the availability API is a cache in front of it."""
    params = {"url": url, "output": "json", "filter": "statuscode:200", "limit": "1",
              "closest": ts or "2017", "sort": "closest", "fl": "timestamp,original"}
    q = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(q, headers=UA), timeout=40, context=CTX) as r:
            rows = json.load(r)
    except Exception:  # noqa: BLE001
        return None
    if len(rows) < 2:
        return None
    stamp, original = rows[1]
    return f"https://web.archive.org/web/{stamp}/{original}"


def wayback(url, added):
    """Closest snapshot. The availability API answers empty for pages that ARE archived
    (2026-10-02: 5 of 5 "no copy" verdicts were wrong — four on retry, be-at.tv only in CDX),
    so a miss there is not absence: fall back to the CDX index before saying "no copy"."""
    ts = (added or "").replace("-", "") or "2017"
    variants = list(dict.fromkeys([url, url.replace("%20", "").rstrip("/")]))
    for u in variants:
        for t in (ts, None):
            w = _wayback_once(u, t)
            if w:
                return w
    for u in variants:
        w = _wayback_cdx(u, ts)
        if w:
            return w
    return None


def verdict(row):
    code, final, err = fetch(row["url"])
    out = {"checked": date.today().isoformat(), "http": code}
    if code is None:
        out["status"], out["error"] = "dead", err
    elif code in (401, 403, 429, 503):
        out["status"] = "blocked"
    elif code >= 400:
        out["status"] = "dead"
    elif final and _host(final) != _host(row["url"]):
        deep = bool(_path(row["url"]))
        out["status"] = "moved" if deep and not _path(final) else "redirected"
        out["final_url"] = final
    else:
        out["status"] = "alive"
        if final and final != row["url"] and _path(final) == _path(row["url"]):
            out["url"] = final  # http->https / www only: same page
    # A human verdict wins over the robot's: `pin` is set by hand (with `note`) when the
    # robot's view is known to be wrong — e.g. a site that sends robots to a login wall,
    # or a redirect to a page that no longer has the content. The observed answer is kept.
    if row.get("pin"):
        out["observed"] = out["status"]
        out["status"] = row["pin"]
    if out["status"] in ("dead", "moved"):
        out["wayback"] = row.get("wayback") or wayback(row["url"], row.get("added"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="catalog.jsonl")
    ap.add_argument("--only-status", default="")
    a = ap.parse_args()
    path = Path(a.catalog)
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    only = {s for s in a.only_status.split(",") if s}
    todo = [r for r in rows if not only or r.get("status") in only]
    with cf.ThreadPoolExecutor(16) as ex:
        results = list(ex.map(verdict, todo))
    for r, upd in zip(todo, results):
        for k in ("final_url", "wayback", "error", "observed"):
            r.pop(k, None)
        r.update(upd)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    c = Counter(r["status"] for r in rows)
    print("checked", len(todo), "|", dict(c.most_common()), "| wayback found",
          sum(1 for r in rows if r.get("wayback")), "of", c["dead"] + c["moved"])
    if all(r.get("http") is None for r in todo) and todo:
        print("NOT CHECKED: no link answered at all - network down?")
        sys.exit(3)


if __name__ == "__main__":
    main()
