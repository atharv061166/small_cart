import sys
import json
from recommendation_engine import get_recommendations, _load_models
import reranker

def print_side_by_side(title, lists_dict):
    print(f"\n--- {title} ---")
    headers = list(lists_dict.keys())
    # Format headers
    header_str = " | ".join(f"{h:<30}" for h in headers)
    print(header_str)
    print("-" * len(header_str))
    
    max_len = max(len(l) for l in lists_dict.values())
    
    for i in range(max_len):
        row_items = []
        for h in headers:
            lst = lists_dict[h]
            name = lst[i]["product_name"] if i < len(lst) else ""
            row_items.append(f"{name:<30}")
        print(" | ".join(row_items))

if __name__ == "__main__":
    _load_models()
    cart = ["Organic Whole Milk", "Organic Baby Spinach"]
    
    original_rerank = reranker.rerank
    weights = [0.55, 0.75, 0.85]
    
    fp_results = {}
    lgbm_results = {}
    
    for w in weights:
        def temp_rerank(recs, diversity_weight=0.75):
            return original_rerank(recs, diversity_weight=w)
        reranker.rerank = temp_rerank
        
        fp_results[f"Weight {w}"] = get_recommendations(user_id=1, cart_items=cart, order_count=2, n=10)["recommendations"]
        lgbm_results[f"Weight {w}"] = get_recommendations(user_id=1, cart_items=[], order_count=15, n=10)["recommendations"]

    print_side_by_side("FP-Growth (Cold Start User)", fp_results)
    print_side_by_side("LightGBM (Active User)", lgbm_results)

    # STEP 4 check at 0.75
    target_items = ["Banana", "Organic Banana", "Bag of Organic Bananas", "Organic Strawberries", "Strawberries", "Organic Hass Avocado", "Avocado", "Organic Avocado"]
    
    fp_075 = [r["product_name"] for r in fp_results["Weight 0.75"][:3]]
    lgbm_075 = [r["product_name"] for r in lgbm_results["Weight 0.75"][:3]]
    
    fp_has_target = any(t in fp_075 for t in target_items)
    lgbm_has_target = any(t in lgbm_075 for t in target_items)
    
    if fp_has_target or lgbm_has_target:
        print("\n[!] Top 3 still dominated by popular items at 0.75. Re-running with 0.85 and checking...")
        fp_085 = [r["product_name"] for r in fp_results["Weight 0.85"][:3]]
        lgbm_085 = [r["product_name"] for r in lgbm_results["Weight 0.85"][:3]]
        
        fp_still_has = any(t in fp_085 for t in target_items)
        lgbm_still_has = any(t in lgbm_085 for t in target_items)
        
        if fp_still_has or lgbm_still_has:
            print("[!] Even at 0.85, popular items still in top 3.")
        else:
            print("[✓] At 0.85, popular items pushed out of top 3 successfully.")
            
        print("\n[ACTION REQUIRED] MUST UPDATE CODEBASE TO USE 0.85")
    else:
        print("\n[✓] At 0.75, popular items pushed out of top 3 successfully. Leaving default at 0.75.")
