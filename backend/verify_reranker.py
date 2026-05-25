import sys
import json
from recommendation_engine import get_recommendations
import reranker

def print_recs(title, before, after):
    print(f"\n--- {title} ---")
    print(f"{'BEFORE':<35} | {'AFTER':<35}")
    print("-" * 75)
    for i in range(max(len(before), len(after))):
        b = before[i]["product_name"] if i < len(before) else ""
        a = after[i]["product_name"] if i < len(after) else ""
        print(f"{b:<35} | {a:<35}")

if __name__ == "__main__":
    # Cart item to trigger FP-Growth
    cart = ["Organic Whole Milk", "Organic Baby Spinach"]
    
    # 1. Disable reranker temporarily by patching diversity_weight to 0
    print("Fetching BEFORE recommendations...")
    original_rerank = reranker.rerank
    
    def dummy_rerank(recs, diversity_weight=0.35):
        return original_rerank(recs, diversity_weight=0.0)
        
    reranker.rerank = dummy_rerank
    
    # Force load of models to avoid mixing output with our print statements
    from recommendation_engine import _load_models
    _load_models()
    
    fp_before = get_recommendations(user_id=1, cart_items=cart, order_count=2, n=10)["recommendations"]
    lgbm_before = get_recommendations(user_id=1, cart_items=[], order_count=15, n=10)["recommendations"]
    
    # 2. Enable reranker with diversity_weight = 0.35
    print("\nFetching AFTER recommendations (weight 0.35)...")
    def active_rerank(recs, diversity_weight=0.35):
        return original_rerank(recs, diversity_weight=0.35)
        
    reranker.rerank = active_rerank
    fp_after = get_recommendations(user_id=1, cart_items=cart, order_count=2, n=10)["recommendations"]
    lgbm_after = get_recommendations(user_id=1, cart_items=[], order_count=15, n=10)["recommendations"]
    
    print_recs("FP-Growth (Cold Start) weight=0.35", fp_before, fp_after)
    print_recs("LightGBM (Active User) weight=0.35", lgbm_before, lgbm_after)

    # Check if Bananas are still in top 3
    banana_terms = ["Banana", "Organic Banana", "Bag of Organic Bananas"]
    
    fp_top_3 = [r["product_name"] for r in fp_after[:3]]
    lgbm_top_3 = [r["product_name"] for r in lgbm_after[:3]]
    
    needs_increase = any(b in fp_top_3 for b in banana_terms) or any(b in lgbm_top_3 for b in banana_terms)
    
    if needs_increase:
        print("\nBananas still in top 3! Increasing diversity_weight to 0.5")
        
        # We also need to change recommendation_engine.py to use 0.5 permanently
        # but let's test it first.
        def heavy_rerank(recs, diversity_weight=0.35):
            return original_rerank(recs, diversity_weight=0.5)
            
        reranker.rerank = heavy_rerank
        fp_after_heavy = get_recommendations(user_id=1, cart_items=cart, order_count=2, n=10)["recommendations"]
        lgbm_after_heavy = get_recommendations(user_id=1, cart_items=[], order_count=15, n=10)["recommendations"]
        
        print_recs("FP-Growth (Cold Start) weight=0.5", fp_before, fp_after_heavy)
        print_recs("LightGBM (Active User) weight=0.5", lgbm_before, lgbm_after_heavy)
