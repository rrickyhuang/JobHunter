"""Loads runtime configuration and secrets.

Personal settings live in `config.yaml` (gitignored); secrets live in `.env`
(gitignored). Both have committed templates (`config.example.yaml`, `.env.example`)
so a fresh clone knows what to fill in. Neither real file is ever committed.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.yaml"
ENV_PATH = ROOT / ".env"

load_dotenv(ENV_PATH)


@lru_cache(maxsize=1)
def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "config.yaml not found. Copy config.example.yaml to config.yaml "
            "and edit it for your search:\n"
            "    copy config.example.yaml config.yaml   (Windows)\n"
            "    cp config.example.yaml config.yaml      (macOS/Linux)"
        )
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def env(key: str, default: str | None = None, *, required: bool = False) -> str | None:
    val = os.getenv(key, default)
    if required and not val:
        raise RuntimeError(
            f"Missing required environment variable {key!r}. "
            f"Copy .env.example to .env and fill it in."
        )
    return val
