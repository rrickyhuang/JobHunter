"""Keyword-based first-pass employment-type classification (full-time vs.
part-time/casual/on-call/seasonal/temporary). Cheap pre-filter; the LLM
enrichment step refines it later, same pattern as role_classifier.py.

Unmatched postings default to "unknown" rather than assuming "full_time" —
many full-time postings never say so explicitly, and we'd rather under-
penalize (miss a real part-time posting) than over-penalize a real full-time
one just because it didn't spell it out.
"""
from __future__ import annotations

EMPLOYMENT_SIGNALS: dict[str, list[str]] = {
    "full_time": [
        "full-time", "full time", "regular full-time", "permanent full-time",
        "1.0 fte",
    ],
    "part_time": [
        "part-time", "part time", "reduced hours", "0.5 fte", "0.6 fte",
    ],
    "casual": ["casual"],
    "on_call": [
        "on-call", "on call", "as-needed", "as needed", "relief", "auxiliary",
    ],
    "seasonal": ["seasonal"],
    "temporary": [
        "temporary", "term position", "fixed-term", "contract position",
    ],
}


def _count_hits(terms: list[str], title: str, body: str) -> float:
    score = 0.0
    for t in terms:
        if t in title:
            score += 2.0
        if t in body:
            score += 1.0
    return score


def classify_employment_type(title: str, description: str = "") -> str:
    title_l = (title or "").lower()
    body_l = (description or "").lower()

    scores = {kind: _count_hits(terms, title_l, body_l)
              for kind, terms in EMPLOYMENT_SIGNALS.items()}

    best = max(scores, key=scores.get)
    if scores[best] == 0.0:
        return "unknown"
    return best
