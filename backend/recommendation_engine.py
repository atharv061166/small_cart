"""
recommendation_engine.py
------------------------
Adaptive recommendation engine that switches between FP-Growth and LightGBM
based on user order count:
  - New user (0-9 orders)   → FP-Growth + Popularity
  - Growing  (10-20 orders) → Hybrid (both engines)
  - Active   (21+ orders)   → LightGBM

Loads pre-trained artifacts from ../outputs/
"""

import os
import joblib
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../outputs/")

# ── Mapping between frontend names and representative Instacart dataset product IDs ──
FRONTEND_TO_INSTACART_MAP = {
    # produce
    "banana": 24852,
    "organic banana": 37067,
    "organic_banana": 37067,
    "avocado": 48527,
    "strawberries": 16797,
    "lemon": 48455,
    "garlic": 34358,
    "onion": 47016,
    "tomato": 25162,
    "spinach": 48205,
    "apple": 48227,
    # dairy & eggs
    "whole milk": 4210,
    "whole_milk": 4210,
    "organic milk": 1463,
    "organic_milk": 1463,
    "greek yogurt": 45675,
    "greek_yogurt": 45675,
    "yogurt": 35073,
    "eggs": 5038,
    "butter": 5460,
    "cottage cheese": 36339,
    "cottage_cheese": 36339,
    "cheese sticks": 22035,
    "cheese_sticks": 22035,
    # bakery
    "bread": 20479,
    "whole wheat bread": 13517,
    "whole_wheat_bread": 13517,
    "tortillas": 19508,
    "bagels": 2071,
    # snacks
    "chips": 40709,
    "crackers": 31564,
    "granola bars": 27981,
    "granola_bars": 27981,
    "popcorn": 46061,
    "cookies": 25114,
    # beverages
    "sparkling water": 5258,
    "sparkling_water": 5258,
    "orange juice": 34050,
    "orange_juice": 34050,
    "almond milk": 35951,
    "almond_milk": 35951,
    "coffee": 48722,
    "soda": 196,
    # frozen
    "frozen pizza": 24561,
    "frozen_pizza": 24561,
    "ice cream": 43856,
    "ice_cream": 43856,
    "frozen vegetables": 14678,
    "frozen_vegetables": 14678,
    # breakfast
    "cereal": 20955,
    "oatmeal": 10229,
    "pancake mix": 46812,
    "pancake_mix": 46812,
    "granola": 17224,
    # pantry
    "rice": 49075,
    "pasta": 32734,
    "canned beans": 27156,
    "canned_beans": 27156,
    "olive oil": 9979,
    "olive_oil": 9979,
}

RULE_ITEM_TO_FRONTEND = {
    "bag of organic bananas": "Organic Banana",
    "banana": "Banana",
    "large lemon": "Lemon",
    "limes": "Lemon",
    "organic avocado": "Avocado",
    "organic baby spinach": "Spinach",
    "organic fuji apple": "Apple",
    "organic hass avocado": "Avocado",
    "organic raspberries": "Strawberries",
    "organic strawberries": "Strawberries",
    "organic whole milk": "Organic Milk",
    "strawberries": "Strawberries",
}

# ── Lazy-loaded globals ──
_lgbm_model = None
_lgbm_feature_cols = None
_lgbm_train = None
_product_names = None
_mba_rules = None
_models_loaded = False
_product_features = None
_name_to_pid = None


def _load_models():
    """Load all model artifacts once."""
    global _lgbm_model, _lgbm_feature_cols, _lgbm_train, _product_names, _mba_rules, _models_loaded, _product_features

    if _models_loaded:
        return

    print("Loading recommendation engine artifacts...")

    # LightGBM
    try:
        import lightgbm as lgb
        lgbm_path = os.path.join(OUTPUTS_DIR, "lgbm_model.txt")
        if os.path.exists(lgbm_path):
            _lgbm_model = lgb.Booster(model_file=lgbm_path)
            _lgbm_feature_cols = joblib.load(os.path.join(OUTPUTS_DIR, "lgbm_feature_cols.pkl"))
            _lgbm_train = pd.read_parquet(os.path.join(OUTPUTS_DIR, "train_features.parquet"))
            _product_features = _lgbm_train[["product_id", "product_total_orders", "product_unique_users", "product_reorder_rate", "product_avg_position", "aisle_id", "department_id"]].drop_duplicates("product_id")
            print(f"  LightGBM loaded — {len(_lgbm_train):,} rows")
        else:
            print("  LightGBM model not found — skipping")
    except Exception as e:
        print(f"  LightGBM load error: {e}")

    # Product names
    try:
        pn_path = os.path.join(OUTPUTS_DIR, "product_names.parquet")
        if os.path.exists(pn_path):
            _product_names = pd.read_parquet(pn_path)
            print(f"  Product names loaded — {len(_product_names):,}")
    except Exception as e:
        print(f"  Product names load error: {e}")

    # FP-Growth rules
    try:
        rules_path = os.path.join(OUTPUTS_DIR, "mba_rules.pkl")
        if os.path.exists(rules_path):
            _mba_rules = joblib.load(rules_path)
            print(f"  FP-Growth rules loaded — {len(_mba_rules):,} rules")
        else:
            print("  FP-Growth rules not found — skipping")
    except Exception as e:
        print(f"  FP-Growth rules load error: {e}")

    _models_loaded = True
    print("Recommendation engine ready.")


