from __future__ import annotations

import pytest

import db
from conftest import make_job


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    db.init_db(c)
    yield c
    c.close()


def test_upsert_insert_then_update(conn):
    job = make_job(score=0.5)
    assert db.upsert(conn, job) is True   # new row
    job.score = 0.9
    assert db.upsert(conn, job) is False  # existing row, updated

    fetched = db.get(conn, job.id)
    assert fetched.score == 0.9


def test_upsert_preserves_user_state_on_rescrape(conn):
    job = make_job()
    db.upsert(conn, job)
    db.set_state(conn, job.id, saved=True)
    db.set_stage(conn, job.id, "applied")

    # Re-scrape: same job, freshly built (as scrape.py would), with no
    # knowledge of the saved/stage state a human set via the cockpit.
    rescraped = make_job(source=job.source, external_id=job.external_id, score=0.7)
    db.upsert(conn, rescraped)

    fetched = db.get(conn, job.id)
    assert fetched.saved is True
    assert fetched.stage == "applied"
    assert fetched.score == 0.7  # non-protected fields DO refresh


def test_first_seen_at_is_stamped_once_and_never_moves(conn):
    job = make_job()
    db.upsert(conn, job)
    first = db.get(conn, job.id).first_seen_at

    rescraped = make_job(source=job.source, external_id=job.external_id)
    db.upsert(conn, rescraped)
    assert db.get(conn, job.id).first_seen_at == first


def test_query_excludes_dismissed_and_duplicates_by_default(conn):
    live = make_job()
    dismissed = make_job()
    dup = make_job()
    for j in (live, dismissed, dup):
        db.upsert(conn, j)
    db.set_state(conn, dismissed.id, dismissed=True)
    db.set_duplicate(conn, dup.id, live.id)

    ids = {j.id for j in db.query(conn)}
    assert ids == {live.id}

    ids_all = {j.id for j in db.query(conn, include_dismissed=True, include_duplicates=True)}
    assert ids_all == {live.id, dismissed.id, dup.id}


def test_query_min_score_filter(conn):
    low = make_job(score=0.1)
    high = make_job(score=0.9)
    db.upsert(conn, low)
    db.upsert(conn, high)

    ids = {j.id for j in db.query(conn, min_score=0.5)}
    assert ids == {high.id}


def test_query_invalid_order_by_raises(conn):
    with pytest.raises(ValueError):
        db.query(conn, order_by="score; DROP TABLE jobs")


def test_get_missing_job_returns_none(conn):
    assert db.get(conn, "does-not-exist") is None


def test_set_duplicate_clears_with_none(conn):
    a, b = make_job(), make_job()
    db.upsert(conn, a)
    db.upsert(conn, b)
    db.set_duplicate(conn, a.id, b.id)
    assert db.get(conn, a.id).duplicate_of == b.id
    db.set_duplicate(conn, a.id, None)
    assert db.get(conn, a.id).duplicate_of is None
