"""Normalize a raw location string + detect remote/hybrid and Vancouver metro.

``location_normalized`` is one of: Vancouver | Remote | Hybrid | Other | Unknown.
``is_remote`` is True for fully-remote roles (used by the commute estimator).
Metro detection drives the out-of-metro disqualifier in the scorer.
"""
from __future__ import annotations

import re

# Cities/areas that count as "Vancouver metro" for this search — the full
# Metro Vancouver Regional District, not just the City of Vancouver, since
# these are all genuinely commutable even if some rides are long.
_METRO = [
    "vancouver", "burnaby", "new westminster", "new west", "richmond",
    "north vancouver", "west vancouver", "coquitlam", "port moody",
    "port coquitlam", "surrey", "delta", "tsawwassen", "ladner",
    "langley", "maple ridge", "pitt meadows", "white rock",
    "bowen island", "anmore", "belcarra", "lions bay",
    "metro vancouver", "lower mainland",
]
_REMOTE = ["remote", "work from home", "wfh", "anywhere", "fully remote"]
_HYBRID = ["hybrid", "flexible location", "partially remote"]


def _has(text: str, terms: list[str]) -> bool:
    return any(t in text for t in terms)


def normalize_location(location: str, description: str = "") -> tuple[str, bool]:
    loc = (location or "").lower().strip()
    desc = (description or "").lower()

    is_remote = _has(loc, _REMOTE) or "fully remote" in desc
    is_hybrid = _has(loc, _HYBRID) or "hybrid" in desc

    if not loc:
        return "Unknown", is_remote

    in_metro = _has(loc, _METRO)

    if is_remote and not in_metro:
        return "Remote", True
    if is_hybrid:
        return "Hybrid", False
    if "vancouver" in loc:
        return "Vancouver", is_remote
    if in_metro:
        return "Vancouver", is_remote  # treat metro municipalities as Vancouver-area
    if is_remote:
        return "Remote", True
    return "Other", is_remote
