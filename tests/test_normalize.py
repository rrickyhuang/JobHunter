from __future__ import annotations

import pytest

from parsers.normalize import normalize_location


@pytest.mark.parametrize("location", [
    "Vancouver, BC, Canada",
    "Burnaby, BC",
    "New Westminster, BC",
    "North Vancouver, BC",
    "Surrey, BC",
    "Coquitlam, BC",
])
def test_metro_cities_classify_as_vancouver(location):
    assert normalize_location(location) == ("Vancouver", False)


@pytest.mark.parametrize("location", [
    # Regression test for #16: these used to match "bc, canada" / "british
    # columbia" as a metro-Vancouver substring and got misclassified.
    "Kelowna, BC, Canada",
    "Prince George, British Columbia",
    "Kamloops, BC",
    "Victoria, BC",
    "Nanaimo, BC, Canada",
])
def test_out_of_metro_bc_cities_are_not_vancouver(location):
    normalized, _is_remote = normalize_location(location)
    assert normalized == "Other"


def test_remote_location_flags_is_remote():
    assert normalize_location("Remote") == ("Remote", True)
    assert normalize_location("Work from home") == ("Remote", True)


def test_hybrid_location():
    assert normalize_location("Hybrid - Vancouver, BC") == ("Hybrid", False)


def test_in_metro_location_string_beats_remote_only_mentioned_in_description():
    # An explicit in-metro location isn't overridden by "fully remote" only
    # appearing in the description — location_normalized stays "Vancouver"
    # (not bumped to the "Remote" bucket) since the posting names a real office.
    normalized, _is_remote = normalize_location("Vancouver, BC", "this is a fully remote role")
    assert normalized == "Vancouver"


def test_empty_location_is_unknown():
    assert normalize_location("") == ("Unknown", False)
    assert normalize_location(None) == ("Unknown", False)
