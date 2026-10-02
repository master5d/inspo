# Rating chips

Every link can be rated with a handful of chips. A rating is one line in `ratings.jsonl`
(append-only: the last line for an `id` wins), keyed by the link's `id` in `catalog.jsonl`.

```json
{"id": "andygilmore-3f9a1c", "ts": "2026-10-02T18:00:00Z", "nature": "taste",
 "verdict": "take", "why": "one colour field carries the whole composition",
 "dims": ["color/light", "form/proportion"],
 "poles": {"air-density": "air", "grid-break": "break"},
 "roles": ["reference", "sweep"], "star": true}
```

## 0. What is it — taste object or utility

The catalog holds two different things, and they are judged differently:

| chip | value | judged by |
|---|---|---|
| 🎨 Taste object | `taste` | how it is made — artists, galleries, sites, magazines |
| 🧰 Utility | `utility` | what it is for — generators, services, shops, calendars, feeds |

`catalog.jsonl` carries a default `nature` (utility for the kinds `tool`, `service`,
`shop`, `gear`, `course`; taste otherwise); a rating can override it. Only taste
verdicts say anything about taste, so only they ever leave this repository as taste.

## 1. Verdict — exactly one

**Taste object**

| chip | value | needs `why` |
|---|---|---|
| 🔥 Core | `core` — a reference I return to | yes |
| ✅ Take | `take` — something here is worth carrying over | yes |
| 👀 Watch | `watch` — interesting, undecided | no |
| 🧊 Archive | `archive` — kept for the record, no longer a reference | no |
| ✕ Pass | `reject` — not my direction | yes |

**Utility**

| chip | value | needs `why` |
|---|---|---|
| 🧰 Keep | `keep` — needed for work | yes: what it is for |
| 🧊 Archive | `archive` — kept for the record | no |
| ✕ Drop | `drop` — not needed | no |

`why` is one line. For a taste object it is a judgement with a reason ("one colour field
carries the whole composition"), not a label ("nice colours"). For a utility it says what
the thing is used for ("source of occasions for the content calendar").

## 2. What is strong here — taste objects only, up to three

`form/proportion` · `color/light` · `type/letter` · `rhythm/space` · `material/texture` ·
`motion/time` · `mood/narrative` · `contrast/hierarchy`

## 3. Poles — taste objects only, optional, pick a side

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

| role | value | applies to |
|---|---|---|
| 📚 Reference | `reference` — look at it | taste objects |
| 🔁 Taste sweep | `sweep` — revisit regularly for new work | taste objects |
| 🛠 Tool | `tool` — make with it | both |
| 📅 Content ideas | `ideas` — occasions and topics for content | both |
| 🎓 Learn | `learn` | both |
| 🧑‍🤝‍🧑 Community | `community` | both |
| 🛒 Shop | `shop` | both |

## 5. Showcase

⭐ `star: true` — recommended to colleagues; starred links float to the top of their section.

## How ratings are used outside this repo

This catalog doubles as the input of a personal design lab. There, ratings are consumed
one way only, catalog → lab:

- a **taste** verdict with `why` (`core`, `take`, `reject`) becomes an entry in the lab's taste
  ledger (`source.kind: catalog`, `source.ref: <id>`, the axis as medium, `dims` as
  dimensions). Utility ratings never do;
- a pole pair that leans one way in at least 80% of at least 10 ratings is proposed as a line
  of the lab's taste vector, in the form "<side> — refusing <other side>"; the line is
  written into the vector by the owner, never automatically;
- links with the `sweep` role join the list of sources the lab revisits weekly;
  links with the `ideas` role join the content-calendar sources;
- the whole catalog is indexed into the lab's knowledge base.
