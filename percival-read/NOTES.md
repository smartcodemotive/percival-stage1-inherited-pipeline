# Notes

## Hours

About **5 hours** end to end (read brief + room, chase the rule-sheet disagreements, fix
loader/rules/figures, tests, write-up). Split roughly:

| Block | ~time |
| --- | --- |
| Read RULES/OUTPUT, run inherited pipeline, diff vs reference | 45m |
| Hand-check room A lines (esp. L006, L018, L020, amendment) | 50m |
| Fix live_status + top-3 + records; retune tests | 1h 30m |
| Harden loader; messy-room tests; crash stub in run.py | 1h |
| DECISIONS / PREDICTION / NOTES, tidy README, AI session export | 55m |

Used Cursor (Composer) for the mechanical edits and test scaffolding. I did the rule calls
and the hand checks myself; see `ai-sessions/`.

## What I would not trust

**In the inherited code (and why it scared me for hidden rooms)**

- The start-date → live shortcut. Convenient on room A, forbidden by rule 11, and exactly the
  kind of thing that prints a clean number an investor will believe.
- Publishing top-3 as `complete` while live was already a range. Internally consistent with
  “share of known”, externally a point fact the output contract does not qualify.
- No calculation records. Hard to see what was in or out of a figure.
- Loader assumed one column layout and `float(cell)`. Fine for the sample room; brittle
  elsewhere. A crash on room 3 of N zeroes that room.

**In my own code**

- Column alias lists. Finite. A room that calls the price column `MRR_USD` (or similar) will
  scope everything unless I guessed that name — better than a wrong float, still a gap.
- Single-hop amendment inheritance (D2).
- Currency detection is string-sniffing, not a real FX policy.
- The share-range path I skipped: if a later pass needs a top-3 number on incomplete live, it
  needs careful work; I would not bolt it on in a hurry.
- `run.py`’s failure stub still exits 1 and leaves figures empty — correct for “do not invent”,
  but the investor tooling must treat that as a failed room.

**Reference eval**

`eval/run_eval.py` vs `reference.json` will disagree on purpose (L018, live.low, A10 usage
minimum, A11). I kept the eval script; I do not treat that percentage as a quality gate
anymore. `python -m unittest` is what I trust on room A.
