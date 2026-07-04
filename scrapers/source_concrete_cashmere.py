"""Concrete Cashmere Designs — a small Vancouver interior design-build studio
(commercial/retail/institutional/medical). WordPress site; the ``/careers/``
page lists open roles as plain ``VIEW POSITION`` links to their own static
pages, each rendered inside ``<main>``. First firm-direct scraper: a single
small studio with real, live openings (unlike the design consultancies
investigated and shelved for having empty career pages most of the time).
"""
from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from scrapers.base import Fetcher

log = logging.getLogger("scrapers.concrete_cashmere")

SOURCE = "concrete_cashmere"
_CAREERS_URL = "https://concretecashmere.com/careers/"
_COMPANY = "Concrete Cashmere Designs"


def _detail(fetcher: Fetcher, url: str) -> str:
    try:
        html = fetcher.get(url)
    except Exception as e:  # noqa: BLE001
        log.debug("Concrete Cashmere detail fetch failed for %s: %s", url, e)
        return ""
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("main") or soup
    return main.get_text(" | ", strip=True)


def fetch(cfg: dict) -> list[dict]:
    fetcher = Fetcher(min_interval=2.0)
    try:
        html = fetcher.get(_CAREERS_URL)
    except Exception as e:  # noqa: BLE001
        log.warning("Concrete Cashmere careers fetch failed: %s", e)
        return []

    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    for link in soup.find_all("a"):
        if link.get_text(strip=True).upper() != "VIEW POSITION":
            continue
        job_url = link.get("href", "")
        if not job_url:
            continue
        # Each posting is an image + "<h2>Title</h2><p>Location</p>" text block
        # + this button, in that order — the title is the nearest preceding h2.
        title_el = link.find_previous("h2")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            continue

        description = _detail(fetcher, job_url)
        slug = job_url.rstrip("/").split("/")[-1]

        out.append({
            "source": SOURCE,
            "external_id": slug,
            "url": job_url,
            "title": title,
            "company": _COMPANY,
            "location": "Vancouver, BC",
            "description": description or title,
            "posted_at": None,
        })
    log.info("Concrete Cashmere: %d postings", len(out))
    return out
