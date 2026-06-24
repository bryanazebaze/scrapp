"""Back-translate raw_listings.description_raw (French) → English.

Populates the listing_translations table (language='en'). Respects
raw_listings immutability — writes go to the side table, never to
raw_listings itself. Idempotent: skips listings that already have an
English translation.

Batched with a semaphore to keep Qwen rate limits in check.
"""
from __future__ import annotations

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import AsyncOpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.config import settings

qwen = AsyncOpenAI(
    api_key=settings.dashscope_api_key,
    base_url=settings.qwen_base_url,
)

SYSTEM_PROMPT = (
    "You are a professional French-to-English translator for a real-estate "
    "listing in Cameroon. Translate the user-provided description text from "
    "French to English. Rules:\n"
    "1. Do NOT translate phone numbers, URLs, prices, or numeric values.\n"
    "2. Keep the tone natural and concise for an English-speaking audience.\n"
    "3. Return ONLY the translated text — no markdown, no quotes, no explanations."
)

BATCH_SIZE = 20
CONCURRENCY = 8
BATCH_PAUSE = 1.0  # seconds between batches


async def translate_one(raw_listing_id: int, description: str) -> tuple[int, str | None]:
    """Translate one description, retrying on failure. Returns (id, text)."""
    for attempt in range(4):
        try:
            resp = await qwen.chat.completions.create(
                model=settings.qwen_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": description},
                ],
                temperature=0.1,
                max_tokens=1500,
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            return raw_listing_id, content
        except Exception as e:
            wait = 2 ** attempt
            print(f"  [RETRY {attempt+1}/4] listing {raw_listing_id} waiting {wait}s... ({e})")
            await asyncio.sleep(wait)
    print(f"  [FAIL] listing {raw_listing_id} could not translate after 4 retries")
    return raw_listing_id, None


async def main():
    engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    db = SessionLocal()

    try:
        # Listings needing translation: have a description, no en translation yet.
        rows = db.execute(text(
            "SELECT r.id, r.description_raw FROM raw_listings r "
            "WHERE r.description_raw IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM listing_translations t "
            "WHERE t.raw_listing_id = r.id AND t.language = 'en') "
            "ORDER BY r.id"
        )).fetchall()

        total = len(rows)
        print(f"\n=== Listings to translate: {total} ===\n")
        if total == 0:
            print("Nothing to do — all listings already have English translations.")
            return

        done = 0
        sem = asyncio.Semaphore(CONCURRENCY)

        async def bounded(item):
            async with sem:
                return await translate_one(item[0], item[1])

        for i in range(0, total, BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            results = await asyncio.gather(*[bounded(b) for b in batch])

            for rid, translated in results:
                if translated is not None:
                    db.execute(text(
                        "INSERT INTO listing_translations "
                        "(raw_listing_id, language, description) "
                        "VALUES (:rid, 'en', :desc) "
                        "ON CONFLICT (raw_listing_id, language) DO UPDATE "
                        "SET description = EXCLUDED.description, "
                        "updated_at = now()"
                    ), {"rid": rid, "desc": translated})
                    done += 1
            db.commit()
            print(f"  batch {i // BATCH_SIZE + 1}: {done}/{total} translated")
            await asyncio.sleep(BATCH_PAUSE)

        print(f"\nTranslated {done}/{total} listings.")

        print("\n=== Sample Results ===\n")
        samples = db.execute(text(
            "SELECT r.id, LEFT(r.description_raw, 100) as fr, "
            "LEFT(t.description, 100) as en "
            "FROM raw_listings r JOIN listing_translations t "
            "ON t.raw_listing_id = r.id AND t.language = 'en' "
            "LIMIT 3"
        )).fetchall()
        for s in samples:
            print(f"  [{s[0]}] FR: {s[1]}...")
            print(f"        EN: {s[2]}...")

        print("\nDone!")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())