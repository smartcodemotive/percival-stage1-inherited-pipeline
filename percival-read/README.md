# percival-read

Computes the Read's recurring-value figures from a data room's CSV exports under `RULES.md`,
and writes them to `out/results.json` in the shape in `OUTPUT.md`.

```
python run.py                                  # room/ as of 2026-06-30
python run.py --room PATH --as-of 2026-06-30   # another room
python -m unittest discover -s tests -t .      # tests
python eval/run_eval.py                        # agreement with the reference
```

## Status (v0.4, 9 October)

- All tests pass.
- Agreement with the reference is 97.9% (47 of 48 checks). The one difference is Varga Mills,
  where the reference predates the usage-minimum line.
- Handles amendments, future-start lines, partly live multi-site contracts, missing prices,
  parent grouping and unmapped accounts.

## Layout

| Path | What |
| --- | --- |
| `read/load.py` | Reads the four CSV files into typed records |
| `read/rules.py` | The rule sheet as code: annual value, exclusions, live status |
| `read/figures.py` | Builds the figures in the output contract |
| `eval/` | The reference figures and the agreement check |
| `tests/` | Tests on room A |
