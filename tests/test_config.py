from __future__ import annotations

import pytest

import config


def test_valid_config_passes(cfg):
    config._validate(cfg)  # should not raise


def test_missing_top_level_section_is_reported(cfg):
    del cfg["scoring"]
    with pytest.raises(config.ConfigError, match="scoring"):
        config._validate(cfg)


def test_missing_nested_key_is_reported(cfg):
    del cfg["commute"]["score_buckets"]
    with pytest.raises(config.ConfigError, match="commute.score_buckets"):
        config._validate(cfg)


def test_unknown_weight_key_is_reported(cfg):
    cfg["scoring"]["weights"]["typo_key"] = 1.0
    with pytest.raises(config.ConfigError, match="unrecognized"):
        config._validate(cfg)


def test_malformed_score_bucket_is_reported(cfg):
    cfg["commute"]["score_buckets"] = [{"max_min": 20}]  # missing "score"
    with pytest.raises(config.ConfigError, match="score_buckets"):
        config._validate(cfg)


def test_empty_score_buckets_is_reported(cfg):
    cfg["commute"]["score_buckets"] = []
    with pytest.raises(config.ConfigError, match="score_buckets"):
        config._validate(cfg)


def test_non_dict_config_is_reported():
    with pytest.raises(config.ConfigError):
        config._validate([])
    with pytest.raises(config.ConfigError):
        config._validate(None)


def test_multiple_problems_are_all_reported_at_once(cfg):
    del cfg["delivery"]
    del cfg["enrichment"]
    with pytest.raises(config.ConfigError) as exc_info:
        config._validate(cfg)
    message = str(exc_info.value)
    assert "delivery" in message
    assert "enrichment" in message
