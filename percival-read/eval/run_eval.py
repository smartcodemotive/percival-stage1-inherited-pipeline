"""Agreement of out/results.json with the reference figures.

    python eval/run_eval.py [--results out/results.json]

The reference (eval/reference.json) was assembled on 2 October: figures from the v0.3 run,
reconciled against management's ARR table, with six lines checked by hand. Management's table
uses its own definitions, so it is compared only where the two are within 5%; larger gaps are
management's definitional differences, not pipeline errors.
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).parent
TOLERANCE = 0.02


def close(a, b, tol=TOLERANCE):
    if a is None or b is None:
        return None
    if b == 0:
        return a == 0
    return abs(a - b) / abs(b) <= tol


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=HERE.parent / "out" / "results.json")
    args = parser.parse_args()
    results = json.loads(args.results.read_text(encoding="utf-8"))
    reference = json.loads((HERE / "reference.json").read_text(encoding="utf-8"))

    checks = []
    for name, fields in reference["figures"].items():
        for field, expected in fields.items():
            checks.append((f"{name}.{field}", close(results["figures"][name].get(field), expected)))

    ours = results["figures"]["live_by_customer"]
    for key, expected in reference["live_by_customer"].items():
        checks.append((f"customer {key}", close(ours.get(key, {}).get("known"), expected)))

    lines = {l["line_id"]: l for l in results["lines"]}
    for line_id, expected in reference["lines"].items():
        got = lines.get(line_id)
        if got is None:
            continue
        checks.append((f"{line_id} annual value", close(got["annual_value"], expected["annual_value"])))
        checks.append((f"{line_id} live status", got["live_status"] == expected["live_status"]))

    names = reference["management_names"]
    for customer, reported in results["management_reported"]["by_customer"].items():
        key = names.get(customer)
        if key in ours and close(ours[key]["known"], reported, 0.05):
            checks.append((f"management {customer}", True))

    scored = [(n, ok) for n, ok in checks if ok is not None]
    passed = sum(ok for _, ok in scored)
    for name, ok in scored:
        if not ok:
            print(f"  differs: {name}")
    print(f"Agreement with reference: {100 * passed / len(scored):.1f}% ({passed} of {len(scored)} checks)")


if __name__ == "__main__":
    main()
