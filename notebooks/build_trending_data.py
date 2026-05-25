"""
build_trending_data.py
----------------------
Process the combined Instacart dataset (3.12 GB) to generate
time-aware trending product scores.

Uses chunked reading + vectorized pandas operations for memory efficiency.

Time Buckets:
  - Morning   (5-11)
  - Afternoon  (12-17)
  - Night      (18-4)

Weighted Score:
  weighted_score = 0.5 * normalized_purchase_frequency
                 + 0.3 * reorder_rate
                 + 0.2 * contextual_frequency

Outputs saved to ../outputs/:
  - trending_scores.parquet
  - trending_scores.csv
  - trending_departments.parquet
  - trending_lookup.pkl
"""

import os
import sys
import time
import pickle
import pandas as pd
import numpy as np

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "..", "data", "combined_instacart_data.csv")
OUTPUTS_DIR = os.path.join(SCRIPT_DIR, "..", "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)


# ── Time Bucket Mapping ──
def get_time_bucket(hour):
    """Assign time bucket: morning(5-11), afternoon(12-17), night(18-4)."""
    if 5 <= hour <= 11:
        return "morning"
    elif 12 <= hour <= 17:
        return "afternoon"
    else:
        return "night"


TIME_BUCKET_MAP = {h: get_time_bucket(h) for h in range(24)}

# Day names (Instacart convention: 0=Saturday, 1=Sunday, ..., 6=Friday)
DAY_NAMES = {0: "Saturday", 1: "Sunday", 2: "Monday", 3: "Tuesday",
             4: "Wednesday", 5: "Thursday", 6: "Friday"}


def load_data():
    """Load dataset with optimized dtypes for memory efficiency."""
    print("Loading dataset...")
    t0 = time.time()

    dtype_map = {
        "order_id": "int32",
        "product_id": "int32",
        "add_to_cart_order": "int16",
        "reordered": "int8",
        "user_id": "int32",
        "order_number": "int16",
        "order_dow": "int8",
        "order_hour_of_day": "int8",
        "aisle_id": "int16",
        "department_id": "int8",
    }

    # Only read columns we need
    use_cols = [
        "order_id", "product_id", "reordered", "order_dow",
        "order_hour_of_day", "product_name", "aisle", "department",
    ]

    df = pd.read_csv(
        DATA_PATH,
        usecols=use_cols,
        dtype={k: v for k, v in dtype_map.items() if k in use_cols},
    )

    elapsed = time.time() - t0
    print(f"Loaded {len(df):,} rows in {elapsed:.1f}s ({df.memory_usage(deep=True).sum() / 1e9:.2f} GB)")
    return df


def add_time_bucket(df):
    """Add time_bucket column using vectorized mapping."""
    print("Adding time buckets...")
    df["time_bucket"] = df["order_hour_of_day"].map(TIME_BUCKET_MAP)
    return df


def compute_product_trending_scores(df):
    """
    Compute weighted trending score per (product, day, time_bucket).

    weighted_score = 0.5 * norm_purchase_freq + 0.3 * reorder_rate + 0.2 * contextual_freq
    """
    print("\nComputing product trending scores...")
    t0 = time.time()

    # ── Step 1: Product × Day × TimeBucket aggregation ──
    context_agg = (
        df.groupby(["product_name", "department", "aisle", "order_dow", "time_bucket"])
        .agg(
            purchase_count=("order_id", "size"),
            reorder_sum=("reordered", "sum"),
            total_orders=("reordered", "size"),
        )
        .reset_index()
    )

    # ── Step 2: Reorder rate ──
    context_agg["reorder_rate"] = (
        context_agg["reorder_sum"] / context_agg["total_orders"]
    ).fillna(0)

    # ── Step 3: Normalized purchase frequency (within each day+time_bucket context) ──
    context_agg["normalized_purchase_frequency"] = (
        context_agg.groupby(["order_dow", "time_bucket"])["purchase_count"]
        .transform(lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0)
    )

    # ── Step 4: Contextual frequency (lift vs. product's overall average) ──
    # Global avg purchases per context for each product
    product_global_avg = (
        df.groupby("product_name")
        .size()
        .reset_index(name="global_count")
    )
    n_contexts = df[["order_dow", "time_bucket"]].drop_duplicates().shape[0]
    product_global_avg["global_avg_per_context"] = product_global_avg["global_count"] / n_contexts

    context_agg = context_agg.merge(product_global_avg[["product_name", "global_avg_per_context"]], on="product_name", how="left")

    # Contextual frequency = purchase_count / global_avg_per_context (capped at 3.0)
    context_agg["contextual_frequency_raw"] = (
        context_agg["purchase_count"] / context_agg["global_avg_per_context"]
    ).clip(upper=3.0)

    # Normalize contextual frequency to 0-1
    cf_min = context_agg["contextual_frequency_raw"].min()
    cf_max = context_agg["contextual_frequency_raw"].max()
    context_agg["contextual_frequency"] = (
        (context_agg["contextual_frequency_raw"] - cf_min) / (cf_max - cf_min)
        if cf_max > cf_min else 0
    )

    # ── Step 5: Weighted score ──
    context_agg["weighted_score"] = (
        0.5 * context_agg["normalized_purchase_frequency"]
        + 0.3 * context_agg["reorder_rate"]
        + 0.2 * context_agg["contextual_frequency"]
    )

    # Round float columns
    float_cols = ["reorder_rate", "normalized_purchase_frequency", "contextual_frequency", "weighted_score"]
    context_agg[float_cols] = context_agg[float_cols].round(4)

    # Sort by score within each context
    context_agg = context_agg.sort_values(
        ["order_dow", "time_bucket", "weighted_score"],
        ascending=[True, True, False],
    )

    # Drop helper columns
    context_agg = context_agg.drop(columns=["global_avg_per_context", "contextual_frequency_raw"], errors="ignore")

    elapsed = time.time() - t0
    print(f"  Computed {len(context_agg):,} (product × context) rows in {elapsed:.1f}s")
    return context_agg


def compute_department_trending(df):
    """Compute department-level trending scores."""
    print("\nComputing department trending scores...")

    dept_agg = (
        df.groupby(["department", "order_dow", "time_bucket"])
        .agg(
            purchase_count=("order_id", "size"),
            reorder_sum=("reordered", "sum"),
            total_orders=("reordered", "size"),
        )
        .reset_index()
    )

    dept_agg["reorder_rate"] = (dept_agg["reorder_sum"] / dept_agg["total_orders"]).fillna(0)

    dept_agg["normalized_frequency"] = (
        dept_agg.groupby(["order_dow", "time_bucket"])["purchase_count"]
        .transform(lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0)
    )

    dept_agg["trending_score"] = (
        0.6 * dept_agg["normalized_frequency"]
        + 0.4 * dept_agg["reorder_rate"]
    ).round(4)

    dept_agg = dept_agg.sort_values(
        ["order_dow", "time_bucket", "trending_score"],
        ascending=[True, True, False],
    )

    print(f"  {len(dept_agg):,} department × context rows")
    return dept_agg


def build_lookup_dict(scores_df, top_n=20, min_purchases=50):
    """
    Build pre-computed lookup dict for fast API serving.
    Filters out niche products and ensures they exist in frontend catalog.

    NOTE: No diversity reranking here — trending products should show the
    most contextually popular items by weighted_score. The reranker belongs
    in the personalized recommendation engine, not in trending.
    """
    print("\nBuilding lookup dict...")

    # Import frontend catalog
    sys.path.append(os.path.join(SCRIPT_DIR, "..", "backend"))
    try:
        from product_catalog import PRODUCTS
        valid_names_lower = set(p['name'].lower() for p in PRODUCTS)
    except ImportError:
        print("Warning: Could not load product_catalog. Using all products.")
        valid_names_lower = None

    lookup = {}
    for (dow, tb), group in scores_df.groupby(["order_dow", "time_bucket"]):
        # Filter to products with meaningful purchase volume
        filtered = group[group["purchase_count"] >= min_purchases]

        # Filter to valid catalog products
        if valid_names_lower is not None:
            filtered = filtered[filtered["product_name"].str.lower().isin(valid_names_lower)]

        # Take top_n by weighted_score — pure contextual popularity ranking
        top = filtered.nlargest(top_n, "weighted_score")

        products = []
        for _, row in top.iterrows():
            products.append({
                "product_name": row["product_name"],
                "department": row["department"],
                "aisle": row["aisle"],
                "score": float(row["weighted_score"]),
                "purchase_count": int(row["purchase_count"]),
                "reorder_rate": float(row["reorder_rate"]),
            })

        lookup[(int(dow), tb)] = products

    print(f"  {len(lookup)} context entries, {top_n} products each (min {min_purchases} purchases)")
    return lookup


def save_outputs(scores_df, dept_df, lookup):
    """Save all output artifacts."""
    print("\nSaving outputs...")

    # Parquet (fast loading)
    scores_path = os.path.join(OUTPUTS_DIR, "trending_scores.parquet")
    scores_df.to_parquet(scores_path, index=False)
    print(f"  [OK] {scores_path} ({os.path.getsize(scores_path) / 1e6:.1f} MB)")

    # CSV (human-readable)
    csv_path = os.path.join(OUTPUTS_DIR, "trending_scores.csv")
    scores_df.head(5000).to_csv(csv_path, index=False)  # Top 5000 only for readability
    print(f"  [OK] {csv_path} (top 5000 rows)")

    # Department scores
    dept_path = os.path.join(OUTPUTS_DIR, "trending_departments.parquet")
    dept_df.to_parquet(dept_path, index=False)
    print(f"  [OK] {dept_path} ({os.path.getsize(dept_path) / 1e6:.1f} MB)")

    # Lookup dict (pickle for instant API loading)
    pkl_path = os.path.join(OUTPUTS_DIR, "trending_lookup.pkl")
    with open(pkl_path, "wb") as f:
        pickle.dump(lookup, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"  [OK] {pkl_path} ({os.path.getsize(pkl_path) / 1e6:.1f} MB)")


def main():
    print("=" * 60)
    print("TIME-AWARE TRENDING PRODUCTS — Feature Engineering")
    print("=" * 60)
    total_start = time.time()

    # Load
    df = load_data()

    # Add time buckets
    df = add_time_bucket(df)

    # Verify time bucket distribution
    print("\nTime bucket distribution:")
    print(df["time_bucket"].value_counts().to_string())
    print(f"\nDay of week distribution:")
    print(df["order_dow"].map(DAY_NAMES).value_counts().to_string())

    # Compute scores
    scores_df = compute_product_trending_scores(df)
    dept_df = compute_department_trending(df)

    # Build lookup
    lookup = build_lookup_dict(scores_df)

    # Save
    save_outputs(scores_df, dept_df, lookup)

    # Summary
    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"DONE in {total_elapsed:.1f}s")
    print(f"  Products scored: {scores_df['product_name'].nunique():,}")
    print(f"  Contexts: {len(lookup)}")
    print(f"  Top product overall: {scores_df.iloc[0]['product_name']}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
