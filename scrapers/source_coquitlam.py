"""City of Coquitlam career site — a Cegid/Talentsoft-style board embedded
directly on the homepage (``careers.coquitlam.ca``), not a separate search
page. Each opening is a ``div.col-md-3.latestJobItems`` repeated across a
carousel + list widget (same postings duplicated for responsive layouts), so
postings are de-duplicated by the numeric ``offerid`` from each item's
``detailOffre(id)`` onclick handler. Detail links need a page-state token
that's embedded in a `<script>` on the same homepage — extracted fresh each
run rather than hardcoded, in case it changes.
"""
from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup

from scrapers.base import Fetcher

log = logging.getLogger("scrapers.coquitlam")

SOURCE = "coquitlam"
_HOME = "https://careers.coquitlam.ca/"
_TOKEN_RE = re.compile(r'location\.href\s*=\s*"([^"]+)"\s*\+\s*idOffre')
_ONCLICK_RE = re.compile(r"detailOffre\((\d+)\)")


def _detail(fetcher: Fetcher, url: str) -> str:
    try:
        html = fetcher.get(url)
    except Exception as e:  # noqa: BLE001
        log.debug("Coquitlam detail fetch failed for %s: %s", url, e)
        return ""
    soup = BeautifulSoup(html, "lxml")
    meta = soup.select_one('meta[property="og:description"]')
    if not meta or not meta.get("content"):
        return ""
    return BeautifulSoup(meta["content"], "lxml").get_text(" ", strip=True)


def fetch(cfg: dict) -> list[dict]:
    fetcher = Fetcher(min_interval=2.0)
    try:
        html = fetcher.get(_HOME)
    except Exception as e:  # noqa: BLE001
        log.warning("Coquitlam home fetch failed: %s", e)
        return []

    token_match = _TOKEN_RE.search(html)
    if not token_match:
        log.warning("Coquitlam: detail-link token not found, skipping (page layout may have changed)")
        return []
    detail_prefix = token_match.group(1)

    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    seen: set[str] = set()
    for block in soup.select("div.col-md-3.latestJobItems"):
        btn = block.select_one("input.viewOfferCarousel")
        if not btn:
            continue
        m = _ONCLICK_RE.search(btn.get("onclick", ""))
        if not m:
            continue
        offer_id = m.group(1)
        if offer_id in seen:
            continue
        seen.add(offer_id)

        title_el = block.select_one(".jobName")
        city_el = block.select_one(".jobCity")
        title = title_el.get_text(strip=True) if title_el else ""
        city = city_el.get_text(strip=True) if city_el else ""
        if not title:
            continue

        job_url = f"{_HOME}{detail_prefix}{offer_id}"
        description = _detail(fetcher, job_url) or block.get_text(" | ", strip=True)

        out.append({
            "source": SOURCE,
            "external_id": offer_id,
            "url": job_url,
            "title": title,
            "company": "City of Coquitlam",
            "location": f"{city}, Coquitlam, BC" if city else "Coquitlam, BC",
            "description": description,
            "posted_at": None,
        })
    log.info("City of Coquitlam: %d postings", len(out))
    return out
