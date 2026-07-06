"""Local web cockpit for browsing jobs and managing application status.

    python serve.py            run the UI at http://127.0.0.1:5001

A live, write-capable companion to the read-only `report.html`. Phase 1: browse
the full DB with the same search/filter controls as the report, and change a
job's application stage / interested / dismissed state inline (HTMX swaps just
the affected card, no page reload). Reuses the existing renderers (`html_render`)
and DB logic (`db`) — this module is mostly wiring.

Mirrors the sibling apartment-hunter app's conventions (Flask + HTMX, partial
swaps, localhost-only, factory + argparse). Runs on port 5001 so it can sit
alongside the apartment hunter (5000) at the same time. See WEB_UI_PLAN.md.
"""
from __future__ import annotations

import argparse
import logging

from flask import Flask, abort, request

import config
import db
import html_render
import logutil

log = logging.getLogger("serve")

# Stage buttons offered on each card, in pipeline order. None == clear/not-applied.
_STAGE_CHOICES = ("applied", "interviewing", "offer", "denied", "withdrawn")

_BTN = ("display:inline-block;padding:3px 9px;margin:0 4px 4px 0;border-radius:6px;"
        "border:1px solid #d0d7de;background:#fff;color:#24292f;font-size:12px;"
        "cursor:pointer;font-family:inherit;")
_BTN_ON = _BTN + "background:#0969da;color:#fff;border-color:#0969da;"


def _actions_html(job) -> str:
    """The inline control bar appended inside a card: one button per stage plus
    interested / dismiss toggles. Each posts to a route that flips state and
    returns the freshly rendered card, which HTMX swaps in place."""
    hx = ('hx-target="#job-{id}" hx-swap="outerHTML" '
          'hx-post="/job/{id}/{path}"').format
    stage_btns = "".join(
        f'<button style="{_BTN_ON if job.stage == s else _BTN}" '
        f'{hx(id=job.id, path="stage/" + s)}>{s.capitalize()}</button>'
        for s in _STAGE_CHOICES
    )
    clear = (f'<button style="{_BTN}" {hx(id=job.id, path="stage/clear")}>Clear</button>'
             if job.stage else "")
    interested = (f'<button style="{_BTN_ON if (job.saved and not job.stage) else _BTN}" '
                  f'{hx(id=job.id, path="interested")}>Interested</button>')
    dismiss = (f'<button style="{_BTN_ON if job.dismissed else _BTN}" '
               f'{hx(id=job.id, path="dismiss")}>Dismiss</button>')
    return (
        '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #eaeef2;">'
        f'{stage_btns}{clear}'
        '<span style="display:inline-block;width:12px;"></span>'
        f'{interested}{dismiss}</div>'
    )


def _card(job, row_no: int) -> str:
    return html_render.job_card(
        job, row_no, full_desc=True, report=True, row_no=row_no,
        dom_id=f"job-{job.id}", actions_html=_actions_html(job))


def create_app(db_path=db.DB_PATH) -> Flask:
    app = Flask(__name__)
    conn0 = db.connect(db_path)
    db.init_db(conn0)
    conn0.close()

    def get_conn():
        return db.connect(db_path)

    def _job_or_404(conn, job_id: str):
        job = db.get(conn, job_id)
        if not job:
            abort(404)
        return job

    def _row_no(conn, job_id: str) -> int:
        """Position of a job in the full ranked list — the same '#' the report
        and show.py use, so it stays consistent across a status change."""
        jobs = db.query(conn, include_dismissed=True, include_duplicates=True,
                        order_by="score DESC")
        for i, j in enumerate(jobs, 1):
            if j.id == job_id:
                return i
        return 0

    @app.route("/")
    def index():
        cfg = config.load_config()
        conn = get_conn()
        jobs = db.query(conn, include_dismissed=True, include_duplicates=True,
                        order_by="score DESC")
        live = [j for j in jobs if not j.disqualifier and not j.duplicate_of]
        dead = sum(1 for j in jobs if j.disqualifier)
        dup = sum(1 for j in jobs if j.duplicate_of)
        intro = (f"{len(live)} scored · {dead} disqualified · {dup} duplicates — "
                 "click a status on any card to update it instantly")
        cards = "".join(_card(j, i) for i, j in enumerate(jobs, 1))
        body = (html_render._filter_bar(jobs)
                + f'<div id="cards">{cards}</div>'
                + html_render._SCRIPT)
        conn.close()
        head = '<script src="https://unpkg.com/htmx.org@1.9.12"></script>'
        return html_render.page("JobHunter — Cockpit", intro, body, head_extra=head)

    @app.route("/job/<job_id>/stage/<stage>", methods=["POST"])
    def set_stage(job_id, stage):
        if stage != "clear" and stage not in db.STAGES:
            abort(400)
        conn = get_conn()
        job = _job_or_404(conn, job_id)
        new_stage = None if stage == "clear" else stage
        db.set_stage(conn, job_id, new_stage)
        log.info("stage -> %s on %s (%s @ %s)", new_stage or "cleared",
                 job_id, job.title, job.company)
        job = db.get(conn, job_id)
        row_no = _row_no(conn, job_id)
        conn.close()
        return _card(job, row_no)

    @app.route("/job/<job_id>/interested", methods=["POST"])
    def toggle_interested(job_id):
        conn = get_conn()
        job = _job_or_404(conn, job_id)
        db.set_state(conn, job_id, saved=not job.saved)
        log.info("interested -> %s on %s (%s @ %s)", not job.saved,
                 job_id, job.title, job.company)
        job = db.get(conn, job_id)
        row_no = _row_no(conn, job_id)
        conn.close()
        return _card(job, row_no)

    @app.route("/job/<job_id>/dismiss", methods=["POST"])
    def toggle_dismiss(job_id):
        conn = get_conn()
        job = _job_or_404(conn, job_id)
        db.set_state(conn, job_id, dismissed=not job.dismissed)
        log.info("dismissed -> %s on %s (%s @ %s)", not job.dismissed,
                 job_id, job.title, job.company)
        job = db.get(conn, job_id)
        row_no = _row_no(conn, job_id)
        conn.close()
        return _card(job, row_no)

    return app


def main() -> None:
    logutil.setup_logging()
    ap = argparse.ArgumentParser(description="JobHunter web cockpit.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5001)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    app = create_app()
    print(f"\n  JobHunter cockpit -> http://{args.host}:{args.port}\n")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
