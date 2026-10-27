"""The rule sheet (RULES.md) as code: annual value, exclusions, live status."""
from __future__ import annotations

from datetime import date

from .load import Line, Room

CADENCE_FACTOR = {"monthly": 12, "quarterly": 4, "annual": 1}

# Clearly not recurring. Anything else with a recurring cadence is treated as recurring;
# unrecognised types with no usable cadence get excluded in exclusion_reason.
NON_RECURRING = {"one_time", "usage", "overage", "once"}


def annual_value(line: Line) -> float | None:
    """Rule 5. None when the room does not give us enough to annualise (rule 1)."""
    if line.price is None:
        return None
    if line.cadence == "term":
        if not line.term_months or line.term_months <= 0:
            return None
        return line.price * 12 / line.term_months
    factor = CADENCE_FACTOR.get(line.cadence)
    if factor is None:
        return None
    return line.price * factor


def is_recurring(line: Line) -> bool:
    """Rules 6 and 7."""
    if line.line_type in NON_RECURRING:
        return False
    if line.line_type in {"recurring", "usage_minimum"}:
        return True
    # unrecognised type: still recurring if the cadence looks like a recurring charge
    return line.cadence in CADENCE_FACTOR or line.cadence == "term"


def superseded_ids(room: Room) -> set[str]:
    return {l.supersedes for l in room.lines if l.supersedes}


def exclusion_reason(line: Line, room: Room, as_of: date) -> str | None:
    """Why a line is not contracted recurring value at as-of, or None if it is (rules 6–10)."""
    if not is_recurring(line):
        if line.line_type in {"usage", "overage"}:
            return "usage/overage is not recurring value (rule 7)"
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
    """Rules 11–13: 'live', 'not_live' or 'unknown'.

    Contract start / signature alone are not evidence (rule 11). The inherited
    code treated a past start date as live when the activation log was missing;
    that disagrees with the rule sheet, so it is gone.
    """
    # Dated evidence that service has not started yet → clearly not live.
    if line.start and line.start > as_of:
        return "not_live"

    events = room.go_live.get(line.line_id, [])
    evidenced = [d for _, d in events if d and d <= as_of]

    # Multi-site, single price: any shortfall in live sites → unknown dollars (rule 12).
    if line.sites > 1:
        if len(evidenced) == 0:
            # no evidence at all — could still be wholly not-live, but we lack proof either way
            # unless every site has a future live date
            future_only = [d for _, d in events if d and d > as_of]
            if events and len(future_only) == len(events):
                return "not_live"
            return "unknown"
        if len(evidenced) < line.sites:
            return "unknown"
        return "live"

    if evidenced:
        return "live"

    # Amendment continuing a line that was already live: the go-live evidence sits on
    # the superseded id. Count that as evidence for the governing line (decision D2).
    if line.supersedes:
        pred = next((l for l in room.lines if l.line_id == line.supersedes), None)
        if pred is not None and live_status(pred, room, as_of) == "live":
            return "live"

    # Future-dated activation rows with nothing on or before as-of → not live.
    if events and all(d is None or d > as_of for _, d in events):
        return "not_live"

    # Signed, in-term, but no activation evidence → unknown, not live (rule 11).
    return "unknown"
