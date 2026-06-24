"""Database setup helper.

Prefer Alembic migrations (`alembic upgrade head`) — they preserve data.
This script is kept only for emergency fresh-schema creation and will DROP
all existing data. It will refuse to run if legacy tables are detected; use
Alembic instead so the backfill in 0001_initial_schema runs.
"""
import sys

from core.database import engine, Base
from core import models  # noqa: F401  -- register models on Base.metadata


def main() -> None:
    import sqlalchemy as sa
    insp = sa.inspect(engine)
    if insp.has_table("annonces") or insp.has_table("sources_annonces"):
        print("Legacy tables detected. Refusing to drop — run `alembic upgrade head`")
        print("instead so the backfill migration preserves your data.")
        sys.exit(1)
    print("Creating fresh schema (no existing data to preserve)...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Done. Now seed sources with: alembic upgrade head  (runs backfill, harmless on empty db)")


if __name__ == "__main__":
    main()