# ── FP-Growth Recommendations ──

def _department_recommend(cart_items: list[str], exclude_names: list[str] = None, n: int = 10) -> list[dict]:
    from product_catalog import PRODUCTS, POPULARITY_RANKING
    exclude = set(nm.lower() for nm in (exclude_names or []))
    recs = []
    
    cart_depts = set()
    for c in cart_items:
        prod = next((p for p in PRODUCTS if p["name"].lower() == c.lower()), None)
        if prod and prod.get("department"):
            cart_depts.add(prod["department"])
            
    if not cart_depts:
        return []
        
    for pid in POPULARITY_RANKING:
        prod = next((p for p in PRODUCTS if p["id"] == pid), None)
        if prod and prod["department"] in cart_depts and prod["name"].lower() not in exclude:
            recs.append({
                "product_name": prod["name"],
                "score": round(0.5 - len(recs) * 0.01, 4),
                "source": "fp_growth",
            })
            if len(recs) >= n:
                break
                
    return recs

def _fpgrowth_recommend(cart_items: list[str], n: int = 10) -> list[dict]:
    """
    Given a list of product names in the cart, find associated products
    using FP-Growth association rules.
    """
    _load_models()

    if _mba_rules is None or len(cart_items) == 0:
        return []

    basket_set = set(p.strip().lower() for p in cart_items)
    
    # Expand basket_set to include matched rule names
    rule_to_frontend_lower = {k: v.lower() for k, v in RULE_ITEM_TO_FRONTEND.items()}
    frontend_to_rule_lower = {}
    for rule_item, frontend_item in rule_to_frontend_lower.items():
        if frontend_item not in frontend_to_rule_lower:
            frontend_to_rule_lower[frontend_item] = []
        frontend_to_rule_lower[frontend_item].append(rule_item)
        
    expanded_basket = set()
    for item in basket_set:
        expanded_basket.add(item)
        if item in frontend_to_rule_lower:
            expanded_basket.update(frontend_to_rule_lower[item])
            
    recs = {}

    for _, rule in _mba_rules.iterrows():
        antecedent = set(x.lower() for x in rule["antecedents"])
        consequent = set(x.lower() for x in rule["consequents"])

        if antecedent.issubset(expanded_basket):
            for product in consequent:
                frontend_name = RULE_ITEM_TO_FRONTEND.get(product, product)
                if frontend_name.lower() not in basket_set:
                    if frontend_name not in recs or recs[frontend_name]["lift"] < rule["lift"]:
                        recs[frontend_name] = {
                            "product_name": frontend_name,
                            "confidence": round(float(rule["confidence"]), 4),
                            "lift": round(float(rule["lift"]), 4),
                            "source": "fp_growth",
                            "score": round(float(rule["lift"]) * float(rule["confidence"]), 4),
                        }

    sorted_recs = sorted(recs.values(), key=lambda x: x["score"], reverse=True)[:n]
    
    if len(sorted_recs) < n and len(cart_items) > 0:
        exclude = [r["product_name"] for r in sorted_recs] + cart_items
        dept_recs = _department_recommend(cart_items, exclude_names=exclude, n=n - len(sorted_recs))
        sorted_recs.extend(dept_recs)
        
    return sorted_recs[:n]


def _popularity_recommend(exclude_names: list[str] = None, n: int = 10) -> list[dict]:
    """
    Fallback: recommend the most popular products from the catalog.
    """
    from product_catalog import POPULARITY_RANKING, PRODUCTS

    exclude = set(exclude_names or [])
    recs = []

    for pid in POPULARITY_RANKING:
        prod = next((p for p in PRODUCTS if p["id"] == pid), None)
        if prod and prod["name"] not in exclude:
            recs.append({
                "product_name": prod["name"],
                "score": round(1.0 - len(recs) * 0.02, 4),
                "source": "popularity",
            })
            if len(recs) >= n:
                break

    return recs


# ── LightGBM Recommendations ──

