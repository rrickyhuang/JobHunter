"""Indeed.ca scraper.

Heads-up: Indeed actively fights scraping (Cloudflare / bot walls). This module
makes a best-effort HTML scrape and fails *gracefully* — if Indeed serves a wall
it logs a warning and returns whatever it got (often nothing) rather than
crashing the whole run. Treat Indeed as a bonus source, not a dependency; the
field-specific boards (Archinect/PIBC/CSLA) are the reliable backbone.
"""
from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup

from scrapers.base import Fetcher, BlockedError

log = logging.getLogger("scrapers.indeed")

SOURCE = "indeed"
_BASE = "https://ca.indeed.com/jobs"


def _build_query(cfg: dict) -> str:
    # Indeed treats quoted phrases joined by OR as alternatives.
    kws = cfg["search_queries"]["keywords"]
    return " OR ".join(f'"{k}"' for k in kws[:6])  # keep the query string sane


def _parse_cards(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    cards = soup.select("div.job_seen_beacon, div.cardOutline, a.tapItem")
    for c in cards:
        title_el = c.select_one("h2.jobTitle span[title], h2.jobTitle a, h2 span")
        title = title_el.get("title") if title_el and title_el.has_attr("title") \
            else (title_el.get_text(strip=True) if title_el else "")
        comp_el = c.select_one(
            "[data-testid='company-name'], span.companyName, .company_location .companyName"
        )
        loc_el = c.select_one(
            "[data-testid='text-location'], div.companyLocation, .company_location > div"
        )
        snip_el = c.select_one("div.job-snippet, [data-testid='jobsnippet_footer'], ul")
        link_el = c.select_one("a[href*='/rc/clk'], a[href*='jk='], h2.jobTitle a")

        href = link_el.get("href") if link_el else None
        jk = None
        if href:
            m = re.search(r"jk=([0-9a-f]{16})", href)
            jk = m.group(1) if m else None
        if not jk:
            # data-jk attribute on the card itself
            jk = c.get("data-jk") or (link_el.get("data-jk") if link_el else None)
        if not (title and jk):
            continue

        url = f"https://ca.indeed.com/viewjob?jk={jk}"
        out.append({
            "source": SOURCE,
            "external_id": jk,
            "url": url,
            "title": title,
            "company": comp_el.get_text(strip=True) if comp_el else "",
            "location": loc_el.get_text(strip=True) if loc_el else "",
            "description": snip_el.get_text(" ", strip=True) if snip_el else "",
        })
    return out


def fetch(cfg: dict, *, max_pages: int = 2) -> list[dict]:
    sq = cfg["search_queries"]
    fetcher = Fetcher(min_interval=3.0)
    results: dict[str, dict] = {}
    q = _build_query(cfg)
    for page in range(max_pages):
        params = {
            "q": q,
            "l": sq.get("location", "Vancouver, BC"),
            "radius": sq.get("location_radius_km", 40),
            "fromage": 7,          # last 7 days
            "start": page * 10,
        }
        try:
            html = fetcher.get(_BASE, params=params)
        except BlockedError as e:
            log.warning("Indeed blocked the request (%s). Skipping Indeed.", e)
            break
        except Exception as e:  # noqa: BLE001 — never let one source kill the run
            log.warning("Indeed fetch failed: %s", e)
            break
        cards = _parse_cards(html)
        if not cards:
            break
        for card in cards:
            results[card["external_id"]] = card
    log.info("Indeed: %d postings", len(results))
    return list(results.values())
