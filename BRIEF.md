# Percival engineering assessment: the inherited pipeline

Percival reads a company's data room for an investor and reports what the documents support.
Agents do much of the work, so most of our engineering is making sure a figure is right, and
honest about what the room does not support, before an investor relies on it.

Use any AI tools you like. We expect you to.

## The situation

You have inherited `percival-read/`. An AI coding agent built it last week. It computes
recurring-value figures from a data room's CSV exports under `RULES.md`, and writes them to
`out/results.json` in the shape in `OUTPUT.md`. Its README tells you where it stands.

After you submit, several more data rooms arrive, each from a different company. We will run
your pipeline on each of them ourselves, once:

```
python run.py --room <room> --as-of 2026-06-30 --out <folder>
```

The investor receives the figures it writes, unedited. You will never see those rooms. Each
has the same four files with the same purpose; their columns and values may differ in the
ways real exports differ: format, units, currency and naming. If a run crashes, the investor
receives nothing for that room.

## Your job

Make `percival-read` ready for those runs. `RULES.md` applies to every room. `OUTPUT.md` is
fixed: you may add fields, not remove or rename them.

How we judge the hidden runs. Each figure in `figures`, and each line in `lines`, is one of:

- **right**;
- **unknown**: marked unknown, scoped, or given as a wider range, where the room supported more;
- **wrong**: a number the room does not support.

**The bar is no wrong numbers.** A wrong number reaches an investor as a fact; an unknown
does not. Among submissions with no wrong numbers, more right ones rank higher. A crash
counts every item in that room as unknown.

## How to work

- **Do not ask us questions.** Where something is unclear, decide, and record it in
  `DECISIONS.md` with your reason in a sentence or two.
- **Aim for 4 to 6 hours.** Decide what matters most.
- Keep it in Python, 3.10 or later.

## What to send back

The repository, with:

1. Your changes, and the tests you rely on.
2. `DECISIONS.md`: what you decided where things were unclear, and what you chose not to do.
3. `PREDICTION.md`: how many wrong numbers you expect across the hidden runs, which figures
   you think most likely to be wrong, and what that rests on.
4. `NOTES.md`: the hours you spent, and what in the inherited code or your own you would not
   trust.
5. Your AI session transcripts, complete, as exported sessions or markdown, from fresh
   sessions used only for this task.
6. Your AI setup and instruction files as you used them (`AGENTS.md`, `CLAUDE.md`, rules,
   skills, prompts). Redact secrets.

## How we mark it

The hidden runs. How you established that your figures are right. How close your prediction
was to what happened. And, from your transcripts, how you directed and checked the AI.
