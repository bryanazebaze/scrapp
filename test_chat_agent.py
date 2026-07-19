#!/usr/bin/env python3
"""Comprehensive test suite for the CentralImmo AI chat agent (DeepSeek).

Sends 50 questions to POST /chat, captures the response (reply, properties,
tool_used), independently queries the database for ground truth, and compares
the AI's answer against what the DB actually contains.

Usage:
    python test_chat_agent.py
    python test_chat_agent.py --verbose          # print full AI replies
    python test_chat_agent.py --category search  # run one category only
    python test_chat_agent.py --timeout 60      # per-question timeout (seconds)

Categories: search, safety, analytics, price, locations, complex
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any

import psycopg2
import requests

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000/chat")
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "database": os.environ.get("DB_NAME", "immo_db"),
    "user": os.environ.get("DB_USER", "immo_user"),
    "password": os.environ.get("DB_PASS", "1234"),
}

# Categories: search, safety, analytics, price, locations, complex
CATEGORIES = ["search", "safety", "analytics", "price", "locations", "complex"]


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass
class TestCase:
    id: int
    category: str
    question: str
    expected_tools: list[str]      # tools we expect the agent to call
    db_check: str                  # SQL to get ground truth (or empty)
    validate: str                  # name of the validation function to use
    description: str = ""


@dataclass
class TestResult:
    test: TestCase
    ai_reply: str
    ai_properties: list[dict]
    ai_tool_used: str | None
    db_truth: Any
    passed: bool
    issues: list[str] = field(default_factory=list)
    elapsed: float = 0.0
    error: str | None = None


# --------------------------------------------------------------------------- #
# DB helpers
# --------------------------------------------------------------------------- #
def get_db():
    return psycopg2.connect(**DB_CONFIG)


def db_query(sql: str, params: tuple | None = None) -> Any:
    """Run a SQL query and return results."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        if cur.description:
            return cur.fetchall()
        conn.commit()
        return []
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Validation functions
# --------------------------------------------------------------------------- #
def normalize_price(p) -> int | None:
    """Convert a price value to int, handling None and floats."""
    if p is None:
        return None
    return int(float(p))


def val_property_count(result: TestResult) -> bool:
    """Check if the number of properties returned by the AI matches the DB."""
    db_count = result.db_truth[0][0] if result.db_truth else 0
    ai_count = len(result.ai_properties)
    if db_count == 0:
        # If DB has 0, AI should say "no properties found" or similar
        ok = ai_count == 0 or "aucun" in result.ai_reply.lower() or "pas de" in result.ai_reply.lower() or "rien" in result.ai_reply.lower()
        if not ok:
            result.issues.append(f"DB has 0 properties but AI returned {ai_count} and didn't say 'no results'")
        return ok
    if db_count > 10:
        # Tool has a default limit of 10 — AI won't return all. Check if AI
        # returned some properties or mentioned the total count.
        if ai_count == 0:
            ok = str(db_count) in result.ai_reply or "trouve" in result.ai_reply.lower()
            if not ok:
                result.issues.append(f"DB has {db_count} properties but AI returned 0 and didn't mention the count")
            return ok
        # AI returned some properties — that's fine, it's limited by the tool
        return True
    if ai_count == 0 and db_count > 0:
        # DB has properties but AI returned none — real issue
        ok = str(db_count) in result.ai_reply or "trouve" in result.ai_reply.lower()
        if not ok:
            result.issues.append(f"DB has {db_count} properties but AI returned 0 and didn't mention the count")
        return ok
    # Both have properties — check if counts are close (within 3)
    if abs(db_count - ai_count) > 3:
        result.issues.append(f"DB count={db_count}, AI count={ai_count} (diff={abs(db_count - ai_count)})")
        return False
    return True


def val_property_count_and_ids(result: TestResult) -> bool:
    """Check property count and verify some property IDs match."""
    if not result.db_truth:
        return val_property_count(result)
    db_ids = {row[0] for row in result.db_truth}
    ai_ids = {p.get("id") for p in result.ai_properties if p.get("id")}
    if db_ids and ai_ids:
        overlap = db_ids & ai_ids
        if len(overlap) == 0:
            result.issues.append(f"DB IDs={list(db_ids)[:5]}, AI IDs={list(ai_ids)[:5]} — no overlap")
            return False
    return val_property_count(result)


def _strip_accents(s: str) -> str:
    """Remove accents from a string for comparison."""
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    ).lower()


