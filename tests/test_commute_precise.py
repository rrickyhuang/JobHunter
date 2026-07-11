from __future__ import annotations

import commute_precise
from conftest import make_job


def _enabled_cfg(cfg):
    cfg["commute"]["google_maps"]["enabled"] = True
    return cfg


def test_refine_returns_none_when_feature_disabled(cfg):
    job = make_job(location_lat=49.28, location_lng=-123.12, commute_min=25)
    assert commute_precise.refine(job, cfg) is None


def test_refine_returns_none_for_remote_job(cfg, monkeypatch):
    _enabled_cfg(cfg)
    monkeypatch.setattr(commute_precise.config, "env", lambda key, default=None, **kw: "fake-key")
    job = make_job(is_remote=True, location_lat=49.28, location_lng=-123.12, commute_min=25)
    assert commute_precise.refine(job, cfg) is None


def test_refine_returns_none_without_latlng(cfg, monkeypatch):
    _enabled_cfg(cfg)
    monkeypatch.setattr(commute_precise.config, "env", lambda key, default=None, **kw: "fake-key")
    job = make_job(location_lat=None, location_lng=None, commute_min=25)
    assert commute_precise.refine(job, cfg) is None


def test_refine_skips_jobs_whose_free_estimate_was_untrusted(cfg, monkeypatch):
    """Regression test for #17: commute.py's free estimate deliberately falls
    back to 'unknown' (commute_min stays None) for a geocode far from any
    station — real Google refinement must not silently trust that address
    just because lat/lng happen to be populated."""
    _enabled_cfg(cfg)
    monkeypatch.setattr(commute_precise.config, "env", lambda key, default=None, **kw: "fake-key")

    def _boom(*args, **kwargs):
        raise AssertionError("should never call the Distance Matrix API for an untrusted geocode")
    monkeypatch.setattr(commute_precise.requests, "get", _boom)

    job = make_job(location_lat=49.9, location_lng=-125.5, commute_min=None)
    assert commute_precise.refine(job, cfg) is None


def test_refine_proceeds_for_a_trusted_free_estimate(cfg, monkeypatch):
    _enabled_cfg(cfg)
    monkeypatch.setattr(commute_precise.config, "env", lambda key, default=None, **kw: "fake-key")
    monkeypatch.setattr(commute_precise, "_home_coords", lambda cfg: (49.26, -123.10))

    class _FakeResp:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return {"status": "OK", "rows": [{"elements": [
                {"status": "OK", "duration": {"value": 1800}}
            ]}]}

    monkeypatch.setattr(commute_precise.requests, "get", lambda *a, **kw: _FakeResp())
    job = make_job(location_lat=49.28, location_lng=-123.12, commute_min=25)
    minutes = commute_precise.refine(job, cfg)
    assert minutes == 30
