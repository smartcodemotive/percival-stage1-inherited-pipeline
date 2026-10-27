"""Load a data room's CSV exports into typed records.

Rooms are expected to have the same four files. Column names, date formats and
number formats vary in practice, so parsing here is deliberately loose. What we
cannot parse cleanly still shows up as a row — see parse_warnings / bad lines.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import date, datetime
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
    # original raw cells, for the citation check
    raw: dict[str, str] = field(default_factory=dict, hash=False, compare=False)


@dataclass(frozen=True)
class Account:
    account_id: str
    legal_name: str
    parent_id: str | None
    parent_name: str | None


@dataclass
class Room:
    lines: list[Line]
    go_live: dict[str, list[tuple[str, date]]]
    accounts: dict[str, Account]
    management: dict[str, float]
    management_total: float | None
    currency: str = "USD"
    # rows we saw but could not turn into a Line; still part of the population
    unparsed: list[dict] = field(default_factory=list)
    source_files: dict[str, Path] = field(default_factory=dict)


# --- column aliases (lowered, stripped of non-alphanumerics) -----------------

def _norm_key(k: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (k or "").lower())


def _pick(row: dict[str, str], *aliases: str, default: str = "") -> str:
    """Look up a cell by any of several alias names."""
    normed = {_norm_key(k): v for k, v in row.items()}
    for a in aliases:
        v = normed.get(_norm_key(a))
        if v is not None and str(v).strip() != "":
            return str(v).strip()
    # try exact-normalized match against alias list already done; fall back
    for a in aliases:
        if _norm_key(a) in normed and normed[_norm_key(a)] == "":
            return ""
    return default


def _rows(path: Path) -> list[dict[str, str]]:
    # utf-8-sig handles Excel's BOM; if that fails, try latin-1 rather than crash
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")
    return [
        {k: (v or "").strip() for k, v in row.items() if k is not None}
        for row in csv.DictReader(text.splitlines())
    ]


def parse_date(value: str) -> date | None:
    if value is None:
        return None
    value = str(value).strip()
    if not value or value.lower() in {"na", "n/a", "none", "null", "-"}:
        return None
    # ISO first
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y", "%d-%b-%y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_number(value: str) -> float | None:
    """Parse a money-ish cell. Returns None for blank / unknown — never zero-fills."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"na", "n/a", "none", "null", "-", "tbd", "see order form"}:
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(" ", "").replace("£", "").replace("€", "").replace("¥", "")
    s = s.replace("USD", "").replace("usd", "").replace("GBP", "").replace("EUR", "")
    s = s.replace("$", "")
    # 1,234.56 vs 1.234,56
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s and "." not in s:
        # "15000" style with thousand sep, or decimal comma. Heuristic: 3 digits
        # after the comma → thousand sep; else decimal.
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) == 3 and parts[0].isdigit():
            s = "".join(parts)
        else:
            s = s.replace(",", ".")
    try:
        n = float(s)
    except ValueError:
        return None
    return -n if neg else n


def _infer_currency(folder: Path, contract_rows: list[dict[str, str]]) -> str:
    """Best-effort currency. We do not invent FX; we only label what the room shows."""
    for path_name in ("contracts.csv", "management_arr_summary.csv"):
        p = folder / path_name
        if not p.exists():
            continue
        head = p.read_text(encoding="utf-8-sig", errors="replace")[:400].lower()
        if "gbp" in head or "£" in head:
            return "GBP"
        if "eur" in head or "€" in head:
            return "EUR"
    for r in contract_rows[:5]:
        joined = " ".join(r.values()).lower()
        if "£" in joined or "gbp" in joined:
            return "GBP"
        if "€" in joined or "eur" in joined:
            return "EUR"
    return "USD"


def _cadence(raw: str) -> str:
    s = (raw or "").strip().lower().replace("-", "").replace(" ", "")
    aliases = {
        "monthly": "monthly",
        "month": "monthly",
        "mo": "monthly",
        "permonth": "monthly",
        "quarterly": "quarterly",
        "quarter": "quarterly",
        "qtr": "quarterly",
        "annual": "annual",
        "annually": "annual",
        "yearly": "annual",
        "year": "annual",
        "pa": "annual",
        "peryear": "annual",
        "term": "term",
        "fixedterm": "term",
        "once": "once",
        "oneoff": "once",
        "onetime": "once",
    }
    return aliases.get(s, s or "")


def _line_type(raw: str) -> str:
    s = (raw or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "recurring": "recurring",
        "subscription": "recurring",
        "saas": "recurring",
        "licence": "recurring",
        "license": "recurring",
        "one_time": "one_time",
        "onetime": "one_time",
        "oneoff": "one_time",
        "setup": "one_time",
        "implementation": "one_time",
        "usage_minimum": "usage_minimum",
        "usageminimum": "usage_minimum",
        "minimum_commit": "usage_minimum",
        "min_commit": "usage_minimum",
        "usage": "usage",
        "overage": "usage",
        "consumption": "usage",
    }
    return aliases.get(s, s or "recurring")


