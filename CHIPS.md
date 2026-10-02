# Rating chips

Every link can be rated with a handful of chips. A rating is one line in `ratings.jsonl`
(append-only: the last line for an `id` wins), keyed by the link's `id` in `catalog.jsonl`.

```json
{"id": "andygilmore-3f9a1c", "ts": "2026-10-02T18:00:00Z",
 "verdict": "take", "why": "one colour field carries the whole composition",
 "dims": ["color/light", "form/proportion"],
 "poles": {"air-density": "air", "grid-break": "break"},
 "roles": ["reference", "source"], "star": true}
```

## 1. Verdict — exactly one

| chip | value | needs `why` |
|---|---|---|
| 🔥 core | `core` — a reference I return to | yes |
| ✅ take | `take` — something here is worth carrying over | yes |
| 👀 watch | `watch` — interesting, undecided | no |
| 🧊 archive | `archive` — kept for the record, no longer a reference | no |
| ✕ pass | `reject` — not my direction | yes |

`why` is one line, a judgement with a reason ("one colour field carries the whole
composition"), not a label ("nice colours").

## 2. What is strong here — up to three

`form/proportion` · `color/light` · `type/letter` · `rhythm/space` · `material/texture` ·
`motion/time` · `mood/narrative` · `contrast/hierarchy`

## 3. Poles — optional, pick a side

| pair | sides |
|---|---|
| `air-density` | `air` ↔ `density` |
| `grid-break` | `grid` ↔ `break` |
| `hand-machine` | `hand` ↔ `machine` |
| `warm-cold` | `warm` ↔ `cold` |
| `quiet-loud` | `quiet` ↔ `loud` |
| `organic-geometric` | `organic` ↔ `geometric` |
| `sacred-utilitarian` | `sacred` ↔ `utilitarian` |
| `retro-future` | `retro` ↔ `future` |
| `minimal-excess` | `minimal` ↔ `excess` |
| `single-collage` | `single idea` ↔ `collage` |

Poles are the raw material of a taste direction: a pair that keeps landing on the same
side across many ratings says where the work wants to go, and what it refuses.

## 4. Role — any number

`reference` (look at it) · `tool` (make with it) · `source` (check it regularly for new
work) · `learn` · `community` · `shop`

## 5. Showcase

⭐ `star: true` — recommended to colleagues; starred links float to the top of their section.

## How ratings are used outside this repo

This catalog doubles as the input of a personal design lab. There, ratings are consumed
one way only, catalog → lab:

- a verdict with `why` (`core`, `take`, `reject`) becomes an entry in the lab's taste ledger
  (`source.kind: catalog`, `source.ref: <id>`, the axis as medium, `dims` as dimensions);
- a pole pair that leans one way in at least 80% of at least 10 ratings is proposed as a line
  of the lab's taste vector, in the form "<side> — refusing <other side>"; the line is
  written into the vector by the owner, never automatically;
- links with the `source` role join the list of sources the lab revisits weekly;
- the whole catalog is indexed into the lab's knowledge base.
