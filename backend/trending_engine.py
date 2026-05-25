"""
trending_engine.py
------------------
Lightweight contextual trending engine.
Loads pre-computed trending scores from ../outputs/ and serves
time-aware product recommendations.

No ML models — only aggregation-based weighted scoring.
"""

import os
import pickle
import pandas as pd
from datetime import datetime
from typing import Optional

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../outputs/")

# ── Constants ──
TIME_BUCKETS = {
    "morning": {"label": "Morning", "hours": "5 AM - 12 PM", "icon": "sunrise"},
    "afternoon": {"label": "Afternoon", "hours": "12 PM - 6 PM", "icon": "sun"},
    "night": {"label": "Night", "hours": "6 PM - 5 AM", "icon": "moon"},
}

# Instacart convention: 0=Saturday, 1=Sunday, ..., 6=Friday
DAY_NAMES = {0: "Saturday", 1: "Sunday", 2: "Monday", 3: "Tuesday",
             4: "Wednesday", 5: "Thursday", 6: "Friday"}

# Map Python weekday (0=Monday) to Instacart dow (0=Saturday)
PYTHON_WEEKDAY_TO_INSTACART = {
    0: 2,  # Monday
    1: 3,  # Tuesday
    2: 4,  # Wednesday
    3: 5,  # Thursday
    4: 6,  # Friday
    5: 0,  # Saturday
    6: 1,  # Sunday
}

# Department emoji mapping for non-catalog products
DEPARTMENT_EMOJIS = {
    "produce": "🥬", "dairy eggs": "🥛", "beverages": "☕",
    "snacks": "🍿", "bakery": "🍞", "frozen": "🧊",
    "breakfast": "🥣", "pantry": "🫙", "meat seafood": "🥩",
    "personal care": "🧴", "household": "🏠", "deli": "🥪",
    "dry goods pasta": "🍝", "canned goods": "🥫", "babies": "👶",
    "international": "🌍", "pets": "🐾", "alcohol": "🍷",
    "missing": "📦",
}

# ── Lazy-loaded globals ──
_trending_lookup = None
_trending_departments = None
_loaded = False


def _load_trending_data():
    """Load pre-computed trending artifacts."""
    global _trending_lookup, _trending_departments, _loaded

    if _loaded:
        return

    print("Loading trending engine data...")

    # Primary: pickle lookup (instant)
    pkl_path = os.path.join(OUTPUTS_DIR, "trending_lookup.pkl")
    if os.path.exists(pkl_path):
        with open(pkl_path, "rb") as f:
            _trending_lookup = pickle.load(f)
        print(f"  Trending lookup loaded -- {len(_trending_lookup)} contexts")
    else:
        print(f"  WARNING: {pkl_path} not found. Run notebooks/build_trending_data.py first.")
        _trending_lookup = {}

    # Department trends
    dept_path = os.path.join(OUTPUTS_DIR, "trending_departments.parquet")
    if os.path.exists(dept_path):
        _trending_departments = pd.read_parquet(dept_path)
        print(f"  Department trends loaded -- {len(_trending_departments)} rows")
    else:
        _trending_departments = pd.DataFrame()

    _loaded = True
    print("Trending engine ready.")


def get_time_bucket(hour: int) -> str:
    """Get time bucket for a given hour."""
    if 5 <= hour <= 11:
        return "morning"
    elif 12 <= hour <= 17:
        return "afternoon"
    else:
        return "night"


def get_current_context() -> tuple[int, str]:
    """Get current (instacart_dow, time_bucket) based on local time."""
    now = datetime.now()
    dow = PYTHON_WEEKDAY_TO_INSTACART[now.weekday()]
    tb = get_time_bucket(now.hour)
    return dow, tb


def _get_dept_emoji(department: str) -> str:
    """Get emoji for a department."""
    return DEPARTMENT_EMOJIS.get(department.lower().strip(), "📦")


