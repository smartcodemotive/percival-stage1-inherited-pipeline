"""The rule sheet (RULES.md) as code: annual value, contract status and live status of a line."""
from datetime import date

from .load import Line, Room

CADENCE_FACTOR = {"monthly": 12, "quarterly": 4, "annual": 1}


def annual_value(line: Line) -> float | None:
    """Rule 5: annual recurring amount. None when the price is not in the room (rule 1)."""
    if line.price is None:
        return None
    if line.cadence == "term":
        return line.price * 12 / line.term_months
    return line.price * CADENCE_FACTOR[line.cadence]


def is_recurring(line: Line) -> bool:
    """Rules 6 and 7: one-time fees are never recurring value."""
    return line.line_type != "one_time"


def superseded_ids(room: Room) -> set[str]:
    return {l.supersedes for l in room.lines if l.supersedes}


def exclusion_reason(line: Line, room: Room, as_of: date) -> str | None:
    """Why a line is not contracted recurring value at the as-of date, or None if it is (rules 6-10)."""
    if not is_recurring(line):
        return "one-time fee (rule 6)"
    if line.signed is None:
        return "unsigned pipeline (rule 9)"
    if line.signed > as_of:
        return "signed after the as-of date (rule 9)"
    if line.line_id in superseded_ids(room):
        return "superseded by an amendment (rule 8)"
    if line.cancel_effective and line.cancel_effective <= as_of:
        return "cancelled (rule 9)"
    if line.end and line.end < as_of:
        return "term ended before the as-of date, no renewal in the room"
    return None


def live_status(line: Line, room: Room, as_of: date) -> str:
    """Rules 11-13: 'live', 'not_live' or 'unknown'."""
    if line.start and line.start > as_of:
        return "not_live"
    evidenced = [d for _, d in room.go_live.get(line.line_id, []) if d and d <= as_of]
    if line.sites > 1 and len(evidenced) < line.sites:
        return "unknown"
    if evidenced:
        return "live"
    if line.supersedes:
        predecessor = next((l for l in room.lines if l.line_id == line.supersedes), None)
        if predecessor and live_status(predecessor, room, as_of) == "live":
            return "live"
    # Activation logs in data rooms are often incomplete, so a signed line that is past its
    # start date with no activation record is treated as live.
    if line.start and line.start <= as_of:
        return "live"
    return "unknown"
