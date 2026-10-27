"""Load a data room's CSV exports into typed records."""
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Line:
    line_id: str
    contract_id: str
    account_id: str
    product: str
    line_type: str
    price: float | None
    cadence: str
    term_months: int | None
    signed: date | None
    start: date | None
    end: date | None
    supersedes: str | None
    cancel_effective: date | None
    sites: int
    notes: str


@dataclass(frozen=True)
class Account:
    account_id: str
    legal_name: str
    parent_id: str | None
    parent_name: str | None


@dataclass(frozen=True)
class Room:
    lines: list[Line]
    go_live: dict[str, list[tuple[str, date]]]
    accounts: dict[str, Account]
    management: dict[str, float]
    management_total: float | None


def _date(value: str) -> date | None:
    return date.fromisoformat(value) if value else None


def _number(value: str) -> float | None:
    return float(value) if value else None


def _rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def load_room(folder: Path) -> Room:
    folder = Path(folder)
    lines = [
        Line(
            line_id=r["line_id"],
            contract_id=r["contract_id"],
            account_id=r["account_id"],
            product=r["product"],
            line_type=r["line_type"],
            price=_number(r["price"]),
            cadence=r["cadence"],
            term_months=int(r["term_months"]) if r["term_months"] else None,
            signed=_date(r["signed_date"]),
            start=_date(r["start_date"]),
            end=_date(r["end_date"]),
            supersedes=r["supersedes_line_id"] or None,
            cancel_effective=_date(r["cancel_effective_date"]),
            sites=int(r["sites_in_scope"] or 1),
            notes=r["notes"],
        )
        for r in _rows(folder / "contracts.csv")
    ]

    go_live: dict[str, list[tuple[str, date]]] = {}
    for r in _rows(folder / "go_live.csv"):
        go_live.setdefault(r["line_id"], []).append((r["site"], _date(r["live_date"])))

    accounts = {
        r["account_id"]: Account(r["account_id"], r["legal_name"], r["parent_id"] or None, r["parent_name"] or None)
        for r in _rows(folder / "customers.csv")
    }

    management: dict[str, float] = {}
    management_total = None
    for r in _rows(folder / "management_arr_summary.csv"):
        if r["customer"].lower().startswith("total"):
            management_total = float(r["reported_arr"])
        else:
            management[r["customer"]] = float(r["reported_arr"])

    return Room(lines, go_live, accounts, management, management_total)