def _find(folder: Path, *names: str) -> Path:
    """Find a room file by exact name, then by fuzzy stem match."""
    for n in names:
        p = folder / n
        if p.exists():
            return p
    # case-insensitive / partial
    lower = {p.name.lower(): p for p in folder.iterdir() if p.is_file()}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    stems = [n.split(".")[0].lower() for n in names]
    for fname, p in lower.items():
        stem = fname.rsplit(".", 1)[0]
        for s in stems:
            if s in stem or stem in s:
                return p
    raise FileNotFoundError(f"could not find any of {names} in {folder}")


def load_room(folder: Path) -> Room:
    folder = Path(folder)
    contracts_path = _find(folder, "contracts.csv", "contract.csv", "contract_lines.csv")
    go_live_path = _find(folder, "go_live.csv", "golive.csv", "activations.csv", "go-live.csv")
    customers_path = _find(folder, "customers.csv", "accounts.csv", "customer.csv")
    management_path = _find(
        folder, "management_arr_summary.csv", "management.csv", "arr_summary.csv", "management_arr.csv"
    )

    contract_rows = _rows(contracts_path)
    currency = _infer_currency(folder, contract_rows)

    lines: list[Line] = []
    unparsed: list[dict] = []
    for i, r in enumerate(contract_rows):
        line_id = _pick(r, "line_id", "lineid", "line", "id", "Line ID")
        if not line_id:
            unparsed.append({"row": i + 2, "reason": "missing line_id", "raw": r})
            continue
        term_raw = _pick(r, "term_months", "termmonths", "term", "term_month")
        sites_raw = _pick(r, "sites_in_scope", "sitesinscope", "sites", "site_count", default="1")
        try:
            term_months = int(float(term_raw)) if term_raw else None
        except ValueError:
            term_months = None
        try:
            sites = int(float(sites_raw)) if sites_raw else 1
        except ValueError:
            sites = 1
        lines.append(
            Line(
                line_id=line_id,
                contract_id=_pick(r, "contract_id", "contractid", "contract", "contract_no"),
                account_id=_pick(r, "account_id", "accountid", "account", "customer_id", "customerid"),
                product=_pick(r, "product", "product_name", "sku", "item"),
                line_type=_line_type(_pick(r, "line_type", "linetype", "type", "charge_type")),
                price=parse_number(_pick(r, "price", "amount", "fee", "arr", "acv", "value", "annual_price")),
                cadence=_cadence(_pick(r, "cadence", "billing_cadence", "frequency", "billing_period")),
                term_months=term_months,
                signed=parse_date(_pick(r, "signed_date", "signeddate", "signature_date", "signed")),
                start=parse_date(_pick(r, "start_date", "startdate", "service_start", "start")),
                end=parse_date(_pick(r, "end_date", "enddate", "end", "term_end")),
                supersedes=_pick(r, "supersedes_line_id", "supersedeslineid", "supersedes", "replaces") or None,
                cancel_effective=parse_date(
                    _pick(r, "cancel_effective_date", "canceleffectivedate", "cancelled_date", "cancel_date")
                ),
                sites=max(sites, 1),
                notes=_pick(r, "notes", "note", "comment"),
                raw=dict(r),
            )
        )

    go_live: dict[str, list[tuple[str, date]]] = {}
    for r in _rows(go_live_path):
        lid = _pick(r, "line_id", "lineid", "line")
        live = parse_date(_pick(r, "live_date", "livedate", "go_live_date", "activation_date", "date"))
        if not lid or not live:
            continue
        site = _pick(r, "site", "site_name", "location", default="")
        go_live.setdefault(lid, []).append((site, live))

    accounts: dict[str, Account] = {}
    for r in _rows(customers_path):
        aid = _pick(r, "account_id", "accountid", "account", "customer_id", "id")
        if not aid:
            continue
        accounts[aid] = Account(
            account_id=aid,
            legal_name=_pick(r, "legal_name", "legalname", "name", "customer", "account_name"),
            parent_id=_pick(r, "parent_id", "parentid", "parent") or None,
            parent_name=_pick(r, "parent_name", "parentname") or None,
        )

    management: dict[str, float] = {}
    management_total = None
    for r in _rows(management_path):
        customer = _pick(r, "customer", "name", "account", "legal_name")
        arr = parse_number(_pick(r, "reported_arr", "reportedarr", "arr", "amount", "value", "arr_usd"))
        if not customer or arr is None:
            continue
        if customer.lower().startswith("total"):
            management_total = arr
        else:
            management[customer] = arr

    return Room(
        lines=lines,
        go_live=go_live,
        accounts=accounts,
        management=management,
        management_total=management_total,
        currency=currency,
        unparsed=unparsed,
        source_files={
            "contracts": contracts_path,
            "go_live": go_live_path,
            "customers": customers_path,
            "management": management_path,
        },
    )
