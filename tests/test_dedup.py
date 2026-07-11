from __future__ import annotations

import dedup
from conftest import make_job

_LONG_DESC = "Design public realm streetscapes and lead community engagement. " * 5


def test_same_title_and_company_across_sources_group_together(cfg):
    a = make_job(source="pibc", title="Urban Designer", company="City of Vancouver",
                 location_normalized="Vancouver")
    b = make_job(source="indeed", title="Urban Designer", company="City of Vancouver",
                 location_normalized="Vancouver")
    groups = dedup.find_groups([a, b], cfg)
    assert len(groups) == 1
    assert {j.id for j in groups[0]} == {a.id, b.id}


def test_different_titles_do_not_group(cfg):
    a = make_job(title="Urban Designer", company="City of Vancouver")
    b = make_job(title="Structural Engineer", company="City of Vancouver")
    assert dedup.find_groups([a, b], cfg) == []


def test_same_title_different_company_and_weak_description_does_not_group(cfg):
    a = make_job(title="Urban Designer", company="City of Vancouver", description="short")
    b = make_job(title="Urban Designer", company="Totally Different Firm", description="short")
    assert dedup.find_groups([a, b], cfg) == []


def test_same_title_no_company_but_strong_description_match_groups(cfg):
    # Aggregators sometimes blank the company or show a reseller's name —
    # a strong description match alone should still be enough to merge.
    a = make_job(title="Urban Designer", company="", description=_LONG_DESC,
                 location_normalized="Vancouver")
    b = make_job(title="Urban Designer", company="", description=_LONG_DESC,
                 location_normalized="Vancouver")
    groups = dedup.find_groups([a, b], cfg)
    assert len(groups) == 1


def test_same_title_and_company_but_different_location_and_weak_description_does_not_group(cfg):
    # Two genuinely different reqs at the same employer/title shouldn't merge
    # just because the title+company match.
    a = make_job(title="Urban Designer", company="Acme", location_normalized="Vancouver",
                 description="short a")
    b = make_job(title="Urban Designer", company="Acme", location_normalized="Other",
                 description="short b")
    assert dedup.find_groups([a, b], cfg) == []


def test_pick_keeper_prefers_source_priority_order(cfg):
    aggregator = make_job(source="indeed", score=0.9)
    direct = make_job(source="vancouver_gov", score=0.5)
    keeper = dedup.pick_keeper([aggregator, direct], cfg)
    assert keeper.id == direct.id


def test_pick_keeper_falls_back_to_score_when_priority_ties(cfg):
    a = make_job(source="unranked_source_a", score=0.4)
    b = make_job(source="unranked_source_b", score=0.9)
    keeper = dedup.pick_keeper([a, b], cfg)
    assert keeper.id == b.id


def test_pick_keeper_tiebreaks_on_id_for_stability(cfg):
    a = make_job(source="vancouver_gov", external_id="a", score=0.5)
    b = make_job(source="vancouver_gov", external_id="b", score=0.5)
    expected = min(a.id, b.id)
    keeper = dedup.pick_keeper([a, b], cfg)
    assert keeper.id == expected
