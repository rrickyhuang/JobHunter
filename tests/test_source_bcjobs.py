from __future__ import annotations

import json

from scrapers import source_bcjobs

_JOB_POSTING_HTML = """<html><body>
<script type="application/ld+json">{"@type":"JobPosting","title":"Urban Designer",
"hiringOrganization":{"name":"City of Vancouver"},"datePosted":"2026-06-01",
"jobLocation":[{"address":{"addressLocality":"Vancouver","addressRegion":"BC"}}],
"description":"<p>Design public spaces.</p>"}</script>
</body></html>"""


def test_job_posting_jsonld_parses_valid_block():
    data = source_bcjobs._job_posting_jsonld(_JOB_POSTING_HTML)
    assert data["title"] == "Urban Designer"


def test_job_posting_jsonld_returns_none_for_malformed_json():
    html = '<script type="application/ld+json">{not valid json</script>'
    assert source_bcjobs._job_posting_jsonld(html) is None


def test_job_posting_jsonld_returns_none_when_absent():
    assert source_bcjobs._job_posting_jsonld("<html><body>no jsonld here</body></html>") is None


def test_detail_extracts_expected_fields(monkeypatch):
    class _FakeFetcher:
        def get(self, url, params=None):
            return _JOB_POSTING_HTML
    detail = source_bcjobs._detail(_FakeFetcher(), "https://www.bcjobs.ca/job/123")
    assert detail["title"] == "Urban Designer"
    assert detail["company"] == "City of Vancouver"
    assert detail["location"] == "Vancouver, BC"
    assert "Design public spaces" in detail["description"]


def test_detail_returns_none_when_detail_fetch_raises():
    class _FailingFetcher:
        def get(self, url, params=None):
            raise RuntimeError("network blip")
    assert source_bcjobs._detail(_FailingFetcher(), "https://www.bcjobs.ca/job/x") is None


def test_fetch_skips_malformed_list_items_instead_of_aborting_the_whole_run(monkeypatch, cfg):
    """Regression test for #31: one item in the list API response missing its
    'id' key used to raise an uncaught KeyError that killed the entire
    fetch() call (all keywords/pages), not just that one item."""
    good_item = {"id": 1, "url": "/job/1"}
    bad_item = {"url": "/job/2"}  # missing "id" — the schema-drift case
    list_payload = {
        "data": [good_item, bad_item],
        "paging": {"pages": 1},
    }

    class _FakeFetcher:
        def __init__(self, *a, **kw):
            pass

        def get(self, url, params=None):
            if url == source_bcjobs._API:
                return json.dumps(list_payload)
            return _JOB_POSTING_HTML

    monkeypatch.setattr(source_bcjobs, "Fetcher", _FakeFetcher)
    cfg["search_queries"] = {"keywords": ["urban designer"], "location": "Vancouver, BC"}

    out = source_bcjobs.fetch(cfg)
    # The good item still comes through; the malformed one is skipped, not
    # a source-wide crash that would have discarded everything.
    assert len(out) == 1
    assert out[0]["external_id"] == "1"
