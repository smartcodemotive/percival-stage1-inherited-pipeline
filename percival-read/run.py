"""Run the Read on a room and write out/results.json.

    python run.py                      # room/ at the default as-of date
    python run.py --room PATH --as-of 2026-06-30 --out PATH
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import date
from pathlib import Path

from read.figures import build
from read.load import load_room

HERE = Path(__file__).parent


def _fmt_money(n: float | None) -> str:
    if n is None:
        return "n/a"
    return f"{n:,.0f}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--room", type=Path, default=HERE / "room")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date(2026, 6, 30))
    parser.add_argument("--out", type=Path, default=HERE / "out")
    args = parser.parse_args()

    try:
        room = load_room(args.room)
        results = build(room, args.as_of)
    except Exception as exc:  # noqa: BLE001
        # A crash leaves the investor with nothing. Write a stub so the failure
        # is visible, then exit non-zero.
        args.out.mkdir(parents=True, exist_ok=True)
        stub = {
            "as_of": args.as_of.isoformat(),
            "currency": "USD",
            "figures": {},
            "lines": [],
            "excluded": [],
            "management_reported": {"total": None, "by_customer": {}},
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        (args.out / "results.json").write_text(json.dumps(stub, indent=2), encoding="utf-8")
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    f = results["figures"]
    c, live, top = f["contracted"], f["live"], f["top3_share_pct"]
    print(f"Currency: {results['currency']}")
    print(f"Contracted: {c['status']}, known {_fmt_money(c.get('known'))}")
    print(
        f"Live: {live['status']}, "
        f"{_fmt_money(live.get('low'))} to {_fmt_money(live.get('high'))} "
        f"(known {_fmt_money(live.get('known'))})"
    )
    if top.get("value") is not None:
        print(f"Top-3 share: {top['value']}%")
    else:
        print(f"Top-3 share: {top['status']} ({top.get('reason', 'n/a')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