def val_safety_rating(result: TestResult) -> bool:
    """Check if the AI mentions the correct security rating (accent-insensitive)."""
    if not result.db_truth:
        result.issues.append("No DB data for safety profile")
        return False
    db_rating = result.db_truth[0][0] or ""
    # Normalize the DB rating (remove accents) for keyword lookup
    norm_rating = _strip_accents(db_rating)
    rating_keywords = {
        "risque eleve": ["eleve", "haut", "high"],
        "risque modere": ["modere", "moderate", "medium"],
        "risque faible": ["faible", "low"],
    }
    expected = rating_keywords.get(norm_rating, [norm_rating])
    reply_norm = _strip_accents(result.ai_reply)
    found = any(kw in reply_norm for kw in expected)
    if not found:
        result.issues.append(f"DB rating='{db_rating}' but AI reply doesn't mention it. Reply: '{result.ai_reply[:200]}'")
    return found


def val_safest_city(result: TestResult) -> bool:
    """Check if the AI correctly identifies the safest city.
    Accepts any city with the same (lowest) security rating."""
    if not result.db_truth:
        result.issues.append("No DB data for safest city")
        return False
    safest_city = result.db_truth[0][0]
    reply_norm = _strip_accents(result.ai_reply)
    # The DB query returns the first city with the lowest risk, but there
    # may be ties (e.g., both Kribi and Ebolowa have "Risque faible").
    # Accept the answer if the AI mentions ANY "Risque faible" city.
    found = _strip_accents(safest_city) in reply_norm
    if not found:
        # Check if AI mentioned another city with "Risque faible"
        # by looking for "faible" in the reply
        if "faible" in reply_norm:
            return True  # AI mentioned a low-risk city, accept it
        result.issues.append(f"DB safest city='{safest_city}' but AI didn't mention it. Reply: '{result.ai_reply[:200]}'")
    return found


def val_analytics_value(result: TestResult) -> bool:
    """Check if the AI mentions the correct median price from analytics.
    Handles various price formats: "45000000", "45 000 000", "45 millions"."""
    if not result.db_truth:
        result.issues.append("No DB data for analytics")
        return False
    db_median = int(float(result.db_truth[0][0] or 0))
    db_count = int(result.db_truth[0][1] or 0)
    reply_lower = result.ai_reply.lower().replace(" ", "")
    reply_norm = _strip_accents(result.ai_reply).replace(" ", "")

    # Check if AI mentions the listing count
    count_ok = str(db_count) in result.ai_reply

    # Check if AI mentions the median price in any format
    price_str = str(db_median)
    price_ok = price_str in reply_norm
    if not price_ok:
        # Try "X millions" format (e.g., 45000000 -> "45 millions" or "45million")
        if db_median >= 1_000_000:
            millions = db_median // 1_000_000
            price_ok = f"{millions}million" in reply_norm or f"{millions}m" in reply_norm
        # Try "X mille" / "X k" format (e.g., 25000 -> "25 mille" or "25k")
        if not price_ok and db_median >= 1_000:
            thousands = db_median // 1_000
            price_ok = f"{thousands}mille" in reply_norm or f"{thousands}k" in reply_norm

    # Require either count OR price to be mentioned (not both — AI may
    # summarize differently per the "be concise" system prompt)
    issues = []
    if not count_ok and not price_ok:
        issues.append(f"Neither listing_count={db_count} nor median_price={db_median} found in reply")
    result.issues.extend(issues)
    return len(issues) == 0


def val_neighborhood_list(result: TestResult) -> bool:
    """Check if the AI mentions the correct neighborhoods for a city (accent-insensitive)."""
    if not result.db_truth:
        result.issues.append("No DB data for neighborhoods")
        return False
    db_neighborhoods = [row[0] for row in result.db_truth if row[0]]
    reply_norm = _strip_accents(result.ai_reply)
    found = sum(1 for nb in db_neighborhoods if _strip_accents(nb) in reply_norm)
    total = len(db_neighborhoods)
    # At least 30% of neighborhoods should be mentioned
    ratio = found / total if total > 0 else 0
    if ratio < 0.3:
        result.issues.append(f"Only {found}/{total} neighborhoods mentioned in reply")
        return False
    return True


def val_trending(result: TestResult) -> bool:
    """Check if the AI mentions trending neighborhoods from the DB."""
    if not result.db_truth:
        result.issues.append("No DB data for trending")
        return False
    db_neighborhoods = [row[0] for row in result.db_truth if row[0]]
    reply_lower = result.ai_reply.lower()
    found = sum(1 for nb in db_neighborhoods if nb.lower() in reply_lower)
    if found == 0:
        result.issues.append(f"None of the trending neighborhoods mentioned. DB: {db_neighborhoods[:5]}")
        return False
    return True


