"""Translate all neighborhood_profiles and city_profiles from English to French.

Uses Qwen AI (DashScope) to batch-translate text fields and JSONB arrays/objects
per record. Idempotent — running twice just re-translates.
"""
from __future__ import annotations

import asyncio
import json
import sys
import os

# Ensure we can import from core/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import AsyncOpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.config import settings

# Qwen client
qwen = AsyncOpenAI(
    api_key=settings.dashscope_api_key,
    base_url=settings.qwen_base_url,
)

SYSTEM_PROMPT = (
    "You are a professional English-to-French translator for a real-estate "
    "intelligence platform in Cameroon. Translate all text values in the JSON "
    "from English to French. Rules:\n"
    "1. Keep keys unchanged — only translate values.\n"
    "2. If a value is null, empty, or already in French, keep it as-is.\n"
    "3. Do NOT translate phone numbers, URLs, or numeric values.\n"
    "4. Security ratings: 'Low Risk'->'Risque faible', 'Moderate Risk'->'Risque modere', "
    "'High Risk'->'Risque eleve'.\n"
    "5. Keep translations concise and natural for a French-speaking audience.\n"
    "6. Return ONLY a valid JSON object with the same keys — no markdown, no explanations."
)


async def translate_fields(fields: dict) -> dict:
    """Send a dict of fields to Qwen, get back translated dict. Retries on failure."""
    to_translate = {k: v for k, v in fields.items() if v}
    if not to_translate:
        return {}

    for attempt in range(4):
        try:
            resp = await qwen.chat.completions.create(
                model=settings.qwen_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(to_translate, ensure_ascii=False)},
                ],
                temperature=0.1,
                max_tokens=2000,
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            return json.loads(content)
        except Exception as e:
            wait = 2 ** attempt
            print(f"  [RETRY {attempt+1}/4] Waiting {wait}s... ({e})")
            await asyncio.sleep(wait)

    print(f"  [FAIL] Could not translate after 4 retries")
    return {}


async def translate_neighborhood_profiles(db):
    rows = db.execute(text(
        "SELECT id, city, neighborhood, security_rating, security_notes, "
        "description, real_estate_context, demographics, transport_info, "
        "risk_factors, landmarks, amenities FROM neighborhood_profiles"
    )).fetchall()

    print(f"\n=== Neighborhood Profiles: {len(rows)} records ===\n")
    translated_count = 0

    for row in rows:
        rid, city, neighborhood = row[0], row[1], row[2]
        label = f"{neighborhood or 'N/A'}, {city}" if neighborhood else city
        print(f"[{translated_count + 1}/{len(rows)}] {label} (id={rid})")

        text_fields = {
            "security_rating": row[3],
            "security_notes": row[4],
            "description": row[5],
            "real_estate_context": row[6],
            "demographics": row[7],
            "transport_info": row[8],
        }
        translated = await translate_fields(text_fields)

        risk_factors = row[9]
        if risk_factors and isinstance(risk_factors, list) and len(risk_factors) > 0:
            rf_t = await translate_fields({"risk_factors": risk_factors})
            if "risk_factors" in rf_t:
                risk_factors = rf_t["risk_factors"]

        landmarks = row[10]
        if landmarks and isinstance(landmarks, list) and len(landmarks) > 0:
            lm_t = await translate_fields({"landmarks": landmarks})
            if "landmarks" in lm_t:
                landmarks = lm_t["landmarks"]

        amenities = row[11]
        if amenities and isinstance(amenities, list) and len(amenities) > 0:
            am_t = await translate_fields({"amenities": amenities})
            if "amenities" in am_t:
                amenities = am_t["amenities"]

        updates = {}
        for k, v in translated.items():
            updates[k] = v
        if risk_factors is not None and row[9] is not None:
            updates["risk_factors"] = json.dumps(risk_factors, ensure_ascii=False)
        if landmarks is not None and row[10] is not None:
            updates["landmarks"] = json.dumps(landmarks, ensure_ascii=False)
        if amenities is not None and row[11] is not None:
            updates["amenities"] = json.dumps(amenities, ensure_ascii=False)

        if updates:
            set_clauses = ", ".join([f"{k} = :{k}" for k in updates])
            params = dict(updates)
            params["__id"] = rid
            db.execute(
                text(f"UPDATE neighborhood_profiles SET {set_clauses} WHERE id = :__id"),
                params
            )
            db.commit()
            translated_count += 1

        await asyncio.sleep(1.5)

    print(f"\nTranslated {translated_count}/{len(rows)} neighborhood profiles.")


