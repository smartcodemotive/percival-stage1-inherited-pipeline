# Prediction — hidden rooms

## How many wrong numbers

I expect **0–2 wrong numbers across all hidden rooms**, and I am aiming at zero. If something
is wrong it is more likely a live/not-live call than an arithmetic one.

A crash would count everything in that room as unknown, not wrong. I spent more time on
“do not crash / do not invent” than on matching room A’s old reference.

## Figures most likely to be wrong

1. **`live` / per-customer live (amendments)** — Decision D2 (inherit go-live from the
   superseded line). If a room uses supersedes for a true restart with a gap in service, we
   may mark the new line live without fresh evidence. That would be a wrong “live” dollar
   figure.
2. **`live` (sparse activation logs)** — We now require dated go-live evidence. Rooms that
   only keep start dates and never log activation will show a lot of `unknown`. That is not
   “wrong”, but it will look thin next to management’s ARR table. The failure mode I worry
   about is the opposite: some other evidence column I did not map, so we leave a line
   unknown when the room actually supported live.
3. **`contracted` annual values** — Cadence / unit surprises (price already annual but
   cadence still says monthly; prices in thousands; fiscal “ARR” column mixed with fee).
   Alias list will not catch every label. Unpriced → scoped (safe). Mis-read unit → wrong.
4. **`top3_share_pct`** — Withheld whenever live is incomplete, so it should not be wrong; it
   will often be blank. If a room’s live figure comes out `complete` because we missed an
   unknown, the share could be wrong as a knock-on.

## What this rests on

- Room A, re-checked by hand for L001, L005/L004, L006, L012, L018, L020 against RULES.md
  (not against management).
- Unit tests on room A plus a messy-export fixture (aliases, `$1,500`, `£`, term fee with no
  term months, unsigned blank dates).
- Citation + completeness checks in `records` on every run.
- Explicit refusal to use management ARR to fill gaps.

I am least confident about rooms whose go-live file uses a shape I did not alias, and about
amendment chains deeper than one hop (we only walk the immediate predecessor).
