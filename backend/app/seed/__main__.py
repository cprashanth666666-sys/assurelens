"""Seed the control library and demo engagement.

    python -m app.seed

Separate from migrations so the public demo's reset endpoint can re-run it
without touching schema. [SCHEMA 6]
"""

import argparse
import logging

from app.db import get_session_factory
from app.seed.controls import load_control_library, load_engagement_scope

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the AssureLens database.")
    parser.add_argument(
        "--library-only",
        action="store_true",
        help="Load the control library without creating the demo engagement.",
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

        db.commit()
    log.info("done")


if __name__ == "__main__":
    main()
