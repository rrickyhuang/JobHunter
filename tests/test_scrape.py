from __future__ import annotations

import scrape
import db


def test_bad_item_is_skipped_without_aborting_the_rest_of_the_source(monkeypatch, cfg):
    """Regression test for #30: one malformed raw item used to raise
    uncaught out of the per-item loop, aborting every remaining item from
    that source (and any sources after it in the same run)."""
    good_1 = {
        "source": "testsrc", "external_id": "1", "url": "https://example.com/1",
        "title": "Urban Designer", "company": "Acme", "location": "Vancouver, BC",
        "description": "Design streetscapes.",
    }
    # Missing "source" — raw_to_job's `raw["source"]` KeyErrors immediately.
    bad = {"external_id": "2", "url": "https://example.com/2"}
    good_2 = {
        "source": "testsrc", "external_id": "3", "url": "https://example.com/3",
        "title": "Landscape Architect", "company": "Acme", "location": "Vancouver, BC",
        "description": "Design parks.",
    }

    real_connect = db.connect
    monkeypatch.setattr(scrape, "SOURCES", {"testsrc": lambda cfg: [good_1, bad, good_2]})
    monkeypatch.setattr(db, "connect", lambda *a, **kw: real_connect(":memory:"))
    cfg["enrichment"]["enabled"] = False

    stats = scrape.run(["testsrc"], cfg, dry_run=True)

    assert stats["fetched"] == 3
    # Both good items made it through as previews; the bad one was skipped.
    assert len(stats["previews"]) == 2
    titles = {job.title for _is_new, job in stats["previews"]}
    assert titles == {"Urban Designer", "Landscape Architect"}
