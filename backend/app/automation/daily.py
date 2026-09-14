# backend/app/automation/daily.py
"""
Daily billing automation entrypoint.

Run once a day (a few minutes after midnight local time) from cron, a systemd
timer, or any container scheduler:

    python -m app.automation.daily
    python -m app.automation.daily --date 2026-09-01     # backfill / replay

Each organisation decides for itself whether today is its configured invoice
day or reminder day, and every run is idempotent - re-running the same day is
safe and does nothing the second time. Exit status is 0 when the sweep
completed, 1 when any organisation reported a failed job.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime

from app.db.session import SessionLocal
from app.services.automation_service import run_daily


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AlphaOne daily automation sweep")
    parser.add_argument(
        "--date",
        dest="run_date",
        default=None,
        help="Override the run date (YYYY-MM-DD). Use for backfills and replays.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log at DEBUG level.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    run_date: date | None = None
    if args.run_date:
        run_date = datetime.strptime(args.run_date, "%Y-%m-%d").date()

    db = SessionLocal()
    try:
        summary = run_daily(db, run_date=run_date)
    except Exception:  # noqa: BLE001 - the scheduler needs a clean exit code
        logging.getLogger(__name__).exception("automation sweep failed")
        return 1
    finally:
        db.close()

    ran = [row for row in summary if row["status"] in ("success", "failed")]
    failed = [row for row in summary if row["status"] == "failed"]

    for row in ran:
        print(
            f"[{row['status']}] org={row['organization_id']} job={row['job']} "
            f"{(row.get('message') or '').strip()}"
        )
    print(
        f"automation complete: {len(ran)} job(s) ran, "
        f"{len(failed)} failed, {len(summary) - len(ran)} not due/disabled"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
