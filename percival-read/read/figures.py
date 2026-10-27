"""Build the Read figures (OUTPUT.md) from a loaded room."""
from __future__ import annotations

from datetime import date

from .load import Line, Room, parse_number
from .rules import annual_value, exclusion_reason, live_status


def _figure(known: float, unknown: dict[str, float | None]) -> dict:
    """Figure from a known sum and unknown lines (id -> max addable, or None if unbounded)."""
    if not unknown:
        return {
            "status": "complete",
            "value": known,
            "known": known,
            "low": known,
            "high": known,
            "unknown_lines": [],
        }
    if all(v is not None for v in unknown.values()):
        return {
            "status": "range",
            "value": None,
            "known": known,
            "low": known,
            "high": known + sum(unknown.values()),
            "unknown_lines": sorted(unknown),
        }
    return {
        "status": "scoped",
        "value": None,
        "known": known,
        "low": None,
        "high": None,
        "unknown_lines": sorted(unknown),
    }


def customer_key(account_id: str, room: Room) -> str:
    """Economic customer (rule 14): parent if mapped, else the account."""
    account = room.accounts.get(account_id)
    if account and account.parent_id:
        return account.parent_id
    return account_id or "UNMAPPED"


def _mapped_keys(room: Room) -> set[str]:
    keys = set()
    for a in room.accounts.values():
        keys.add(a.parent_id or a.account_id)
        keys.add(a.account_id)
    return keys


def _citation_check(room: Room, contracted: list[Line]) -> dict:
    """Re-read price cells from the contracts file and compare to what we used."""
    try:
        from .load import _rows, _pick  # local import to reuse parser

        path = room.source_files.get("contracts")
        if path is None or not path.exists():
            return {"status": "not possible", "reason": "contracts source path missing"}
        by_id = {}
        for r in _rows(path):
            lid = _pick(r, "line_id", "lineid", "line", "id")
            if lid:
                by_id[lid] = r
        mismatches = []
        for line in contracted:
            raw = by_id.get(line.line_id)
            if raw is None:
                mismatches.append(f"{line.line_id}: not found on re-read")
                continue
            cell = _pick(raw, "price", "amount", "fee", "arr", "acv", "value", "annual_price")
            parsed = parse_number(cell)
            if parsed != line.price:
                mismatches.append(f"{line.line_id}: used {line.price!r}, source parses to {parsed!r}")
        if mismatches:
            return {"status": "fail", "reason": "; ".join(mismatches[:8])}
        return {"status": "pass", "reason": f"re-read {len(contracted)} contracted prices from {path.name}"}
    except Exception as exc:  # noqa: BLE001 — check must not crash the run
        return {"status": "not possible", "reason": f"citation check error: {exc}"}


def _completeness_check(
    room: Room,
    contracted: list[Line],
    excluded: list[dict],
) -> dict:
    """Reconcile used + excluded against the full line population (rule sheet)."""
    pop = {l.line_id for l in room.lines}
    for i, u in enumerate(room.unparsed):
        pop.add(u.get("raw", {}).get("line_id") or f"UNPARSED-{i}")

    used = {l.line_id for l in contracted}
    excl = {e["line_id"] for e in excluded}
    union = used | excl
    missing = pop - union
    overlap = used & excl

    # totals: every population line should appear once
    if overlap:
        return {
            "status": "fail",
            "reason": f"lines both used and excluded: {sorted(overlap)}",
        }
    if missing:
        return {
            "status": "fail",
            "reason": f"population lines neither used nor excluded: {sorted(missing)}",
        }
    if len(union) != len(pop):
        return {
            "status": "fail",
            "reason": f"set sizes differ: population {len(pop)}, used+excluded {len(union)}",
        }
    return {
        "status": "pass",
        "reason": f"{len(used)} used, {len(excl)} excluded, population {len(pop)}",
    }


def _top3_share(live_total: dict, by_customer: dict) -> dict:
    """Rule 16: only publish a point share when the live total is complete."""
    if live_total["status"] != "complete" or not live_total["known"]:
        return {
            "status": "scoped",
            "value": None,
            "known": None,
            "low": None,
            "high": None,
            "unknown_lines": list(live_total.get("unknown_lines") or []),
            "reason": "live total is not complete; point share withheld (rule 16)",
        }

    ranked = sorted(
        (
            (f["value"] if f["status"] == "complete" and f["value"] is not None else f["known"]) or 0.0
            for f in by_customer.values()
        ),
        reverse=True,
    )
    share = 100.0 * sum(ranked[:3]) / live_total["known"]
    return {
        "status": "complete",
        "value": round(share, 2),
        "known": None,
        "low": round(share, 2),
        "high": round(share, 2),
        "unknown_lines": [],
    }