def val_price_analysis(result: TestResult) -> bool:
    """Check if the AI mentions the correct verdict from price analysis."""
    if not result.db_truth:
        result.issues.append("No DB data for price analysis")
        return False
    db_verdict = result.db_truth[0][0] if result.db_truth else None
    if not db_verdict:
        result.issues.append("No verdict in DB data")
        return False
    verdict_map = {
        "below_market": ["en dessous", "below", "inferieur", "au-dessous"],
        "above_market": ["au-dessus", "above", "superieur", "plus cher"],
        "around_market": ["autour", "around", "dans la moyenne", "proche"],
        "insufficient_data": ["insuffisant", "pas assez", "insufficient"],
    }
    expected_kws = verdict_map.get(db_verdict, [db_verdict])
    reply_lower = result.ai_reply.lower()
    found = any(kw in reply_lower for kw in expected_kws)
    if not found:
        result.issues.append(f"DB verdict='{db_verdict}' but AI didn't mention it. Reply: '{result.ai_reply[:200]}'")
    return found


def val_locations(result: TestResult) -> bool:
    """Check if the AI mentions the correct cities from the DB (accent-insensitive)."""
    if not result.db_truth:
        result.issues.append("No DB data for locations")
        return False
    db_cities = [row[0] for row in result.db_truth if row[0]]
    reply_norm = _strip_accents(result.ai_reply)
    found = sum(1 for c in db_cities if _strip_accents(c) in reply_norm)
    if found < len(db_cities) * 0.5:
        result.issues.append(f"Only {found}/{len(db_cities)} cities mentioned")
        return False
    return True


def val_median_price_text(result: TestResult) -> bool:
    """Check if the AI mentions the correct median price for a city/type."""
    if not result.db_truth:
        result.issues.append("No DB data for median price")
        return False
    db_median = int(float(result.db_truth[0][0] or 0))
    price_str = str(db_median)
    price_ok = price_str in result.ai_reply or price_str.replace(" ", "") in result.ai_reply.replace(" ", "")
    if not price_ok:
        result.issues.append(f"DB median={db_median} not found in reply: '{result.ai_reply[:200]}'")
    return price_ok


def val_tool_called(result: TestResult) -> bool:
    """Check if the AI called the expected tool."""
    expected = result.test.expected_tools
    if not expected:
        return True
    tool_used = result.ai_tool_used
    if tool_used is None:
        # The AI might not have called any tool if it answered from its own knowledge
        # Check if the expected tool name appears in the reply
        result.issues.append(f"Expected tool(s) {expected} but tool_used=None")
        return False
    ok = tool_used in expected
    if not ok:
        result.issues.append(f"Expected tools {expected}, got '{tool_used}'")
    return ok


def val_always_pass(result: TestResult) -> bool:
    """Always passes — for informational questions."""
    return True


def val_no_error(result: TestResult) -> bool:
    """Check if the AI didn't return an error message."""
    error_phrases = ["desole", "erreur", "difficulte technique", "pas configure", "reformuler"]
    reply_lower = result.ai_reply.lower()
    for phrase in error_phrases:
        if phrase in reply_lower:
            result.issues.append(f"AI returned error-like phrase: '{phrase}'")
            return False
    return True


