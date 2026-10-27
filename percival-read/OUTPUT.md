# Output contract: out/results.json

The investor tooling reads this file as it is. Do not change its shape. You may add fields;
do not remove or rename any. The calculation records `RULES.md` asks for go in a field you add,
for example `records`.

```
{
  "as_of": "2026-06-30",
  "currency": "USD",
  "figures": {
    "contracted":       <figure>,   contracted recurring value
    "future_start":     <figure>,   of which signed but starting after the as-of date
    "live":             <figure>,   live recurring value
    "live_by_customer": { "<customer key>": <figure> plus "mapped": true|false },
    "top3_share_pct":   <figure>    top-3 customers' share of live value, in percent
  },
  "lines":    [ { "line_id", "customer", "annual_value", "live_status" } ],
  "excluded": [ { "line_id", "reason" } ],
  "management_reported": { "total", "by_customer" }
}
```

A **figure** is:

| Field | Meaning |
| --- | --- |
| `status` | `complete`: the room supports one value. `range`: the room bounds it. `scoped`: some of it cannot be valued or bounded |
| `value` | The value when `complete`, else null |
| `known` | The sum over what can be valued (null for a share) |
| `low`, `high` | The bounds when `complete` or `range`, else null |
| `unknown_lines` | The line ids that make it incomplete |

A customer key is the parent id where an account has a parent, else the account id.

What the investor sees is generated from this file without editing. A `complete` figure is
printed as a fact.
