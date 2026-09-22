"""Seed the control library and demo engagement.

    python -m app.seed

Separate from migrations so the public demo's reset endpoint can re-run it
without touching schema. [SCHEMA 6]
"""

import argparse
import logging

from app.config import get_settings
from app.db import get_session_factory
from app.seed.controls import load_control_library, load_engagement_scope
from app.seed.meridian import load_estate

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the AssureLens database.")
    parser.add_argument(
        "--library-only",
        action="store_true",
        help="Load the control library without creating the demo engagement.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for the synthetic estate. Defaults to DEFAULT_SEED.",
    )
    parser.add_argument(
        "--force-estate",
        action="store_true",
        help="Re-seed the estate even if it already exists.",
    )
    parser.add_argument(
        "--no-estate",
        action="store_true",
        help="Skip the synthetic estate (control library and engagement only).",
    )
    args = parser.parse_args()

    logging.basicConfig(level="INFO", format="%(message)s")

    with get_session_factory()() as db:
        stats = load_control_library(db)
        log.info(
            "control library: %d frameworks, %d clauses, %d controls (%d executable)",
            stats["frameworks"], stats["clauses"], stats["controls"], stats["executable"],
        )

        if not args.library_only:
            scope = load_engagement_scope(db)
            log.info(
                "engagement %d seeded; %d control(s) scoped out with a written reason",
                scope["engagement_id"], scope["excluded"],
            )

            if not args.no_estate:
                seed = args.seed if args.seed is not None else get_settings().default_seed
                counts = load_estate(db, seed, force=args.force_estate)
                if counts["skipped"]:
                    log.info(
                        "estate already present (%d principals); left alone",
                        counts["principals"],
                    )
                else:
                    log.info(
                        "estate seed=%d: %d principals, %d consents, %d events, "
                        "%d processors, %d access logs, %d predictions",
                        counts["seed"], counts["principals"], counts["consents"],
                        counts["consent_events"], counts["third_parties"],
                        counts["access_logs"], counts["predictions"],
                    )

        db.commit()
    log.info("done")


if __name__ == "__main__":
    main()