async def translate_city_profiles(db):
    rows = db.execute(text(
        "SELECT id, city, region, security_rating, security_summary, "
        "area_description, travel_tips, curfew_info, "
        "current_threats, safest_zones, emergency_contacts "
        "FROM city_profiles"
    )).fetchall()

    print(f"\n=== City Profiles: {len(rows)} records ===\n")
    translated_count = 0

    for row in rows:
        rid, city = row[0], row[1]
        print(f"[{translated_count + 1}/{len(rows)}] {city} (id={rid})")

        text_fields = {
            "security_rating": row[3],
            "security_summary": row[4],
            "area_description": row[5],
            "travel_tips": row[6],
            "curfew_info": row[7],
        }
        translated = await translate_fields(text_fields)

        current_threats = row[8]
        if current_threats and isinstance(current_threats, list) and len(current_threats) > 0:
            ct_t = await translate_fields({"current_threats": current_threats})
            if "current_threats" in ct_t:
                current_threats = ct_t["current_threats"]

        safest_zones = row[9]
        if safest_zones and isinstance(safest_zones, list) and len(safest_zones) > 0:
            sz_t = await translate_fields({"safest_zones": safest_zones})
            if "safest_zones" in sz_t:
                safest_zones = sz_t["safest_zones"]

        emergency_contacts = row[10]
        if emergency_contacts and isinstance(emergency_contacts, list) and len(emergency_contacts) > 0:
            ec_t = await translate_fields({"emergency_contacts": emergency_contacts})
            if "emergency_contacts" in ec_t:
                emergency_contacts = ec_t["emergency_contacts"]

        updates = {}
        for k, v in translated.items():
            updates[k] = v
        if current_threats is not None and row[8] is not None:
            updates["current_threats"] = json.dumps(current_threats, ensure_ascii=False)
        if safest_zones is not None and row[9] is not None:
            updates["safest_zones"] = json.dumps(safest_zones, ensure_ascii=False)
        if emergency_contacts is not None and row[10] is not None:
            updates["emergency_contacts"] = json.dumps(emergency_contacts, ensure_ascii=False)

        if updates:
            set_clauses = ", ".join([f"{k} = :{k}" for k in updates])
            params = dict(updates)
            params["__id"] = rid
            db.execute(
                text(f"UPDATE city_profiles SET {set_clauses} WHERE id = :__id"),
                params
            )
            db.commit()
            translated_count += 1

        await asyncio.sleep(1.5)

    print(f"\nTranslated {translated_count}/{len(rows)} city profiles.")


async def main():
    engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    db = SessionLocal()

    try:
        await translate_neighborhood_profiles(db)
        await translate_city_profiles(db)

        print("\n=== Sample Results ===\n")
        samples = db.execute(text(
            "SELECT id, neighborhood, city, security_rating, "
            "LEFT(security_notes, 120) as notes_snip "
            "FROM neighborhood_profiles LIMIT 5"
        )).fetchall()
        for s in samples:
            print(f"  [{s[0]}] {s[1]}, {s[2]}: rating={s[3]}")
            print(f"       notes: {s[4]}...")

        city_samples = db.execute(text(
            "SELECT id, city, security_rating, LEFT(security_summary, 120) as summary_snip "
            "FROM city_profiles LIMIT 3"
        )).fetchall()
        for s in city_samples:
            print(f"  [{s[0]}] {s[1]}: rating={s[2]}")
            print(f"       summary: {s[3]}...")

        print("\nDone!")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())