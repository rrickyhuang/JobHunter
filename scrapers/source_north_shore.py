"""District of North Vancouver + City of North Vancouver — both run the same
PeopleAdmin/ApplicantStack template (just a different base domain each), same
shared-module pattern as ``source_municipal_taleo``. Listings are server-
rendered at ``/postings/search``; each row is a ``div.job-item-posting`` with
the title link at ``h3 a``. The detail page's full text (incl. salary) is
carried in the ``og:description`` meta tag, cheaper to parse than the body.
"""
from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup

from scrapers.base import Fetcher

log = logging.getLogger("scrapers.north_shore")

SOURCE = "north_shore"
_MAX_PAGES = 10  # safety cap; boards typically list well under 25 open jobs

# (employer name, base URL, city label for geocoding)
_EMPLOYERS = [
    ("District of North Vancouver", "https://careers.dnv.org", "North Vancouver, BC"),
    ("City of North Vancouver", "https://cnv.peopleadmin.ca", "North Vancouver, BC"),
]


def _detail(fetcher: Fetcher, url: str) -> str:
    try:
        html = fetcher.get(url)
    except Exception as e:  # noqa: BLE001
        log.debug("north_shore detail fetch failed for %s: %s", url, e)
        return ""
    soup = BeautifulSoup(html, "lxml")
    meta = soup.select_one('meta[property="og:description"]')
    if meta and meta.get("content"):
        return meta["content"]
    body = soup.select_one("#content_inner") or soup
    return body.get_text(" | ", strip=True)


def _posting_id(url: str) -> str:
    m = re.search(r"/postings/(\d+)", url)
    return m.group(1) if m else url


def _fetch_one(fetcher: Fetcher, employer: str, base: str, city: str) -> list[dict]:
    out: list[dict] = []
    for page in range(1, _MAX_PAGES + 1):
        url = f"{base}/postings/search" + (f"?page={page}" if page > 1 else "")
        try:
            html = fetcher.get(url)
        except Exception as e:  # noqa: BLE001
            log.warning("%s postings fetch failed: %s", employer, e)
            break

        soup = BeautifulSoup(html, "lxml")
        items = soup.select("div.job-item-posting")
        if not items:
            break

        for item in items:
            link = item.select_one("h3 a")
            if not link:
                continue
            title = link.get_text(strip=True)
            href = link.get("href", "")
            job_url = href if href.startswith("http") else base + href

            description = _detail(fetcher, job_url) or item.get_text(" | ", strip=True)

            out.append({
                "source": SOURCE,
                "external_id": f"{employer}-{_posting_id(job_url)}",
                "url": job_url,
                "title": title,
                "company": employer,
                "location": city,
                "description": description,
                "posted_at": None,
            })

        if len(items) < 15:  # under a full page — no need to check for more
            break
    log.info("%s (PeopleAdmin): %d postings", employer, len(out))
    return out


def fetch(cfg: dict) -> list[dict]:
    fetcher = Fetcher(min_interval=2.0)
    out: list[dict] = []
    for employer, base, city in _EMPLOYERS:
        out.extend(_fetch_one(fetcher, employer, base, city))
    return out
