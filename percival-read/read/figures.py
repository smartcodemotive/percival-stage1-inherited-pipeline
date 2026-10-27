"""The Read's figures in the output contract (OUTPUT.md)."""
from datetime import date

from .load import Room
from .rules import annual_value, exclusion_reason, live_status


def _figure(known: float, unknown: dict[str, float | None]) -> dict:
    """A figure from its known sum and its unknown lines (line id -> most it could add, or None)."""
    if not unknown:
        return {"status": "complete", "value": known, "known": known, "low": known, "high": known,
                "unknown_lines": []}
    if all(v is not None for v in unknown.values()):
        return {"status": "range", "value": None, "known": known, "low": known,
                "high": known + sum(unknown.values()), "unknown_lines": sorted(unknown)}
    return {"status": "scoped", "value": None, "known": known, "low": None, "high": None,
            "unknown_lines": sorted(unknown)}


def customer_key(account_id: str, room: Room) -> str:
    """Economic customer (rule 14): the parent where one is mapped, else the account itself."""
    account = room.accounts.get(account_id)
    if account and account.parent_id:
        return account.parent_id
    return account_id


def build(room: Room, as_of: date) -> dict:
    excluded, contracted = [], []
    for line in room.lines:
        reason = exclusion_reason(line, room, as_of)
        if reason:
            excluded.append({"line_id": line.line_id, "reason": reason})
        else:
            contracted.append(line)

    status = {l.line_id: live_status(l, room, as_of) for l in contracted}
    value = {l.line_id: annual_value(l) for l in contracted}

    def known(lines):
        return sum(value[l.line_id] for l in lines if value[l.line_id] is not None)

    def unpriced(lines):
        return {l.line_id: None for l in lines if value[l.line_id] is None}

    future = [l for l in contracted if status[l.line_id] == "not_live"]
    live = [l for l in contracted if status[l.line_id] == "live"]
    unknown_live = [l for l in contracted if status[l.line_id] == "unknown"]

    def live_figure(lines_live, lines_unknown):
        unknown = unpriced(lines_live)
        unknown.update({l.line_id: value[l.line_id] for l in lines_unknown})
        return _figure(known(lines_live), unknown)

    customers = sorted({customer_key(l.account_id, room) for l in contracted})
    by_customer = {}
    for key in customers:
        mine = [l for l in contracted if customer_key(l.account_id, room) == key]
        by_customer[key] = live_figure([l for l in mine if l in live], [l for l in mine if l in unknown_live])
        by_customer[key]["mapped"] = key in {a.parent_id or a.account_id for a in room.accounts.values()}

    live_total = live_figure(live, unknown_live)
    ranked = sorted((f["known"] for f in by_customer.values()), reverse=True)
    # Share of the known live base; the live figure discloses its unknown lines separately.
    top3 = 100 * sum(ranked[:3]) / live_total["known"] if live_total["known"] else None

    return {
        "as_of": as_of.isoformat(),
        "currency": "USD",
        "figures": {
            "contracted": _figure(known(contracted), unpriced(contracted)),
            "future_start": _figure(known(future), unpriced(future)),
            "live": live_total,
            "live_by_customer": by_customer,
            "top3_share_pct": {"status": "complete", "value": round(top3, 2) if top3 is not None else None,
                               "known": None, "low": None, "high": None, "unknown_lines": []},
        },
        "lines": [
            {"line_id": l.line_id, "customer": customer_key(l.account_id, room), "annual_value": value[l.line_id],
             "live_status": status[l.line_id]}
            for l in contracted
        ],
        "excluded": excluded,
        "management_reported": {"total": room.management_total, "by_customer": room.management},
    }
