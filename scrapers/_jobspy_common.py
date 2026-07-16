"""Shared plumbing for JobSpy-backed sources (Indeed, LinkedIn).

JobSpy (python-jobspy) scrapes these boards directly with no proxy needed for
our volume — the hand-rolled requests/BeautifulSoup approach in this repo's
history got Cloudflare-walled on both, but JobSpy's own request handling gets
through cleanly as of 2026-07. Treat that as a fact about JobSpy's current
approach, not a guarantee; if a board starts blocking it, this degrades the
same way any other source does (log + skip, doesn't crash the run).
"""
from __future__ import annotations

import logging
from datetime import date, datetime

log = logging.getLogger("scrapers.jobspy")


def _posted_at(v) -> datetime | None:
    # JobSpy returns a plain datetime.date, not datetime — the rest of the
    # pipeline (models.Job.posted_at, db.py's ISO serialization) expects datetime.
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime.combine(v, datetime.min.time())
    return None


def _num(v):
    """pandas gives NaN (a float), not None, for a missing numeric cell."""
    import math
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else v


def _str(v) -> str:
    """Same NaN issue for string columns — NaN is truthy, so `v or ''` doesn't
    catch it and a bare NaN would leak into a Job field as a float."""
    n = _num(v)
    return str(n) if n is not None else ""


def _salary_raw(row) -> str | None:
    lo, hi = _num(row.get("min_amount")), _num(row.get("max_amount"))
    if lo is None and hi is None:
        return None
    cur = row.get("currency") or ""
    interval = row.get("interval") or ""
    if lo is not None and hi is not None:
        return f"{cur} {lo:.0f} - {hi:.0f} {interval}".strip()
    amount = lo if lo is not None else hi
    return f"{cur} {amount:.0f} {interval}".strip()


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _fetch_batches(scrape_jobs, keywords: list[str], keywords_per_query: int, *, site_name: str,
                    source: str, base_kwargs: dict, seen_ids: set[str], out: list[dict], pass_label: str) -> None:
    for batch in _chunks(keywords, keywords_per_query):
        term = " OR ".join(f'"{k}"' for k in batch)
        kwargs = dict(base_kwargs, search_term=term)
        try:
            df = scrape_jobs(**kwargs)
        except Exception as e:  # noqa: BLE001 — never let one source/batch kill the run
            log.warning("%s: JobSpy scrape failed for %s batch %r: %s", source, pass_label, batch, e)
            continue

        for _, row in df.iterrows():
            title = _str(row.get("title"))
            ext_id = _str(row.get("id")) or _str(row.get("job_url"))
            if not (title and ext_id) or ext_id in seen_ids:
                continue
            seen_ids.add(ext_id)
            out.append({
                "source": source,
                "external_id": ext_id,
                "url": _str(row.get("job_url")),
                "title": title,
                "company": _str(row.get("company")),
                "location": _str(row.get("location")),
                "description": _str(row.get("description")),
                "posted_at": _posted_at(row.get("date_posted")),
                "salary_raw": _salary_raw(row),
            })


def run(cfg: dict, *, site_name: str, source: str, linkedin_fetch_description: bool = False) -> list[dict]:
    try:
        from jobspy import scrape_jobs
    except ImportError:
        log.warning("%s: python-jobspy not installed (pip install python-jobspy) — skipping", source)
        return []

    sq = cfg["search_queries"]
    keywords = sq["keywords"]
    jcfg = cfg.get("jobspy", {})
    # JobSpy takes one search term, not a list. A plain space-joined string is
    # read as one long AND'd phrase (returns ~nothing) — quoted-OR is what
    # Indeed's/LinkedIn's search actually treats as alternatives. There's no
    # documented hard limit on OR-term count, but a single query diluted across
    # 20+ terms risks each match ranking lower in the site's own relevance
    # ordering, so keywords are batched into multiple queries instead of one
    # giant OR string — this costs more requests per run (watch LinkedIn's
    # rate-limit sensitivity) but guarantees every configured keyword actually
    # gets searched, not just however many happened to be first in the list.
    keywords_per_query = jcfg.get("keywords_per_query", 6)

    base_kwargs = dict(
        site_name=[site_name],
        location=sq.get("location", "Vancouver, BC"),
        distance=sq.get("location_radius_km", 40),
        results_wanted=jcfg.get("results_wanted", 30),
        hours_old=jcfg.get("hours_old", 168),
        description_format="markdown",
    )
    if site_name == "indeed":
        base_kwargs["country_indeed"] = "Canada"
    if site_name == "linkedin":
        base_kwargs["linkedin_fetch_description"] = linkedin_fetch_description

    seen_ids: set[str] = set()
    out: list[dict] = []
    n_batches = -(-len(keywords) // keywords_per_query)  # local pass
    _fetch_batches(scrape_jobs, keywords, keywords_per_query, site_name=site_name, source=source,
                   base_kwargs=base_kwargs, seen_ids=seen_ids, out=out, pass_label="local")

    # Optional second pass: JobSpy's is_remote flag asks the site for
    # remote-tagged listings specifically, which the location+distance search
    # above doesn't reliably surface (remote postings often aren't geo-tagged
    # near Vancouver at all). Off by default since it doubles request volume
    # per source — turn on via jobspy.include_remote_pass once you actually
    # want remote-open roles (e.g. a tech/UX pivot search), and watch
    # LinkedIn's rate-limit sensitivity if both keywords_per_query and this
    # are cranked up together.
    if jcfg.get("include_remote_pass", False):
        remote_kwargs = dict(base_kwargs, is_remote=True)
        remote_kwargs.pop("distance", None)  # distance is meaningless for remote-only results
        _fetch_batches(scrape_jobs, keywords, keywords_per_query, site_name=site_name, source=source,
                       base_kwargs=remote_kwargs, seen_ids=seen_ids, out=out, pass_label="remote")
        n_batches *= 2

    log.info("%s (via JobSpy): %d postings across %d keyword batches%s", source, len(out), n_batches,
              " (incl. remote pass)" if jcfg.get("include_remote_pass", False) else "")
    return out