def get_trending_products(dow: int, time_bucket: str, n: int = 10) -> list[dict]:
    """
    Get top-N trending products for a specific (day, time_bucket).

    Returns list of dicts with: product_name, department, aisle, score,
    purchase_count, reorder_rate, emoji, source
    """
    _load_trending_data()

    key = (dow, time_bucket)
    products = _trending_lookup.get(key, [])

    result = []
    for p in products[:n]:
        result.append({
            "product_name": p["product_name"],
            "department": p["department"],
            "aisle": p["aisle"],
            "score": round(p["score"], 4),
            "purchase_count": p["purchase_count"],
            "reorder_rate": round(p["reorder_rate"], 4),
            "emoji": _get_dept_emoji(p["department"]),
            "source": "trending",
        })

    return result


def get_trending_departments(dow: int, time_bucket: str, n: int = 5) -> list[dict]:
    """Get top-N trending departments for a context."""
    _load_trending_data()

    if _trending_departments is None or _trending_departments.empty:
        return []

    filtered = _trending_departments[
        (_trending_departments["order_dow"] == dow) &
        (_trending_departments["time_bucket"] == time_bucket)
    ].nlargest(n, "trending_score")

    result = []
    for _, row in filtered.iterrows():
        result.append({
            "department": row["department"],
            "score": round(float(row["trending_score"]), 4),
            "purchase_count": int(row["purchase_count"]),
            "reorder_rate": round(float(row["reorder_rate"]), 4),
            "emoji": _get_dept_emoji(row["department"]),
        })

    return result


def get_homepage_trending() -> dict:
    """
    Get trending data for homepage — auto-detects current time.

    Returns multiple sections:
    - trending_now: products trending for current context
    - popular_today: top products across all time buckets today
    - weekend_picks: popular weekend products (shown always)
    """
    _load_trending_data()

    dow, tb = get_current_context()
    day_name = DAY_NAMES.get(dow, "Today")
    bucket_info = TIME_BUCKETS.get(tb, {})

    # Section 1: Trending right now
    trending_now = get_trending_products(dow, tb, n=10)

    # Section 2: Popular today (merge all time buckets for this day)
    popular_today = []
    seen_products = set()
    for bucket in ["morning", "afternoon", "night"]:
        for p in get_trending_products(dow, bucket, n=10):
            if p["product_name"] not in seen_products:
                popular_today.append(p)
                seen_products.add(p["product_name"])
    # Sort by score and take top 10
    popular_today = sorted(popular_today, key=lambda x: x["score"], reverse=True)[:10]

    # Section 3: Weekend picks (Saturday=0, Sunday=1)
    weekend_picks = []
    seen_weekend = set()
    for weekend_dow in [0, 1]:  # Saturday, Sunday
        for bucket in ["morning", "afternoon", "night"]:
            for p in get_trending_products(weekend_dow, bucket, n=10):
                if p["product_name"] not in seen_weekend:
                    weekend_picks.append(p)
                    seen_weekend.add(p["product_name"])
    weekend_picks = sorted(weekend_picks, key=lambda x: x["score"], reverse=True)[:10]

    # Trending departments
    trending_depts = get_trending_departments(dow, tb, n=5)

    return {
        "day_name": day_name,
        "time_bucket": tb,
        "time_bucket_label": bucket_info.get("label", tb),
        "sections": {
            "trending_now": {
                "title": f"Trending This {bucket_info.get('label', tb.title())}",
                "subtitle": f"Popular on {day_name} {bucket_info.get('hours', '')}",
                "products": trending_now,
                "icon": "fire",
            },
            "popular_today": {
                "title": f"Popular Items for {day_name}",
                "subtitle": "Top picks across all times today",
                "products": popular_today,
                "icon": "chart",
            },
            "weekend_picks": {
                "title": "Popular on Weekends",
                "subtitle": "Weekend shopping favorites",
                "products": weekend_picks,
                "icon": "star",
            },
        },
        "trending_departments": trending_depts,
    }
