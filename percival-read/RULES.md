# Rule sheet

These are the rules the numbers must follow. They are deliberately strict. Where a rule and
a plausible-looking shortcut disagree, the rule wins. Where the rules are silent, make a call
and record it in `DECISIONS.md`.

Figures are in US dollars and exclude tax. The as-of date is given when the pipeline runs; for the room you have it is **30 June 2026**.

## General

1. **Unknown is never zero.** A missing amount or an unresolved status stays unknown. It is
   shown, with the lines it affects. It is not filled in, estimated, averaged or spread.
2. **A subset is not the total.** A sum over the lines you could value is a *scoped* figure.
   It is labelled as scoped and it lists what it leaves out. It is not the company total and
   it is not automatically a lower bound.
3. **Reported and rebuilt figures stay apart.** A figure management states is *reported*,
   attributed to management, and never overwritten or used to fill a gap in a figure you
   rebuild from the contract lines.
4. **Nothing is dropped silently.** Every source row is either an input to a result or
   excluded with a reason. A row that cannot be mapped or parsed is still in the population.

## Annual recurring amount of a line

5. Monthly price × 12. Quarterly price × 4. Annual price × 1. A single fee for an n-month
   term is `fee × 12 / n`.
6. One-time fees are never annualized.
7. A usage minimum is recurring and annualizes on its own cadence. Usage above the minimum
   (overage) is not recurring value, whatever its history.
8. When an amendment supersedes a line, only the governing (latest) line counts. The
   superseded line does not add to its replacement.

## Contracted recurring value at the as-of date

9. A line counts as contracted when it is signed on or before the as-of date and has not
   been cancelled. A line with no signature is pipeline and is never recurring value.
10. A signed line that starts after the as-of date counts as contracted and is shown
    separately as *future-start*.

## Live recurring value at the as-of date

11. A line is live only when there is dated evidence that service commenced on or before the
    as-of date. A start date in the contract is not evidence. A signature is not evidence.
12. When a contract is partly live and its parts are not separately priced, report the count
    of live parts and leave the live dollars unknown. Never multiply the contract amount by
    the live fraction.
13. Each contracted line falls into exactly one of three groups: **live**, **not live**
    (evidenced, for example a future start), or **live status unknown**.

## Concentration

14. Concentration uses live recurring value by economic customer: accounts that share a
    parent are one customer. Their values are summed.
15. `share = customer value / total`. `rank = 1 + the number of strictly greater values`.
    `top-3 share = the three largest values / total`.
16. The total must be complete. If it is not, do not publish a point share. Either report the
    share as unavailable with the reason, or, if every unknown can be bounded, report a
    range and state the bounds. Say which you chose and why.

## The calculation record

Every result comes with a calculation record. A calculation record holds:

- the method and the rules it applied;
- the input rows, by `line_id`, with each row's contribution;
- the rows excluded, each with its reason;
- the result, labelled complete or scoped, with any unknowns listed;
- its checks, each reporting **pass**, **fail** or **not possible**, with the reason.

Two checks are required on every record:

- **Citation check.** Every input value, re-read from the source file, matches the value
  used.
- **Completeness check.** The rows used and excluded are reconciled against a population
  built independently of the rows the calculation picked. Compare the row sets and the
  totals, not only the counts. A check that cannot be run reports "not possible"; it does
  not report "pass".
