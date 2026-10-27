# Decisions

Things that were unclear, and what I chose. One or two sentences each.

## D1 — Contract start date is not go-live evidence

The inherited `live_status` treated a signed line past its start date as live when the
activation log had no row. That matches management for Pinecrest (L018) on room A, and the
old tests encoded it. Rule 11 says the opposite: a start date is not evidence. I removed the
fallback. L018 is `unknown`. I would rather leave $48k out of “live” than print it as fact.

## D2 — Amendments inherit go-live from the superseded line

L005 has no go-live row; L004 does. An amendment that supersedes a live line is continuing
service, not a new commencement. I count the predecessor’s evidence for the governing line.
If that is wrong on a later room (amendment that is really a restart), the line will read live
when it should not — flagged in PREDICTION.md.

## D3 — Top-3 share when live is incomplete

Rule 16 allows “unavailable” or a bounded range. I withhold a point share whenever live is
not `complete`, and I did not ship share-range maths. Getting the bounds wrong would put a
wrong percentage in front of an investor; blank is safer. Room A’s live figure is a range
(L006 partly live, L018 no evidence), so top-3 is scoped.

## D4 — Partly-live multi-site upper bound

For a single-fee multi-site line with only some sites live (L006), live dollars stay unknown
(rule 12). For the live *range* I still use the line’s full annual value as the high side and
$0 incremental as the low side. That is a bound on what the unknown line can add, not a claim
that the low is a company floor (rule 2).

## D5 — Non-USD rooms, no FX in the file

If the export looks like GBP/EUR I set `currency` accordingly and leave amounts as written. I
do not invent a rate. Labelling sterling as USD would be a wrong number; converting with a
guessed rate would also be wrong.

## D6 — Unrecognised column / number formats

Loader accepts a small set of aliases and common number/date shapes. If a price cell will not
parse, the line stays in the population with `annual_value = null` (scoped), not zero. If the
file is missing entirely, `run.py` writes a stub `results.json` with the error and exits 1 —
still better than a bare traceback with no file.

## D7 — What I chose not to do

- No FX table or external price lookup.
- No attempt to reconcile to management ARR inside the rebuilt figures (rule 3).
- No share-range optimiser for top-3.
- No schema guesser beyond the alias lists — if a room renames “price” to something I have
  not seen, those lines will be unpriced rather than guessed.
- Left `eval/reference.json` alone. It reflects the old (rule-breaking) behaviour and the
  pre-usage-minimum A10 figure. Tests are the source of truth for room A now.
