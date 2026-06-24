"""CentralImmo CLI — manual triggers for crawl, analytics, and job inspection.

Usage:
  python cli.py crawl [--source SLUG] [--max-pages N]
  python cli.py refresh          # re-crawl all active sources (like the 6h job)
  python cli.py analytics        # recompute neighborhood analytics now
  python cli.py jobs             # list scheduled jobs and their last status
  python cli.py universal --url URL [--max-pages N]   # crawl a new site
"""
from __future__ import annotations

import argparse
import sys
import uuid

from core.database import SessionLocal
from core.models import Source
from core.ingest import ingest, mark_removed, recompute_canonical_prices, backfill_canonicals
from core.scheduler import job_crawl_all, job_crawl_source, job_recompute_analytics, list_jobs
from main import build_adapter, run_source


def cmd_crawl(args: argparse.Namespace) -> None:
    if args.source:
        result = job_crawl_source(args.source)
        if not result.get("ok"):
            print(f"FAILED: {result.get('error')}")
            sys.exit(1)
        print(f"crawl {args.source}: {result.get('stats')}")
    else:
        # Crawl all active sources, optionally capping pages.
        if args.max_pages:
            db = SessionLocal()
            try:
                sources = db.query(Source).filter(Source.is_active == True).all()
                for src in sources:
                    try:
                        run_source(db, src, max_pages=args.max_pages)
                    except Exception as e:
                        print(f"!! {src.slug} failed: {e}")
                        db.rollback()
            finally:
                db.close()
        else:
            job_crawl_all()


def cmd_refresh(args: argparse.Namespace) -> None:
    from core.scheduler import job_refresh_active
    job_refresh_active()
    print("refresh done")


def cmd_analytics(args: argparse.Namespace) -> None:
    result = job_recompute_analytics()
    if not result.get("ok"):
        print(f"FAILED: {result.get('error')}")
        sys.exit(1)
    print(f"analytics recomputed: {result.get('stats')}")


def cmd_jobs(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        jobs = list_jobs(db)
        if not jobs:
            print("(no jobs tracked yet — scheduler hasn't run)")
            return
        for j in jobs:
            print(f"  #{j['id']} {j['job_type']} source={j['source_id']} "
                  f"cron={j['cron_expr'] or '-'} status={j['status']} "
                  f"last={j['last_run']} err={j['last_error'] or '-'}")
    finally:
        db.close()


def cmd_recompute_prices(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        stats = recompute_canonical_prices(db)
        print(f"recompute-prices: {stats}")
    finally:
        db.close()


def cmd_backfill(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        stats = backfill_canonicals(db)
        print(f"backfill: {stats}")
    finally:
        db.close()


def cmd_universal(args: argparse.Namespace) -> None:
    """Crawl an arbitrary URL with the universal adapter and ingest results."""
    db = SessionLocal()
    try:
        # Find or create a 'universal' source row for this site.
        from urllib.parse import urlparse
        netloc = urlparse(args.url).netloc
        slug = f"universal:{netloc}"
        src = db.query(Source).filter(Source.slug == slug).first()
        if src is None:
            src = Source(
                slug=slug,
                display_name=netloc,
                site_url=args.url,
                adapter_kind="universal",
                is_active=False,  # not auto-scheduled unless admin activates
                crawl_config={},
            )
            db.add(src)
            db.flush()
            print(f"[universal] created source {slug} (id={src.id})")

        adapter = build_adapter(src)
        crawl_session_id = uuid.uuid4()
        drafts = adapter.fetch_listings(max_pages=args.max_pages)
        stats = ingest(db, drafts, src.id, crawl_session_id, adapter_kind="universal")
        removed = mark_removed(db, src.id, crawl_session_id)
        stats["removed"] = removed
        print(f"[universal] {args.url} -> {stats}")
    finally:
        db.close()


def main() -> None:
    p = argparse.ArgumentParser(prog="cli.py", description="CentralImmo CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_crawl = sub.add_parser("crawl", help="Crawl active sources (or one)")
    p_crawl.add_argument("--source", help="Source slug to crawl (default: all active)")
    p_crawl.add_argument("--max-pages", type=int, default=None)
    p_crawl.set_defaults(func=cmd_crawl)

    p_refresh = sub.add_parser("refresh", help="Re-crawl active sources (6h-style)")
    p_refresh.set_defaults(func=cmd_refresh)

    p_an = sub.add_parser("analytics", help="Recompute neighborhood analytics")
    p_an.set_defaults(func=cmd_analytics)

    p_jobs = sub.add_parser("jobs", help="List scheduled jobs")
    p_jobs.set_defaults(func=cmd_jobs)

    p_rp = sub.add_parser("recompute-prices",
                          help="Recompute canonical best prices from raw listings")
    p_rp.set_defaults(func=cmd_recompute_prices)

    p_bf = sub.add_parser("backfill",
                          help="Re-resolve canonical locations, match_keys, and fields")
    p_bf.set_defaults(func=cmd_backfill)

    p_uni = sub.add_parser("universal", help="Crawl a new URL with the universal adapter")
    p_uni.add_argument("--url", required=True, help="Seed URL to crawl")
    p_uni.add_argument("--max-pages", type=int, default=20)
    p_uni.set_defaults(func=cmd_universal)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()