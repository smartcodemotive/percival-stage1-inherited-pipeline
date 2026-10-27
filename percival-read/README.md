# percival-read

Computes the Read's recurring-value figures from a data room's CSV exports under `RULES.md`,
and writes them to `out/results.json` in the shape in `OUTPUT.md`.

```
python run.py                                  # room/ as of 2026-06-30
python run.py --room PATH --as-of 2026-06-30   # another room
python -m unittest discover -s tests -t .      # tests
python eval/run_eval.py                        # agreement with the (stale) reference
```

## Status (post-inheritance)

Inherited v0.4 matched its own tests and a reference that predated the usage-minimum line
and that treated contract start as go-live evidence. That disagreed with `RULES.md`.

Changes in this pass:

- Live status follows rule 11 (activation evidence required; start date is not enough).
- Top-3 share withheld when the live total is not complete (rule 16).
- Calculation `records` with citation + completeness checks.
- Loader tolerates common column aliases and number/date formats; missing prices stay
  unknown. `run.py` writes a stub result file instead of dying silently on a hard failure.
- Usage minimum (L020) kept as recurring.

Room A tests were updated to match the rule sheet. See `DECISIONS.md`.

## Layout

| Path | What |
| --- | --- |
| `read/load.py` | Reads the four CSV files into typed records |
| `read/rules.py` | The rule sheet as code: annual value, exclusions, live status |
| `read/figures.py` | Builds the figures in the output contract |
| `eval/` | Historical reference + agreement check (not the gate) |
| `tests/` | Room A + messy-export fixtures |
| `DECISIONS.md` / `PREDICTION.md` / `NOTES.md` | Assessment write-up |
| `ai-sessions/` | AI transcripts used on this task |
| `AGENTS.md` | Instructions given to the coding agent |
