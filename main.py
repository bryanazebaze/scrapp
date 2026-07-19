"""Scraper orchestrator — runs all active source adapters and ingests results.

Replaces the legacy main.py that instantiated MapioleScraper/KasastayScraper
and called fusionner_ou_inserer on each dict. The new flow:

  for each active source in the `sources` table (IN PARALLEL):
      adapter = build_adapter(source)         # dedicated or universal
      crawl_session_id = uuid4()
      drafts = adapter.fetch_listings(max_workers=N)  # detail pages concurrent
      stats = ingest(db, drafts, source.id, crawl_session_id, source.adapter_kind)
      mark_removed(db, source.id, crawl_session_id)

A source is matched to its adapter by `sources.slug`. Dedicated adapters are
registered in DEDICATED_ADAPTERS; the universal adapter is built on demand.

Concurrency:
  - Sources run in parallel threads (each with its own DB session).
  - Within each source, detail pages are fetched with a ThreadPoolExecutor
    (controlled by --max-workers, default 8).
  - DB ingest is single-threaded per source (one session per source thread).
  - recompute_canonical_prices runs once after ALL sources finish.
"""
from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.database import get_db, SessionLocal
from core.models import Source
from core.ingest import ingest, mark_removed, recompute_canonical_prices
from scrapers.mapiole import MapioleAdapter
from scrapers.kasastay import KasastayAdapter
from scrapers.nyetapiole import NyetapioleAdapter


DEDICATED_ADAPTERS = {
    "mapiole": MapioleAdapter,
    "kasastay": KasastayAdapter,
    "nyetapiole": NyetapioleAdapter,
}


def build_adapter(source: Source):
    """Instantiate the adapter for a source row, passing its crawl_config."""
    if source.adapter_kind == "universal":
        from scrapers.universal import UniversalAdapter  # lazy import
        return UniversalAdapter(source_id=source.id,
                                crawl_config=source.crawl_config or {},
                                seed_url=source.site_url)
    cls = DEDICATED_ADAPTERS.get(source.slug)
    if cls is None:
        raise ValueError(f"No dedicated adapter registered for source slug={source.slug!r}")
    return cls(source_id=source.id, crawl_config=source.crawl_config or {})


def run_source(db, source: Source, max_pages: int | None = None,
               max_workers: int = 8) -> dict:
    """Run one source's crawl + ingest. Returns the ingest stats.
    `max_workers` controls detail-page parallelism within the adapter."""
    adapter = build_adapter(source)
    crawl_session_id = uuid.uuid4()
    print(f"--- Crawl: {source.display_name} (session {crawl_session_id}) ---")
    drafts = adapter.fetch_listings(max_pages=max_pages, max_workers=max_workers)
    stats = ingest(db, drafts, source.id, crawl_session_id,
                   adapter_kind=source.adapter_kind)
    removed = mark_removed(db, source.id, crawl_session_id)
    stats["removed"] = removed
    print(f"--> {source.display_name}: {stats}")
    return stats


def main(max_pages: int | None = None, max_workers: int = 8) -> None:
    print("=== CentralImmo collection run ===\n")
    # Read the source list in a short-lived session, then close it so the
    # parallel workers each get their own clean session.
    db = SessionLocal()
    try:
        sources = db.query(Source).filter(Source.is_active == True).all()
        if not sources:
            print("No active sources. Seed the sources table first "
                  "(alembic upgrade head does this).")
            return
        # Detach source objects from the session so they can be used in
        # worker threads with separate sessions.
        for s in sources:
            db.expunge(s)
    finally:
        db.close()

    # Run all sources in parallel — each worker creates its own DB session.
    def _run(src: Source) -> dict:
        db = SessionLocal()
        try:
            return run_source(db, src, max_pages=max_pages,
                              max_workers=max_workers)
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=max(len(sources), 2)) as pool:
        futures = {pool.submit(_run, src): src for src in sources}
        for future in as_completed(futures):
            src = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"!! Source {src.slug} failed: {e}")

    # Recompute best prices after all sources are crawled so canonical
    # prices reflect the latest MIN(price_parsed) across linked raws.
    db = SessionLocal()
    try:
        try:
            price_stats = recompute_canonical_prices(db)
            print(f"--> price recompute: {price_stats}")
        except Exception as e:
            print(f"!! price recompute failed: {e}")
            db.rollback()
    finally:
        db.close()
    print("\n=== Collection run finished ===")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--source", help="Only crawl this source slug")
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--max-workers", type=int, default=8,
                   help="Concurrent detail-page fetches per source (default 8)")
    args = p.parse_args()
    if args.source:
        db = SessionLocal()
        try:
            src = db.query(Source).filter(Source.slug == args.source).first()
            if not src:
                raise SystemExit(f"Unknown source: {args.source}")
            run_source(db, src, max_pages=args.max_pages,
                       max_workers=args.max_workers)
        finally:
            db.close()
    else:
        main(max_pages=args.max_pages, max_workers=args.max_workers)