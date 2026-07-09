"""One-time web-research blurb on the hiring company, fed into coverletter.py's
prompt so the "diagnose the problem the org is hiring to solve" framing has
real material to work with — especially for firms the candidate doesn't
already know.

Shells out to the `claude` CLI (subscription, not API tokens) with the
WebSearch tool enabled, same as coverletter.py's draft/critique/revise calls.
Fails soft: no CLI, a timeout, or nothing findable all just mean no blurb —
letters already read fine without one. Cached on the job row (see
db.set_company_research) so a company is only researched once, on first
draft, and reused across revisions.
"""
from __future__ import annotations

import logging
import subprocess

log = logging.getLogger("company_research")

_NO_INFO_SENTINEL = "NO INFO FOUND"


def build_prompt(company: str, title: str) -> str:
    return f"""Use web search to put together a short briefing on "{company}", a company hiring for a "{title}" role.

In 2-4 sentences, cover what the company actually does (sector, focus, notable projects or clients if any) and, if you can find it, anything recent — growth, a new project, an expansion — that hints at why they might be hiring for this role right now. Be concrete and specific; skip generic filler like "a leading provider of innovative solutions."

If you can't find anything reliable and specific about this particular company (as opposed to generic guesses), respond with exactly "{_NO_INFO_SENTINEL}" and nothing else.

Output ONLY the briefing (or that exact sentinel) — no headers, no citations, no commentary before or after."""


def research(company: str, title: str) -> str | None:
    """Return a short company blurb via the claude CLI's web search, or None
    if it can't be produced (CLI missing, timeout, call failure, or nothing
    findable). Never raises."""
    if not company:
        return None
    try:
        result = subprocess.run(
            ["claude", "-p", build_prompt(company, title), "--allowedTools", "WebSearch"],
            capture_output=True, text=True, encoding="utf-8",
            stdin=subprocess.DEVNULL, timeout=120,
        )
    except FileNotFoundError:
        log.warning("claude CLI not found on PATH — skipping company research")
        return None
    except subprocess.TimeoutExpired:
        log.warning("company research for %r timed out", company)
        return None

    if result.returncode != 0 or not result.stdout.strip():
        log.warning("company research for %r failed: %s", company,
                    result.stderr.strip()[:200] or "no output")
        return None
    blurb = result.stdout.strip()
    if _NO_INFO_SENTINEL in blurb.upper():
        return None
    return blurb


def get_or_research(conn, job) -> str | None:
    """Cached lookup: return job.company_research if already saved, else
    research it now and persist it (mutates `job` in place too, so callers
    that already hold this job object see the fetched value immediately).
    Never raises."""
    if job.company_research:
        return job.company_research
    blurb = research(job.company, job.title)
    if blurb:
        import db
        db.set_company_research(conn, job.id, blurb)
        job.company_research = blurb
    return blurb