def _records(
    room: Room,
    as_of: date,
    contracted: list[Line],
    excluded: list[dict],
    value: dict[str, float | None],
    status: dict[str, str],
    figures: dict,
) -> list[dict]:
    """Calculation records required by the rule sheet."""
    citation = _citation_check(room, contracted)
    completeness = _completeness_check(room, contracted, excluded)

    def inputs_for(line_ids: list[str]) -> list[dict]:
        out = []
        for lid in line_ids:
            out.append(
                {
                    "line_id": lid,
                    "annual_value": value.get(lid),
                    "live_status": status.get(lid),
                    "contribution": value.get(lid),
                }
            )
        return out

    contracted_ids = [l.line_id for l in contracted]
    live_ids = [l.line_id for l in contracted if status[l.line_id] == "live"]
    future_ids = [l.line_id for l in contracted if status[l.line_id] == "not_live"]
    unknown_ids = [l.line_id for l in contracted if status[l.line_id] == "unknown"]

    common_checks = {"citation": citation, "completeness": completeness}

    return [
        {
            "figure": "contracted",
            "method": "sum of annual_value over contracted recurring lines (rules 5–10)",
            "rules_applied": [1, 2, 5, 6, 7, 8, 9, 10],
            "inputs": inputs_for(contracted_ids),
            "excluded": excluded,
            "result": figures["contracted"],
            "checks": common_checks,
        },
        {
            "figure": "future_start",
            "method": "contracted lines with live_status not_live (rule 10)",
            "rules_applied": [10, 13],
            "inputs": inputs_for(future_ids),
            "excluded": [],
            "result": figures["future_start"],
            "checks": common_checks,
        },
        {
            "figure": "live",
            "method": (
                "contracted lines with go-live evidence on/before as-of; "
                "partly-live multi-site left unknown (rules 11–13)"
            ),
            "rules_applied": [11, 12, 13],
            "inputs": inputs_for(live_ids + unknown_ids),
            "excluded": [],
            "result": figures["live"],
            "checks": common_checks,
            "as_of": as_of.isoformat(),
        },
        {
            "figure": "top3_share_pct",
            "method": "sum of three largest live-by-customer values / live total (rules 14–16)",
            "rules_applied": [14, 15, 16],
            "inputs": inputs_for(live_ids + unknown_ids),
            "excluded": [],
            "result": figures["top3_share_pct"],
            "checks": common_checks,
        },
    ]


def build(room: Room, as_of: date) -> dict:
    excluded: list[dict] = []
    contracted: list[Line] = []

    for line in room.lines:
        reason = exclusion_reason(line, room, as_of)
        if reason:
            excluded.append({"line_id": line.line_id, "reason": reason})
        else:
            contracted.append(line)

    # Unparsed source rows stay visible (rule 4).
    for i, u in enumerate(room.unparsed):
        excluded.append(
            {
                "line_id": u.get("raw", {}).get("line_id") or f"UNPARSED-{i}",
                "reason": f"unparsed row ({u.get('reason', 'unknown')})",
            }
        )

    status = {l.line_id: live_status(l, room, as_of) for l in contracted}
    value = {l.line_id: annual_value(l) for l in contracted}

    def known(lines: list[Line]) -> float:
        return sum(value[l.line_id] for l in lines if value[l.line_id] is not None)

    def unpriced(lines: list[Line]) -> dict[str, float | None]:
        return {l.line_id: None for l in lines if value[l.line_id] is None}

    future = [l for l in contracted if status[l.line_id] == "not_live"]
    live = [l for l in contracted if status[l.line_id] == "live"]
    unknown_live = [l for l in contracted if status[l.line_id] == "unknown"]

    def live_figure(lines_live: list[Line], lines_unknown: list[Line]) -> dict:
        unknown = unpriced(lines_live)
        # Unknown live-status lines: bound by their annual value when we have one.
        unknown.update({l.line_id: value[l.line_id] for l in lines_unknown})
        return _figure(known(lines_live), unknown)

    customers = sorted({customer_key(l.account_id, room) for l in contracted})
    mapped = _mapped_keys(room)
    by_customer: dict = {}
    for key in customers:
        mine = [l for l in contracted if customer_key(l.account_id, room) == key]
        by_customer[key] = live_figure(
            [l for l in mine if l in live],
            [l for l in mine if l in unknown_live],
        )
        by_customer[key]["mapped"] = key in mapped

    live_total = live_figure(live, unknown_live)
    figures = {
        "contracted": _figure(known(contracted), unpriced(contracted)),
        "future_start": _figure(known(future), unpriced(future)),
        "live": live_total,
        "live_by_customer": by_customer,
        "top3_share_pct": _top3_share(live_total, by_customer),
    }

    return {
        "as_of": as_of.isoformat(),
        "currency": room.currency,
        "figures": figures,
        "lines": [
            {
                "line_id": l.line_id,
                "customer": customer_key(l.account_id, room),
                "annual_value": value[l.line_id],
                "live_status": status[l.line_id],
            }
            for l in contracted
        ],
        "excluded": excluded,
        "management_reported": {"total": room.management_total, "by_customer": room.management},
        "records": _records(room, as_of, contracted, excluded, value, status, figures),
    }
