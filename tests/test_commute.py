from __future__ import annotations

import commute


def test_bucket_score_picks_first_matching_bucket(cfg):
    buckets = cfg["commute"]["score_buckets"]
    assert commute._bucket_score(10, buckets) == 1.0
    assert commute._bucket_score(20, buckets) == 1.0
    assert commute._bucket_score(21, buckets) == 0.85
    assert commute._bucket_score(60, buckets) == 0.35


def test_bucket_score_falls_back_to_last_bucket_beyond_range(cfg):
    buckets = cfg["commute"]["score_buckets"]
    assert commute._bucket_score(100000, buckets) == 0.15


def test_remote_job_gets_flat_remote_score(cfg):
    result = commute.estimate("Remote", "Remote", True, cfg)
    assert result.score == cfg["commute"]["remote_score"]
    assert result.is_remote is True


def test_out_of_metro_scores_zero_and_never_geocodes(cfg, monkeypatch):
    def _boom(location):
        raise AssertionError("out-of-metro locations should never be geocoded")
    monkeypatch.setattr(commute, "_geocode", _boom)
    result = commute.estimate("Calgary, AB", "Other", False, cfg)
    assert result.score == 0.0
    assert result.commute_min is None


def test_city_only_location_is_unknown_not_geocoded(cfg, monkeypatch):
    def _boom(location):
        raise AssertionError("city-only locations should never be geocoded")
    monkeypatch.setattr(commute, "_geocode", _boom)
    result = commute.estimate("Vancouver, BC", "Vancouver", False, cfg)
    assert result.score == cfg["commute"]["unknown_location_score"]
    assert result.commute_min is None


def test_failed_geocode_is_unknown(cfg, monkeypatch):
    monkeypatch.setattr(commute, "_geocode", lambda location: None)
    result = commute.estimate("123 Main St, Vancouver, BC", "Vancouver", False, cfg)
    assert result.score == cfg["commute"]["unknown_location_score"]
    assert result.commute_min is None
    assert result.lat is None


def test_geocode_far_from_any_station_is_unknown_but_still_carries_latlng(cfg, monkeypatch):
    # Regression guard for the #17 fix: commute.py deliberately treats a
    # geocode >10km from any station as "unknown", but still returns lat/lng
    # (a bad geocode or genuinely-unserved area) — commute_precise.py must
    # not silently trust this location just because coordinates exist.
    monkeypatch.setattr(commute, "_geocode", lambda location: (49.9, -125.5))  # far away
    result = commute.estimate("999 Remote Rd, Vancouver, BC", "Vancouver", False, cfg)
    assert result.score == cfg["commute"]["unknown_location_score"]
    assert result.commute_min is None
    assert result.lat is not None and result.lng is not None
    assert result.nearest_station is None


def test_normal_geocode_near_station_produces_a_real_bucket_score(cfg, monkeypatch):
    import transit_data
    station_name = next(iter(transit_data.STATIONS))
    slat, slng = transit_data.STATIONS[station_name][:2]
    monkeypatch.setattr(commute, "_geocode", lambda location: (slat, slng))
    result = commute.estimate("123 Near Station St, Vancouver, BC", "Vancouver", False, cfg)
    assert result.commute_min is not None
    assert result.nearest_station == station_name
    assert result.score in {b["score"] for b in cfg["commute"]["score_buckets"]}
