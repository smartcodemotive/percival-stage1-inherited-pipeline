"""Run the Read on a room and write out/results.json.

    python run.py                      # room/ at the default as-of date
    python run.py --room PATH --as-of 2026-06-30 --out PATH
"""
import argparse
import json
from datetime import date
from pathlib import Path

from read.figures import build
from read.load import load_room

HERE = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--room", type=Path, default=HERE / "room")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date(2026, 6, 30))
    parser.add_argument("--out", type=Path, default=HERE / "out")
    args = parser.parse_args()

    results = build(load_room(args.room), args.as_of)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    f = results["figures"]
    print(f"Contracted: {f['contracted']['status']}, known {f['contracted']['known']:,.0f}")
    print(f"Live: {f['live']['status']}, {f['live']['low']:,.0f} to {f['live']['high']:,.0f}")
    print(f"Top-3 share: {f['top3_share_pct']['value']}%")


if __name__ == "__main__":
    main()
