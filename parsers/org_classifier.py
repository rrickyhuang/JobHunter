"""Keyword-based org-type and org-size guessing.

Informational only — per Ricky's criteria, org type does NOT dock the score.
The LLM enrichment step can override these guesses. Everything that doesn't
match a known signal defaults to a small studio/consultancy.
"""
from __future__ import annotations

ORG_SIGNALS: dict[str, list[str]] = {
    "municipal_govt": [
        "city of vancouver", "city of burnaby", "city of surrey", "city of",
        "metro vancouver", "translink", "park board", "municipality",
        "municipal government", "local government", "district of",
    ],
    "provincial_govt": [
        "province of bc", "bc ministry", "ministry of", "bc housing",
        "crown corporation", "provincial government",
    ],
    "large_eng_firm": [
        "stantec", "wsp", "aecom", "hdr", "arcadis", "arup", "ibi group",
        "hatch", "jacobs", "tetra tech", "golder",
    ],
    "developer": [
        "real estate developer", "development company", "concord", "bosa",
        "wesgroup", "anthem", "polygon", "onni",
    ],
    "nonprofit_civic": [
        "non-profit", "nonprofit", "society", "foundation", "ngo",
        "social enterprise", "community land trust", "charity",
    ],
}

# Firms we know are large, for the size guess.
_LARGE_FIRMS = ORG_SIGNALS["large_eng_firm"]
_LARGE_HINTS = ("multinational", "global firm", "offices worldwide", "1000+ employees")
_SMALL_HINTS = ("boutique", "small studio", "small team", "tight-knit", "studio of")


def classify_org(company: str, description: str = "") -> tuple[str, str]:
    hay = f"{company or ''} {description or ''}".lower()

    org_type = "studio_consultancy"  # default
    for otype, terms in ORG_SIGNALS.items():
        if any(t in hay for t in terms):
            org_type = otype
            break

    # Size guess
    if org_type in ("municipal_govt", "provincial_govt", "large_eng_firm") \
            or any(f in hay for f in _LARGE_FIRMS) or any(h in hay for h in _LARGE_HINTS):
        org_size = "large"
    elif any(h in hay for h in _SMALL_HINTS):
        org_size = "small"
    else:
        org_size = "unknown"

    return org_type, org_size