def extract_live_features(user_orders):
    import pandas as pd
    global _product_features, _product_names, _name_to_pid
    if not user_orders:
        return pd.DataFrame()
        
    if _name_to_pid is None and _product_names is not None:
        _name_to_pid = {str(name).lower(): pid for pid, name in zip(_product_names["product_id"], _product_names["product_name"])}
        
    user_total_orders = len(user_orders)
    total_items = sum(len(o.get("items", [])) for o in user_orders)
    user_avg_basket_size = total_items / user_total_orders if user_total_orders else 0
    
    product_stats = {}
    for i, order in enumerate(reversed(user_orders)):
        order_num = i + 1
        for item in order.get("items", []):
            name = str(item.get("product_name", item.get("name", ""))).lower().strip()
            prod_id_str = str(item.get("product_id", "")).lower().strip()
            
            # Map using FRONTEND_TO_INSTACART_MAP
            pid = None
            if name in FRONTEND_TO_INSTACART_MAP:
                pid = FRONTEND_TO_INSTACART_MAP[name]
            elif prod_id_str in FRONTEND_TO_INSTACART_MAP:
                pid = FRONTEND_TO_INSTACART_MAP[prod_id_str]
            elif _name_to_pid and name in _name_to_pid:
                pid = _name_to_pid[name]
            else:
                try:
                    pid = int(item.get("product_id", 0))
                except:
                    continue
                    
            if pid not in product_stats:
                product_stats[pid] = {
                    "up_times_ordered": 0,
                    "up_first_order_number": order_num,
                }
            product_stats[pid]["up_times_ordered"] += 1
            product_stats[pid]["up_last_order_number"] = order_num
            
    # Add candidate items so LightGBM always has enough items to score
    valid_pids = set(FRONTEND_TO_INSTACART_MAP.values())
    for pid in valid_pids:
        if pid not in product_stats:
            product_stats[pid] = {
                "up_times_ordered": 0,
                "up_first_order_number": 0,
                "up_last_order_number": 0,
            }
            
    rows = []
    for pid, stats in product_stats.items():
        if pid not in valid_pids:
            continue
            
        up_times_ordered = stats["up_times_ordered"]
        up_first_order = stats["up_first_order_number"]
        up_last_order = stats["up_last_order_number"]
        
        possible_orders = user_total_orders - up_first_order + 1
        up_reorder_rate = up_times_ordered / possible_orders if possible_orders > 0 else 0
        up_order_recency = user_total_orders - up_last_order
        up_order_freq_ratio = up_times_ordered / user_total_orders if user_total_orders > 0 else 0
        
        rows.append({
            "product_id": pid,
            "user_total_orders": user_total_orders,
            "user_avg_basket_size": user_avg_basket_size,
            "user_reorder_rate": 0.5,
            "user_avg_days_since_prior": 7.0,
            "user_fav_hour": 12,
            "user_fav_dow": 0,
            "up_times_ordered": up_times_ordered,
            "up_reorder_rate": up_reorder_rate,
            "up_last_order_number": up_last_order,
            "up_first_order_number": up_first_order,
            "up_order_recency": up_order_recency,
            "up_order_freq_ratio": up_order_freq_ratio,
        })
    return pd.DataFrame(rows)


def _lightgbm_recommend(user_id: int = None, user_orders: list = None, n: int = 10, cart_items: list[str] = None) -> list[dict]:
    """
    Get top-N product recommendations using LightGBM from live orders or historical data.
    """
    _load_models()

    if _lgbm_model is None or _lgbm_train is None:
        return []

    if user_orders:
        user_data = extract_live_features(user_orders)
        if not user_data.empty and _product_features is not None:
            user_data = user_data.merge(_product_features, on="product_id", how="left")
            
            # Compute missing engineered features expected by the model
            TOTAL_ORDERS = 3214874.0
            user_data["product_log_popularity"] = np.log1p(user_data["product_total_orders"].fillna(0))
            denom = user_data["product_total_orders"].fillna(0) / TOTAL_ORDERS
            user_data["user_vs_global_affinity"] = user_data["up_order_freq_ratio"] / denom.replace(0, np.nan)
            user_data["user_vs_global_affinity"] = user_data["user_vs_global_affinity"].fillna(0.0)
    elif user_id:
        user_data = _lgbm_train[_lgbm_train["user_id"] == user_id].copy()
    else:
        return []

    if user_data.empty:
        return []

    # Restrict user_data to only items that exist in the frontend catalog
    valid_pids = set(FRONTEND_TO_INSTACART_MAP.values())
    user_data = user_data[user_data["product_id"].isin(valid_pids)]

    if user_data.empty:
        return []

    X = user_data[_lgbm_feature_cols].fillna(0).astype("float32")
    raw_scores = _lgbm_model.predict(X)

    # Apply popularity penalty
    max_pop = user_data["product_total_orders"].max()
    if max_pop > 0:
        normalized_popularity = user_data["product_total_orders"] / max_pop
    else:
        normalized_popularity = 0
        
    user_data["score"] = raw_scores * (1 - 0.3 * normalized_popularity)

    top = user_data.nlargest(n, "score")[["product_id", "score"]]

    # Map the product IDs back to frontend names
    from product_catalog import PRODUCTS
    id_to_frontend_name = {}
    for p in PRODUCTS:
        fname = p["name"].lower().strip()
        fid = p["id"].lower().strip()
        if fname in FRONTEND_TO_INSTACART_MAP:
            id_to_frontend_name[FRONTEND_TO_INSTACART_MAP[fname]] = p["name"]
        if fid in FRONTEND_TO_INSTACART_MAP:
            id_to_frontend_name[FRONTEND_TO_INSTACART_MAP[fid]] = p["name"]
    
    cart_set = set(p.lower().strip() for p in (cart_items or []))
    
    recs = []
    for _, row in top.iterrows():
        pid = int(row["product_id"])
        name = id_to_frontend_name.get(pid, f"Product {pid}")
        if name.lower().strip() not in cart_set:
            recs.append({
                "product_name": name,
                "score": round(float(row["score"]), 4),
                "source": "lightgbm",
            })

    return recs


