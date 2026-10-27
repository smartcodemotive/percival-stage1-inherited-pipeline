# Agent instructions (this assessment only)

You are helping me harden `percival-read` for unseen data rooms.

## Non-negotiables

- `RULES.md` wins over the inherited code, the README status blurb, and `eval/reference.json`.
- Prefer `unknown` / `scoped` / `range` over a plausible but unsupported number.
- Never use management ARR to fill a rebuilt figure.
- Do not remove or rename fields in `OUTPUT.md`. Adding fields (e.g. `records`) is fine.
- Keep it stdlib Python 3.10+. No new dependencies unless I ask.
- Every source row is used or excluded with a reason.

## How to work with me

- Propose the change and the rule it maps to before rewriting a file.
- When unsure, stop and list options — I will pick; we log it in `DECISIONS.md`.
- After edits: `python -m unittest discover -s tests -t .` and `python run.py`.
- Do not “fix” tests to match the old reference if the reference breaks a rule.

## Out of scope unless I say so

FX conversion, PDF parsing, writing up investor commentary, changing the hidden-room CLI.