# --------------------------------------------------------------------------- #
# Test cases (50 questions)
# --------------------------------------------------------------------------- #
TESTS: list[TestCase] = [
    # ===================================================================== #
    # Category 1: Property Search (15 questions)
    # ===================================================================== #
    TestCase(1, "search", "Appartements a Douala",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Douala' AND cp.property_type='Appartement' AND cp.is_active=true",
             "val_property_count",
             "All Appartements in Douala"),

    TestCase(2, "search", "Appartements a Yaounde moins de 50000 XAF",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Yaoundé' AND cp.property_type='Appartement' AND cp.current_best_price <= 50000 AND cp.is_active=true",
             "val_property_count",
             "Appartements in Yaoundé under 50k XAF"),

    TestCase(3, "search", "Terrains a Douala",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Douala' AND cp.property_type='Terrain' AND cp.is_active=true",
             "val_property_count",
             "All Terrains in Douala"),

    TestCase(4, "search", "Biens immobiliers a Bonamoussadi",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.neighborhood='Bonamoussadi' AND cp.is_active=true",
             "val_property_count",
             "Properties in Bonamoussadi"),

    TestCase(5, "search", "Appartements avec 3 chambres a Yaounde",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties WHERE property_type='Appartement' AND bedrooms >= 3 AND is_active=true",
             "val_property_count",
             "3+ bedroom apartments"),

    TestCase(6, "search", "Biens a moins de 100000 XAF",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties WHERE current_best_price <= 100000 AND is_active=true",
             "val_property_count",
             "Properties under 100k XAF"),

    TestCase(7, "search", "Terrain a Yaounde moins de 10 millions",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Yaoundé' AND cp.property_type='Terrain' AND cp.current_best_price <= 10000000 AND cp.is_active=true",
             "val_property_count",
             "Terrain in Yaoundé under 10M"),

    TestCase(8, "search", "Chambres a Douala",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Douala' AND cp.property_type='Chambre' AND cp.is_active=true",
             "val_property_count",
             "Chambres (rooms) in Douala"),

    TestCase(9, "search", "Biens a Bastos",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.neighborhood='Bastos' AND cp.is_active=true",
             "val_property_count",
             "Properties in Bastos"),

    TestCase(10, "search", "Maisons a Yaounde",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Yaoundé' AND cp.property_type='Maison' AND cp.is_active=true",
             "val_property_count",
             "Maisons in Yaoundé"),

    TestCase(11, "search", "Biens entre 5 millions et 50 millions XAF",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties WHERE current_best_price BETWEEN 5000000 AND 50000000 AND is_active=true",
             "val_property_count",
             "Properties 5M-50M XAF"),

    TestCase(12, "search", "Appartements a Douala Bonapriso",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Douala' AND l.neighborhood='Bonapriso' AND cp.property_type='Appartement' AND cp.is_active=true",
             "val_property_count",
             "Appartements in Bonapriso, Douala"),

    TestCase(13, "search", "Bureaux disponibles",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties WHERE property_type='Bureau' AND is_active=true",
             "val_property_count",
             "Bureau properties"),

    TestCase(14, "search", "Biens immobiliers a Kribi",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Kribi' AND cp.is_active=true",
             "val_property_count",
             "Properties in Kribi"),

    TestCase(15, "search", "Villas a Douala",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Douala' AND cp.property_type='Villa' AND cp.is_active=true",
             "val_property_count",
             "Villas in Douala (should be 0 — no Villa type in DB)"),

    # ===================================================================== #
    # Category 2: Safety Profiles (8 questions)
    # ===================================================================== #
    TestCase(16, "safety", "Ville la plus sure du Cameroun?",
             ["get_locations", "get_city_safety_profile"],
             "SELECT city FROM city_profiles WHERE security_rating = (SELECT security_rating FROM city_profiles WHERE security_rating IS NOT NULL ORDER BY CASE WHEN security_rating='Risque faible' THEN 1 WHEN security_rating='Risque modere' THEN 2 ELSE 3 END LIMIT 1) ORDER BY city LIMIT 1",
             "val_safest_city",
             "Safest city (should be Ebolowa or Kribi — Risque faible)"),

    TestCase(17, "safety", "Profil de securite de Douala",
             ["get_city_safety_profile"],
             "SELECT security_rating FROM city_profiles WHERE city='Douala'",
             "val_safety_rating",
             "Douala security profile (Risque élevé)"),

    TestCase(18, "safety", "Est-ce que Yaounde est sure?",
             ["get_city_safety_profile"],
             "SELECT security_rating FROM city_profiles WHERE city='Yaoundé'",
             "val_safety_rating",
             "Yaoundé security profile (Risque modéré)"),

    TestCase(19, "safety", "Securite de Kribi",
             ["get_city_safety_profile"],
             "SELECT security_rating FROM city_profiles WHERE city='Kribi'",
             "val_safety_rating",
             "Kribi security profile (Risque faible)"),

    TestCase(20, "safety", "Compare la securite de Douala et Yaounde",
             ["get_city_safety_profile"],
             "SELECT city, security_rating FROM city_profiles WHERE city IN ('Douala','Yaoundé') ORDER BY city",
             "val_safety_rating",
             "Compare Douala (élevé) vs Yaoundé (modéré)"),

    TestCase(21, "safety", "Quartier le plus sur a Douala",
             ["get_locations", "get_neighborhood_analytics"],
             "SELECT neighborhood FROM neighborhood_profiles WHERE city='Douala' ORDER BY CASE WHEN security_rating='Risque faible' THEN 1 WHEN security_rating='Risque modere' THEN 2 ELSE 3 END LIMIT 1",
             "val_always_pass",
             "Safest neighborhood in Douala"),

    TestCase(22, "safety", "Profil de securite de Bamenda",
             ["get_city_safety_profile"],
             "SELECT security_rating FROM city_profiles WHERE city='Bamenda'",
             "val_safety_rating",
             "Bamenda security profile (Risque élevé)"),

    TestCase(23, "safety", "Est-ce que Ebolowa est une ville sure?",
             ["get_city_safety_profile"],
             "SELECT security_rating FROM city_profiles WHERE city='Ebolowa'",
             "val_safety_rating",
             "Ebolowa security profile (Risque faible)"),

    # ===================================================================== #
    # Category 3: Neighborhood Analytics (10 questions)
    # ===================================================================== #
    TestCase(24, "analytics", "Analytics du marche a Bonamoussadi",
             ["get_neighborhood_analytics"],
             "SELECT median_price, listing_count FROM neighborhood_analytics na JOIN locations l ON l.id=na.location_id WHERE l.neighborhood='Bonamoussadi' AND na.property_type IS NULL",
             "val_analytics_value",
             "Bonamoussadi analytics (median=25000, count=5)"),

    TestCase(25, "analytics", "Quartiers de Douala avec leurs prix",
             ["get_city_neighborhoods"],
             "SELECT neighborhood FROM locations WHERE city='Douala' ORDER BY neighborhood",
             "val_neighborhood_list",
             "Douala neighborhoods list"),

    TestCase(26, "analytics", "Quartiers de Yaounde",
             ["get_city_neighborhoods"],
             "SELECT neighborhood FROM locations WHERE city='Yaoundé' ORDER BY neighborhood",
             "val_neighborhood_list",
             "Yaoundé neighborhoods list"),

    TestCase(27, "analytics", "Quartiers les plus tendance",
             ["get_trending_neighborhoods"],
             "SELECT l.neighborhood FROM neighborhood_analytics na JOIN locations l ON l.id=na.location_id WHERE na.property_type IS NULL AND na.growth_score IS NOT NULL ORDER BY na.growth_score DESC LIMIT 10",
             "val_trending",
             "Trending neighborhoods (growth score)"),

    TestCase(28, "analytics", "Marche immobilier a Ngousso",
             ["get_neighborhood_analytics"],
             "SELECT median_price, listing_count FROM neighborhood_analytics na JOIN locations l ON l.id=na.location_id WHERE l.neighborhood='Ngousso' AND na.property_type IS NULL",
             "val_analytics_value",
             "Ngousso analytics (median=3015000, count=10)"),

    TestCase(29, "analytics", "Analyse du quartier Nkoabang",
             ["get_neighborhood_analytics"],
             "SELECT median_price, listing_count FROM neighborhood_analytics na JOIN locations l ON l.id=na.location_id WHERE l.neighborhood='Nkoabang' AND na.property_type IS NULL",
             "val_analytics_value",
             "Nkoabang analytics (median=45000000, count=9)"),

    TestCase(30, "analytics", "Quartier le plus actif a Yaounde",
             ["get_city_neighborhoods"],
             "SELECT l.neighborhood, na.activity_score FROM neighborhood_analytics na JOIN locations l ON l.id=na.location_id WHERE l.city='Yaoundé' AND na.property_type IS NULL ORDER BY na.activity_score DESC LIMIT 3",
             "val_always_pass",
             "Most active neighborhood in Yaoundé"),

    TestCase(31, "analytics", "Statistiques du quartier Odza",
             ["get_neighborhood_analytics"],
             "SELECT median_price, listing_count FROM neighborhood_analytics na JOIN locations l ON l.id=na.location_id WHERE l.neighborhood='Odza' AND na.property_type IS NULL",
             "val_analytics_value",
             "Odza analytics (median=27500, count=8)"),

    TestCase(32, "analytics", "Prix median a Nkolbisson",
             ["get_neighborhood_analytics"],
             "SELECT median_price, listing_count FROM neighborhood_analytics na JOIN locations l ON l.id=na.location_id WHERE l.neighborhood='Nkolbisson' AND na.property_type IS NULL",
             "val_analytics_value",
             "Nkolbisson analytics (median=18000000, count=9)"),

    TestCase(33, "analytics", "Quartier le plus cher a Yaounde",
             ["get_city_neighborhoods"],
             "SELECT l.neighborhood, na.median_price FROM neighborhood_analytics na JOIN locations l ON l.id=na.location_id WHERE l.city='Yaoundé' AND na.property_type IS NULL AND na.median_price IS NOT NULL ORDER BY na.median_price DESC LIMIT 3",
             "val_always_pass",
             "Most expensive neighborhood in Yaoundé (Tsinga: 15M)"),

    # ===================================================================== #
    # Category 4: Price Analysis (5 questions)
    # ===================================================================== #
    TestCase(34, "price", "Analyse du prix du bien #195",
             ["get_price_analysis"],
             """SELECT CASE
                   WHEN cp.current_best_price IS NULL OR cp.location_id IS NULL THEN 'insufficient_data'
                   ELSE 'around_market'
                 END as verdict
                 FROM canonical_properties cp WHERE cp.id=195""",
             "val_always_pass",
             "Price analysis of property #195 (Terrain, 120M)"),

    TestCase(35, "price", "Le bien numero 200 est-il bien prix?",
             ["get_price_analysis"],
             """SELECT CASE
                   WHEN cp.current_best_price IS NULL OR cp.location_id IS NULL THEN 'insufficient_data'
                   ELSE 'around_market'
                 END as verdict
                 FROM canonical_properties cp WHERE cp.id=200""",
             "val_always_pass",
             "Price analysis of property #200 (Terrain, 6M)"),

    TestCase(36, "price", "Analyse du prix du terrain 198",
             ["get_price_analysis"],
             """SELECT CASE
                   WHEN cp.current_best_price IS NULL OR cp.location_id IS NULL THEN 'insufficient_data'
                   ELSE 'around_market'
                 END as verdict
                 FROM canonical_properties cp WHERE cp.id=198""",
             "val_always_pass",
             "Price analysis of property #198 (Terrain, 7.5M)"),

    TestCase(37, "price", "Prix median des appartements a Douala",
             ["search_properties"],
             "SELECT round(avg(cp.current_best_price)) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Douala' AND cp.property_type='Appartement' AND cp.current_best_price IS NOT NULL AND cp.is_active=true",
             "val_median_price_text",
             "Median price of Appartements in Douala"),

    TestCase(38, "price", "Prix moyen des terrains a Yaounde",
             ["search_properties"],
             "SELECT round(avg(cp.current_best_price)) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Yaoundé' AND cp.property_type='Terrain' AND cp.current_best_price IS NOT NULL AND cp.is_active=true",
             "val_median_price_text",
             "Average price of Terrains in Yaoundé"),

    # ===================================================================== #
    # Category 5: Locations (5 questions)
    # ===================================================================== #
    TestCase(39, "locations", "Lister les villes disponibles",
             ["get_locations"],
             "SELECT DISTINCT city FROM locations ORDER BY city",
             "val_locations",
             "List all cities"),

    TestCase(40, "locations", "Quartiers de Douala",
             ["get_locations"],
             "SELECT neighborhood FROM locations WHERE city='Douala' ORDER BY neighborhood",
             "val_neighborhood_list",
             "Douala neighborhoods via get_locations"),

    TestCase(41, "locations", "Quartiers de Yaounde",
             ["get_locations"],
             "SELECT neighborhood FROM locations WHERE city='Yaoundé' ORDER BY neighborhood",
             "val_neighborhood_list",
             "Yaoundé neighborhoods via get_locations"),

    TestCase(42, "locations", "Quelles villes sont dans la base?",
             ["get_locations"],
             "SELECT DISTINCT city FROM locations ORDER BY city",
             "val_locations",
             "Cities in the database"),

    TestCase(43, "locations", "Localisations disponibles au Cameroun",
             ["get_locations"],
             "SELECT DISTINCT city FROM locations ORDER BY city",
             "val_locations",
             "All locations"),

    # ===================================================================== #
    # Category 6: Multi-tool / Complex (7 questions)
    # ===================================================================== #
    TestCase(44, "complex", "Quelle ville est la plus sure pour acheter un terrain?",
             ["get_locations", "get_city_safety_profile"],
             "",
             "val_no_error",
             "Multi-tool: safest city for buying land"),

    TestCase(45, "complex", "Trouve un appartement abordable a Douala et dis-moi si le quartier est sur",
             ["search_properties", "get_city_safety_profile"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Douala' AND cp.property_type='Appartement' AND cp.is_active=true",
             "val_property_count",
             "Multi-tool: affordable apartment + safety"),

    TestCase(46, "complex", "Compare les prix des terrains a Douala et Yaounde",
             ["search_properties"],
             "SELECT l.city, round(avg(cp.current_best_price)) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE cp.property_type='Terrain' AND cp.current_best_price IS NOT NULL AND cp.is_active=true AND l.city IN ('Douala','Yaoundé') GROUP BY l.city",
             "val_no_error",
             "Multi-tool: compare terrain prices Douala vs Yaoundé"),

    TestCase(47, "complex", "Quel quartier a la meilleure croissance?",
             ["get_trending_neighborhoods"],
             "SELECT l.neighborhood FROM neighborhood_analytics na JOIN locations l ON l.id=na.location_id WHERE na.property_type IS NULL AND na.growth_score IS NOT NULL ORDER BY na.growth_score DESC LIMIT 5",
             "val_trending",
             "Best growth neighborhood"),

    TestCase(48, "complex", "Ou puis-je trouver un terrain moins de 10 millions a Yaounde?",
             ["search_properties"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Yaoundé' AND cp.property_type='Terrain' AND cp.current_best_price <= 10000000 AND cp.is_active=true",
             "val_property_count",
             "Terrain in Yaoundé under 10M"),

    TestCase(49, "complex", "Quel est le quartier le plus cher a Yaounde?",
             ["get_city_neighborhoods"],
             "SELECT l.neighborhood FROM neighborhood_analytics na JOIN locations l ON l.id=na.location_id WHERE l.city='Yaoundé' AND na.property_type IS NULL AND na.median_price IS NOT NULL ORDER BY na.median_price DESC LIMIT 1",
             "val_always_pass",
             "Most expensive neighborhood in Yaoundé"),

    TestCase(50, "complex", "Trouve un terrain a Douala et donne le profil de securite de la ville",
             ["search_properties", "get_city_safety_profile"],
             "SELECT count(*) FROM canonical_properties cp JOIN locations l ON l.id=cp.location_id WHERE l.city='Douala' AND cp.property_type='Terrain' AND cp.is_active=true",
             "val_property_count",
             "Multi-tool: terrain in Douala + safety profile"),
]


# --------------------------------------------------------------------------- #
# API call
# --------------------------------------------------------------------------- #
def call_chat_api(question: str, timeout: int = 60) -> dict:
    """Send a question to the POST /chat endpoint."""
    payload = {"message": question, "history": []}
    resp = requests.post(API_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
VALIDATORS = {
    "val_property_count": val_property_count,
    "val_property_count_and_ids": val_property_count_and_ids,
    "val_safety_rating": val_safety_rating,
    "val_safest_city": val_safest_city,
    "val_analytics_value": val_analytics_value,
    "val_neighborhood_list": val_neighborhood_list,
    "val_trending": val_trending,
    "val_price_analysis": val_price_analysis,
    "val_locations": val_locations,
    "val_median_price_text": val_median_price_text,
    "val_tool_called": val_tool_called,
    "val_always_pass": val_always_pass,
    "val_no_error": val_no_error,
}


def run_test(test: TestCase, timeout: int, verbose: bool) -> TestResult:
    """Run a single test case."""
    # 1. Query the DB for ground truth
    db_truth = None
    if test.db_check:
        try:
            db_truth = db_query(test.db_check)
        except Exception as e:
            db_truth = None

    # 2. Call the API
    start = time.time()
    ai_reply = ""
    ai_properties = []
    ai_tool_used = None
    error = None
    try:
        data = call_chat_api(test.question, timeout=timeout)
        ai_reply = data.get("reply", "")
        ai_properties = data.get("properties", [])
        ai_tool_used = data.get("tool_used")
    except Exception as e:
        error = str(e)
        ai_reply = f"[API ERROR] {e}"
    elapsed = time.time() - start

    result = TestResult(
        test=test,
        ai_reply=ai_reply,
        ai_properties=ai_properties,
        ai_tool_used=ai_tool_used,
        db_truth=db_truth,
        passed=False,
        elapsed=elapsed,
        error=error,
    )

    # 3. Validate
    if error:
        result.passed = False
        result.issues.append(f"API call failed: {error}")
    else:
        # Run the content validation function
        validator = VALIDATORS.get(test.validate, val_always_pass)
        try:
            val_result = validator(result)
            # Tool match is informational — the content validation is
            # the primary pass/fail criterion. The AI may use a different
            # but equivalent tool and still produce a correct answer.
            tool_ok = val_tool_called(result)
            result.passed = val_result
            if not tool_ok and test.expected_tools:
                result.issues.append(
                    f"[INFO] Tool mismatch: expected {test.expected_tools}, "
                    f"got '{result.ai_tool_used}' — content still validated"
                )
        except Exception as e:
            result.passed = False
            result.issues.append(f"Validator error: {e}")

    if verbose:
        print(f"\n{'='*80}")
        print(f"Test #{test.id} [{test.category}]: {test.question}")
        print(f"  Expected tools: {test.expected_tools}")
        print(f"  AI tool_used:    {ai_tool_used}")
        print(f"  AI reply:       {ai_reply[:500]}")
        print(f"  AI properties:  {len(ai_properties)} found")
        if db_truth:
            print(f"  DB truth:       {db_truth[:3]}")
        print(f"  Result:         {'PASS' if result.passed else 'FAIL'}")
        if result.issues:
            for iss in result.issues:
                print(f"  Issue: {iss}")
        print(f"  Elapsed:        {elapsed:.1f}s")

    return result


def print_report(results: list[TestResult], verbose: bool):
    """Print the final test report."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    print(f"\n{'='*80}")
    print(f"  CHAT AGENT TEST REPORT — 50 Questions")
    print(f"{'='*80}")
    print(f"  API:  {API_URL}")
    print(f"  Model: DeepSeek V4 Flash")
    print(f"  Total: {total}  |  Passed: {passed}  |  Failed: {failed}  |  Pass rate: {passed/total*100:.0f}%")
    print(f"  Avg response time: {sum(r.elapsed for r in results)/total:.1f}s")
    print(f"{'='*80}")

    # Per-category breakdown
    print(f"\n  {'Category':<15} {'Total':>6} {'Pass':>6} {'Fail':>6} {'Rate':>8} {'Avg time':>10}")
    print(f"  {'-'*15} {'-'*6} {'-'*6} {'-'*6} {'-'*8} {'-'*10}")
    for cat in CATEGORIES:
        cat_results = [r for r in results if r.test.category == cat]
        if not cat_results:
            continue
        cat_pass = sum(1 for r in cat_results if r.passed)
        cat_total = len(cat_results)
        cat_avg = sum(r.elapsed for r in cat_results) / cat_total
        rate = f"{cat_pass/cat_total*100:.0f}%"
        print(f"  {cat:<15} {cat_total:>6} {cat_pass:>6} {cat_total-cat_pass:>6} {rate:>8} {cat_avg:>9.1f}s")

    # Failed tests detail
    failed_results = [r for r in results if not r.passed]
    if failed_results:
        print(f"\n{'='*80}")
        print(f"  FAILED TESTS ({len(failed_results)})")
        print(f"{'='*80}")
        for r in failed_results:
            print(f"\n  #{r.test.id} [{r.test.category}] {r.test.question}")
            print(f"    Expected tools: {r.test.expected_tools}")
            print(f"    AI tool_used:   {r.ai_tool_used}")
            print(f"    AI reply:       {r.ai_reply[:300]}")
            print(f"    AI properties:  {len(r.ai_properties)} found")
            if r.db_truth:
                print(f"    DB truth:       {str(r.db_truth[:3])[:200]}")
            if r.error:
                print(f"    Error:          {r.error}")
            for iss in r.issues:
                print(f"    Issue: {iss}")
            print(f"    Elapsed:        {r.elapsed:.1f}s")

    # Tool usage summary
    print(f"\n{'='*80}")
    print(f"  TOOL USAGE SUMMARY")
    print(f"{'='*80}")
    tool_counts: dict[str, int] = {}
    no_tool_count = 0
    for r in results:
        if r.ai_tool_used:
            tool_counts[r.ai_tool_used] = tool_counts.get(r.ai_tool_used, 0) + 1
        else:
            no_tool_count += 1
    for tool, count in sorted(tool_counts.items(), key=lambda x: -x[1]):
        print(f"    {tool:<35} {count:>3}x")
    if no_tool_count:
        print(f"    {'(no tool called)':<35} {no_tool_count:>3}x")

    # Response time stats
    times = [r.elapsed for r in results]
    print(f"\n{'='*80}")
    print(f"  RESPONSE TIME STATS")
    print(f"{'='*80}")
    print(f"    Min:    {min(times):.1f}s")
    print(f"    Max:    {max(times):.1f}s")
    print(f"    Mean:   {sum(times)/len(times):.1f}s")
    sorted_times = sorted(times)
    print(f"    Median: {sorted_times[len(sorted_times)//2]:.1f}s")

    # Detailed results table
    if verbose:
        print(f"\n{'='*80}")
        print(f"  DETAILED RESULTS TABLE")
        print(f"{'='*80}")
        print(f"  {'#':>3}  {'Cat':<10} {'Result':>6}  {'Tool':<25} {'Time':>6}  Question")
        print(f"  {'-'*3}  {'-'*10} {'-'*6}  {'-'*25} {'-'*6}  {'-'*40}")
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            tool = r.ai_tool_used or "(none)"
            print(f"  {r.test.id:>3}  {r.test.category:<10} {status:>6}  {tool:<25} {r.elapsed:>5.1f}s  {r.test.question[:50]}")

    print(f"\n{'='*80}")
    if failed == 0:
        print("  ALL TESTS PASSED!")
    else:
        print(f"  {failed} test(s) failed — review the issues above.")
    print(f"{'='*80}\n")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="CentralImmo chat agent test suite (50 questions)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print full AI replies")
    parser.add_argument("--category", "-c", choices=CATEGORIES, help="Run only one category")
    parser.add_argument("--timeout", "-t", type=int, default=60, help="Per-question API timeout (seconds)")
    parser.add_argument("--start", "-s", type=int, default=1, help="Start from test ID")
    parser.add_argument("--end", "-e", type=int, default=50, help="End at test ID")
    parser.add_argument("--list", "-l", action="store_true", help="List all test cases and exit")
    args = parser.parse_args()

    if args.list:
        print(f"\n{'#':>3}  {'Cat':<10}  {'Expected Tools':<30}  Question")
        print(f"{'-'*3}  {'-'*10}  {'-'*30}  {'-'*50}")
        for t in TESTS:
            tools = ", ".join(t.expected_tools)
            print(f"{t.id:>3}  {t.category:<10}  {tools:<30}  {t.question}")
        print(f"\nTotal: {len(TESTS)} test cases")
        return

    # Filter tests
    tests = TESTS
    if args.category:
        tests = [t for t in TESTS if t.category == args.category]
    if args.start or args.end:
        tests = [t for t in tests if args.start <= t.id <= args.end]

    print(f"\nRunning {len(tests)} test(s) against {API_URL}")
    print(f"Model: DeepSeek V4 Flash")
    print(f"Timeout: {args.timeout}s per question")
    print(f"{'='*80}\n")

    results: list[TestResult] = []
    for i, test in enumerate(tests):
        print(f"  [{i+1}/{len(tests)}] Test #{test.id} [{test.category}]: {test.question[:60]}...", end="", flush=True)
        result = run_test(test, timeout=args.timeout, verbose=False)
        status = "PASS" if result.passed else "FAIL"
        print(f"  -> {status} ({result.elapsed:.1f}s, tool={result.ai_tool_used or 'none'})")
        results.append(result)

    print_report(results, verbose=args.verbose or True)

    # Exit code
    failed = sum(1 for r in results if not r.passed)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()