# ── Unified Adaptive Engine ──

def get_recommendations(
    user_id: int | None = None,
    cart_items: list[str] | None = None,
    order_count: int = 0,
    user_orders: list = None,
    n: int = 10,
) -> dict:
    """
    Adaptive recommendation engine:
      - order_count 0-9   → FP-Growth + Popularity (cold start)
      - order_count 10-20 → Hybrid (FP-Growth + LightGBM)
      - order_count 21+   → LightGBM
    
    Returns:
        {
            "engine": "fp_growth" | "hybrid" | "lightgbm",
            "recommendations": [{"product_name": ..., "score": ..., "source": ...}, ...]
        }
    """
    _load_models()
    cart_items = cart_items or []

    # Sync order_count with the length of user_orders if available
    if user_orders is not None:
        order_count = max(order_count, len(user_orders))

    # ── New user: FP-Growth + Popularity ──
    if order_count < 10:
        fp_recs = _fpgrowth_recommend(cart_items, n=n)
        
        if len(fp_recs) < n:
            exclude = [r["product_name"] for r in fp_recs] + cart_items
            pop_recs = _popularity_recommend(exclude_names=exclude, n=n - len(fp_recs))
            fp_recs.extend(pop_recs)

        from reranker import rerank
        final_recs = rerank(fp_recs, diversity_weight=0.75)
        return {"engine": "fp_growth", "recommendations": final_recs[:n]}

    # ── Growing user: Hybrid ──
    elif order_count <= 20:
        fp_recs = _fpgrowth_recommend(cart_items, n=n)
        lgbm_recs = _lightgbm_recommend(user_id=user_id, user_orders=user_orders, n=n, cart_items=cart_items) if (user_id or user_orders) else []

        # Merge: LightGBM products get boosted, FP-Growth products get basket context
        merged = {}
        for r in fp_recs:
            key = r["product_name"]
            merged[key] = {**r, "score": r["score"] * 0.5}
        
        for r in lgbm_recs:
            key = r["product_name"]
            if key in merged:
                merged[key]["score"] += r["score"] * 0.5
                merged[key]["source"] = "hybrid"
            else:
                merged[key] = {**r, "score": r["score"] * 0.5}

        sorted_merged = sorted(merged.values(), key=lambda x: x["score"], reverse=True)

        if len(sorted_merged) < n:
            exclude = [r["product_name"] for r in sorted_merged] + cart_items
            pop_recs = _popularity_recommend(exclude_names=exclude, n=n - len(sorted_merged))
            sorted_merged.extend(pop_recs)

        from reranker import rerank
        final_recs = rerank(sorted_merged, diversity_weight=0.75)
        return {"engine": "hybrid", "recommendations": final_recs[:n]}

    # ── Active user: LightGBM ──
    else:
        lgbm_recs = _lightgbm_recommend(user_id=user_id, user_orders=user_orders, n=n, cart_items=cart_items) if (user_id or user_orders) else []

        if len(lgbm_recs) < n:
            exclude = [r["product_name"] for r in lgbm_recs] + cart_items
            pop_recs = _popularity_recommend(exclude_names=exclude, n=n - len(lgbm_recs))
            lgbm_recs.extend(pop_recs)

        from reranker import rerank
        final_recs = rerank(lgbm_recs, diversity_weight=0.75)
        return {"engine": "lightgbm", "recommendations": final_recs[:n]}
