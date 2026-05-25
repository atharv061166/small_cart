import os
import math
import pandas as pd

# Path to the Instacart dataset
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "combined_instacart_data.csv")

PRODUCT_GLOBAL_COUNTS = {}
MAX_GLOBAL_COUNT = 1

def _load_popularity():
    global PRODUCT_GLOBAL_COUNTS, MAX_GLOBAL_COUNT
    if not os.path.exists(DATA_PATH):
        print(f"Warning: {DATA_PATH} not found. Popularity counts will be 0.")
        return
        
    print("Pre-computing product popularity from combined_instacart_data.csv...")
    try:
        # Read only necessary columns to optimize memory usage
        df = pd.read_csv(DATA_PATH, usecols=["order_id", "product_name"])
        
        # Count unique orders per product
        counts = df.groupby("product_name")["order_id"].nunique().to_dict()
        PRODUCT_GLOBAL_COUNTS = counts
        if counts:
            MAX_GLOBAL_COUNT = max(counts.values())
        print(f"Loaded popularity for {len(counts)} products.")
    except Exception as e:
        print(f"Error loading popularity: {e}")

# Compute ONCE at startup
_load_popularity()

def rerank(recommendations: list[dict], diversity_weight: float = 0.8) -> list[dict]:
    """
    Re-ranks a list of recommendations (dicts with 'product_name') by penalizing popular items.
    """
    if not recommendations:
        return []
        
    n = len(recommendations)
    if n == 1:
        return recommendations
        
    scored_items = []
    
    for i, rec in enumerate(recommendations):
        product_name = rec.get("product_name")
        count = PRODUCT_GLOBAL_COUNTS.get(product_name, 0)
        
        # Rank score based on original position, normalized 0 to 1
        rank_score = (n - i - 1) / (n - 1)
        
        # Log-scaled popularity penalty
        penalty = math.log1p((count / MAX_GLOBAL_COUNT) * 100)
        
        scored_items.append({
            "rec": rec,
            "rank_score": rank_score,
            "raw_penalty": penalty
        })
        
    # Min-Max normalize penalty within the current list
    if scored_items:
        max_pen = max(item["raw_penalty"] for item in scored_items)
        min_pen = min(item["raw_penalty"] for item in scored_items)
    else:
        max_pen, min_pen = 0, 0
        
    for item in scored_items:
        if max_pen > min_pen:
            norm_penalty = (item["raw_penalty"] - min_pen) / (max_pen - min_pen)
        else:
            norm_penalty = 0.0
            
        item["final_score"] = item["rank_score"] - (diversity_weight * norm_penalty)
        
    # Return sorted descending by final_score
    scored_items.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Overwrite original score with the penalty-adjusted sorted score (scaled to [0.15, 0.95])
    if len(scored_items) > 1:
        max_fs = scored_items[0]["final_score"]
        min_fs = scored_items[-1]["final_score"]
        fs_range = max_fs - min_fs
        for item in scored_items:
            if fs_range > 0:
                norm_score = 0.15 + 0.8 * ((item["final_score"] - min_fs) / fs_range)
            else:
                norm_score = 0.5
            item["rec"]["score"] = round(norm_score, 4)
            
    return [item["rec"] for item in scored_items]
