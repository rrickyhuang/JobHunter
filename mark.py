"""Mark a job's application status: applied, interested (saved), not
interested (dismissed), or seen. Works on any job — scraped or manual.

Usage:
    python mark.py <row-# or id> applied
    python mark.py <row-# or id> interested
    python mark.py <row-# or id> not-interested
    python mark.py <row-# or id> seen
    python mark.py <row-# or id> <status> --clear   # undo

Dismissed ("not interested") jobs are hidden from `show.py`'s default list —
use `show.py --all` to see them too.
"""
from __future__ import annotations

import sys

import db

_STATUSES = {
    "applied": "applied",
    "interested": "saved",
    "not-interested": "dismissed",
    "seen": "seen",
}


def _resolve_job(conn, target: str):
    if target.isdigit():
        jobs = db.query(conn, include_dismissed=True, order_by="score DESC")
        idx = int(target)
        if idx < len(jobs):
            return jobs[idx]
    return db.get(conn, target)


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--clear"]
    clear = "--clear" in sys.argv[1:]
    if len(args) < 2:
        print(f"\n  Usage: python mark.py <row-# or id> <{'|'.join(_STATUSES)}> [--clear]\n")
        sys.exit(1)

    target, status = args[0], args[1]
    if status not in _STATUSES:
        print(f"\n  Unknown status {status!r}. Choose one of: {', '.join(_STATUSES)}\n")
        sys.exit(1)

    conn = db.connect()
    db.init_db(conn)
    job = _resolve_job(conn, target)
    if not job:
        print(f"\n  No job found for {target!r}\n")
        conn.close()
        sys.exit(1)

    value = not clear
    if status == "applied":
        db.mark_applied(conn, job.id, applied=value)
    else:
        db.set_state(conn, job.id, **{_STATUSES[status]: value})
    conn.close()

    verb = "Cleared" if clear else "Marked"
    print(f"\n  {verb}: {status} - {job.title} @ {job.company}\n")


if __name__ == "__main__":
    main()
