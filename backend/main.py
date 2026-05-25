"""
main.py
-------
FastAPI backend for Instacart Smart Grocery.
- Product catalog API
- Adaptive recommendations (LightGBM + FP-Growth)
- Order management via Firestore
- Firebase Auth token verification (no service account needed)
"""

import os
import json
import time
import requests as http_requests
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from jose import jwt, JWTError, jwk
from jose.utils import base64url_decode
import json
import pandas as pd

from product_catalog import (
    DEPARTMENTS, PRODUCTS, get_all_products,
    get_products_by_department, get_product_by_id,
)
from recommendation_engine import get_recommendations
from trending_engine import (
    get_trending_products, get_homepage_trending,
    get_trending_departments, get_time_bucket,
    TIME_BUCKETS, DAY_NAMES,
)

# ── Firebase Config ──
FIREBASE_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "small-cart-3f328")
GOOGLE_CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"

# Cache for Google's public certificates
_cached_certs = None
_certs_expiry = 0


def _get_google_certs():
    """Fetch and cache Google's public certificates for token verification."""
    global _cached_certs, _certs_expiry
    
    if _cached_certs and time.time() < _certs_expiry:
        return _cached_certs
    
    resp = http_requests.get(GOOGLE_CERTS_URL)
    resp.raise_for_status()
    _cached_certs = resp.json()
    # Cache for 1 hour
    _certs_expiry = time.time() + 3600
    return _cached_certs


def verify_firebase_token(token: str) -> dict:
    """
    Verify a Firebase ID token using Google's public certificates.
    No service account required.
    """
    # Decode header to get key ID
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
    except JWTError:
        raise ValueError("Invalid token header")
    
    if not kid:
        raise ValueError("Token missing key ID")
    
    # Get matching certificate
    certs = _get_google_certs()
    cert_pem = certs.get(kid)
    if not cert_pem:
        # Force refresh certs in case they rotated
        global _certs_expiry
        _certs_expiry = 0
        certs = _get_google_certs()
        cert_pem = certs.get(kid)
        if not cert_pem:
            raise ValueError("No matching certificate for token")
    
    # Verify and decode the token
    try:
        unverified = jwt.get_unverified_claims(token)
        aud = unverified.get("aud", FIREBASE_PROJECT_ID)
        payload = jwt.decode(
            token,
            cert_pem,
            algorithms=["RS256"],
            audience=aud,
            issuer=f"https://securetoken.google.com/{aud}",
        )
    except JWTError as e:
        raise ValueError(f"Token verification failed: {e}")
    
    # Validate required claims
    if not payload.get("sub"):
        raise ValueError("Token missing subject claim")
    
    # Add uid for compatibility
    payload["uid"] = payload["sub"]
    return payload


print(f"Firebase project: {FIREBASE_PROJECT_ID} (JWT verification, no service account needed)")

# ── Firestore (optional — only if service account exists) ──
db = None
SERVICE_ACCOUNT_PATH = os.environ.get(
    "FIREBASE_SERVICE_ACCOUNT",
    os.path.join(os.path.dirname(__file__), "serviceAccountKey.json"),
)
if os.path.exists(SERVICE_ACCOUNT_PATH):
    import firebase_admin
    from firebase_admin import credentials, firestore
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        # App already initialized (happens on reload)
        pass
    db = firestore.client()
    print("Firestore client ready.")
else:
    print("NOTE: No service account — Firestore disabled. Orders stored in memory.")

# In-memory fallback storage (when Firestore is not available)
_memory_store = {}  # uid -> {"orders": [...], "order_count": 0}

def _get_user_store(uid):
    if uid not in _memory_store:
        _memory_store[uid] = {"orders": [], "order_count": 0, "email": ""}
    return _memory_store[uid]


# ── FastAPI App ──
app = FastAPI(title="Instacart Smart Grocery API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve product images
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "../frontend/public/images")
if os.path.exists(IMAGES_DIR):
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")


# ── Auth Dependency ──
async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """Verify Firebase ID token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.split("Bearer ")[1]
    try:
        decoded = verify_firebase_token(token)
        return decoded
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def optional_token(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Optionally verify token — returns None if not provided."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split("Bearer ")[1]
        return verify_firebase_token(token)
    except Exception:
        return None


# ── Pydantic Models ──
class CartItem(BaseModel):
    product_id: str
    quantity: int = 1


class CreateOrderRequest(BaseModel):
    items: list[CartItem]
    coupon: Optional[dict] = None  # Coupon info: {amount, issued_at, ...}


class RecommendationRequest(BaseModel):
    cart_items: list[str] = []
    order_count: int = 0
    user_id: Optional[int] = None
    user_orders: Optional[list] = None


# ── Product Endpoints ──
@app.get("/api/departments")
async def list_departments():
    return {"departments": DEPARTMENTS}


@app.get("/api/products")
async def list_products(department: Optional[str] = None, search: Optional[str] = None):
    if department:
        products = get_products_by_department(department)
    else:
        products = get_all_products()

    if search:
        from rapidfuzz import process, fuzz, utils
        choices = [p["name"] for p in products]
        matches = process.extract(search, choices, scorer=fuzz.WRatio, processor=utils.default_process, score_cutoff=60, limit=None)
        products = [products[m[2]] for m in matches]

    return {"products": products}


@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product": product}


# ── Recommendation Endpoint ──
@app.post("/api/recommendations")
async def recommend(req: RecommendationRequest, user: Optional[dict] = Depends(optional_token)):
    user_orders = req.user_orders if req.user_orders is not None else []
    
    if user:
        if not user_orders:
            uid = user["uid"]
            if db is not None:
                from firebase_admin import firestore as fs
                orders_ref = db.collection("users").document(uid).collection("orders")
                docs = orders_ref.order_by("created_at", direction=fs.Query.DESCENDING).limit(50).stream()
                for doc in docs:
                    order = doc.to_dict()
                    order["id"] = doc.id
                    user_orders.append(order)
                print(f"[Recommendations] Fetched {len(user_orders)} live orders from Firestore for {uid}")
            else:
                store = _get_user_store(uid)
                user_orders = store.get("orders", [])
                print(f"[Recommendations] Fetched {len(user_orders)} orders from IN-MEMORY store for {uid}")
        else:
            print(f"[Recommendations] Using {len(user_orders)} orders provided in request payload for {user['uid']}")
    else:
        print("[Recommendations] Warning: No valid user token provided! Treating as anonymous.")

    if user and len(user_orders) == 0:
        print("[Recommendations] Warning: User is logged in but has 0 orders available to the backend! LightGBM cannot personalize.")

    result = get_recommendations(
        user_id=req.user_id,
        cart_items=req.cart_items,
        order_count=req.order_count,
        user_orders=user_orders,
        n=10,
    )
    return result


# ── Order Endpoints (Firestore with in-memory fallback) ──
@app.post("/api/orders")
async def create_order(req: CreateOrderRequest, user: dict = Depends(verify_token)):
    uid = user["uid"]

    # Build order items with product details
    order_items = []
    total = 0.0
    for item in req.items:
        product = get_product_by_id(item.product_id)
        if product:
            item_total = product["price"] * item.quantity
            order_items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "department": product["department"],
                "price": product["price"],
                "quantity": item.quantity,
                "item_total": round(item_total, 2),
                "emoji": product.get("emoji", "📦"),
            })
            total += item_total

    if not order_items:
        raise HTTPException(status_code=400, detail="No valid items in order")

    # Apply coupon discount if provided
    discount_amount = 0
    if req.coupon and isinstance(req.coupon, dict):
        discount_amount = req.coupon.get("amount", 0)
    
    final_total = max(0, round(total - discount_amount, 2))

    order_data = {
        "items": order_items,
        "subtotal": round(total, 2),
        "discount_amount": discount_amount,
        "total": final_total,
        "item_count": sum(i["quantity"] for i in order_items),
        "created_at": datetime.utcnow().isoformat(),
        "status": "completed",
    }

    if db is not None:
        # Save to Firestore
        now_iso = datetime.utcnow().isoformat() + "Z"
        order_data["created_at"] = now_iso
        order_ref = db.collection("users").document(uid).collection("orders").add(order_data)
        order_id = order_ref[1].id
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            current_count = user_data.get("order_count", 0)
            update_data = {
                "order_count": current_count + 1,
                "lastOrderAt": now_iso
            }
            # Check for coupon to consume
            coupon = user_data.get("coupon")
            if coupon and not coupon.get("is_used") and not coupon.get("expired"):
                coupon["is_used"] = True
                coupon["used_at"] = now_iso
                update_data["coupon"] = coupon
            
            user_ref.update(update_data)
        else:
            user_ref.set({"order_count": 1, "lastOrderAt": now_iso, "email": user.get("email", "")})
    else:
        # In-memory fallback
        import uuid
        now_iso = datetime.utcnow().isoformat() + "Z"
        order_data["created_at"] = now_iso
        
        order_id = str(uuid.uuid4())[:8]
        store = _get_user_store(uid)
        order_data["id"] = order_id
        store["orders"].insert(0, order_data)
        store["order_count"] += 1
        store["lastOrderAt"] = now_iso
        store["email"] = user.get("email", "")
        
        # Check for coupon to consume
        coupon = store.get("coupon")
        if coupon and not coupon.get("is_used") and not coupon.get("expired"):
            coupon["is_used"] = True
            coupon["used_at"] = now_iso
            store["coupon"] = coupon

    return {"order_id": order_id, "order": order_data}


@app.get("/api/orders")
async def list_orders(user: dict = Depends(verify_token)):
    uid = user["uid"]

    if db is not None:
        from firebase_admin import firestore as fs
        orders_ref = db.collection("users").document(uid).collection("orders")
        docs = orders_ref.order_by("created_at", direction=fs.Query.DESCENDING).stream()
        orders = []
        for doc in docs:
            order = doc.to_dict()
            order["id"] = doc.id
            orders.append(order)
        return {"orders": orders}
    else:
        store = _get_user_store(uid)
        return {"orders": store["orders"]}


@app.get("/api/user/profile")
async def get_user_profile(user: dict = Depends(verify_token)):
    uid = user["uid"]

    if db is not None:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        if user_doc.exists:
            data = user_doc.to_dict()
            
            # Auto-trigger coupon logic
            from datetime import datetime, timedelta, timezone
            last_order_at = data.get("lastOrderAt")
            order_count = data.get("order_count", data.get("orderCount", 0))
            coupon = data.get("coupon")
            
            # Clean up expired coupon
            if coupon and not coupon.get("is_used") and not coupon.get("expired"):
                try:
                    exp = datetime.fromisoformat(coupon["expires_at"].replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > exp:
                        coupon["expired"] = True
                        user_ref.update({"coupon.expired": True})
                        data["coupon"] = coupon
                except Exception as e:
                    print("Error checking expiry:", e)
            
            # Issue new coupon if qualifies
            config_path = os.path.join(os.path.dirname(__file__), "coupon_config.json")
            min_orders = 5
            min_days = 5
            max_days = 10
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        cfg = json.load(f)
                        min_orders = cfg.get("min_order_count", 5)
                        min_days = cfg.get("min_days_since_last_order", 5)
                        max_days = cfg.get("max_days_since_last_order", 10)
                except Exception:
                    pass
                    
            if order_count >= min_orders:
                # If the user has old orders but no lastOrderAt field, fetch it from their latest order
                if not last_order_at:
                    from firebase_admin import firestore as fs
                    try:
                        orders_ref = db.collection("users").document(uid).collection("orders")
                        latest_order = list(orders_ref.order_by("created_at", direction=fs.Query.DESCENDING).limit(1).stream())
                        if latest_order:
                            last_order_at = latest_order[0].to_dict().get("created_at")
                            if last_order_at:
                                user_ref.update({"lastOrderAt": last_order_at})
                                data["lastOrderAt"] = last_order_at
                    except Exception as e:
                        print("Failed to fetch latest order:", e)

                if last_order_at:
                    try:
                        last_date = datetime.fromisoformat(last_order_at.replace('Z', '+00:00'))
                        if last_date.tzinfo is None:
                            last_date = last_date.replace(tzinfo=timezone.utc)
                        days_since = (datetime.now(timezone.utc) - last_date).days
                        # Coupon eligible: not ordered for 5-10 days (reactivation window)
                        if min_days <= days_since <= max_days:
                            has_active_coupon = coupon and not coupon.get("is_used") and not coupon.get("expired")
                            if not has_active_coupon:
                                now = datetime.now(timezone.utc)
                                new_coupon = {
                                    "amount": 50,
                                    "issued_at": now.isoformat(),
                                    "expires_at": (now + timedelta(days=2)).isoformat(),
                                    "is_used": False,
                                    "message": "Shop fast! Your coupon expires soon."
                                }
                                user_ref.update({"coupon": new_coupon})
                                data["coupon"] = new_coupon
                    except Exception as e:
                        print("Error checking coupon eligibility:", e)
                    
            return data
        return {"order_count": 0, "email": user.get("email", ""), "coupon": None}
    else:
        store = _get_user_store(uid)
        
        # Auto-trigger coupon logic for in-memory store
        from datetime import datetime, timedelta, timezone
        last_order_at = store.get("lastOrderAt")
        order_count = store.get("order_count", 0)
        coupon = store.get("coupon")
        
        # Clean up expired coupon
        if coupon and not coupon.get("is_used") and not coupon.get("expired"):
            try:
                exp = datetime.fromisoformat(coupon["expires_at"].replace('Z', '+00:00'))
                if datetime.now(timezone.utc) > exp:
                    coupon["expired"] = True
                    store["coupon"] = coupon
            except Exception as e:
                print("Error checking expiry:", e)
                
        # Issue new coupon if qualifies
        config_path = os.path.join(os.path.dirname(__file__), "coupon_config.json")
        min_orders = 5
        min_days = 5
        max_days = 10
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    cfg = json.load(f)
                    min_orders = cfg.get("min_order_count", 5)
                    min_days = cfg.get("min_days_since_last_order", 5)
                    max_days = cfg.get("max_days_since_last_order", 10)
            except Exception:
                pass
                
        if order_count >= min_orders:
            if not last_order_at and store.get("orders"):
                last_order_at = store["orders"][0].get("created_at")
                store["lastOrderAt"] = last_order_at
                
            if last_order_at:
                try:
                    last_date = datetime.fromisoformat(last_order_at.replace('Z', '+00:00'))
                    if last_date.tzinfo is None:
                        last_date = last_date.replace(tzinfo=timezone.utc)
                    days_since = (datetime.now(timezone.utc) - last_date).days
                    # Coupon eligible: not ordered for 5-10 days (reactivation window)
                    if min_days <= days_since <= max_days:
                        has_active_coupon = coupon and not coupon.get("is_used") and not coupon.get("expired")
                        if not has_active_coupon:
                            now = datetime.now(timezone.utc)
                            new_coupon = {
                                "amount": 50,
                                "issued_at": now.isoformat(),
                                "expires_at": (now + timedelta(days=2)).isoformat(),
                                "is_used": False,
                                "message": "Shop fast! Your coupon expires soon."
                            }
                            store["coupon"] = new_coupon
                except Exception as e:
                    print("Error checking coupon eligibility:", e)
                    
        return {"order_count": store["order_count"], "email": store.get("email", user.get("email", "")), "coupon": store.get("coupon")}
# ── Trending Endpoints ──
@app.get("/api/trending")
async def trending(dow: int = 0, hour: int = 10, n: int = 10):
    """Get trending products for a specific day + time context."""
    if dow < 0 or dow > 6:
        raise HTTPException(status_code=400, detail="dow must be 0-6")
    if hour < 0 or hour > 23:
        raise HTTPException(status_code=400, detail="hour must be 0-23")

    time_bucket = get_time_bucket(hour)
    products = get_trending_products(dow, time_bucket, n=n)
    departments = get_trending_departments(dow, time_bucket, n=5)

    return {
        "day": DAY_NAMES.get(dow, str(dow)),
        "time_bucket": time_bucket,
        "time_bucket_info": TIME_BUCKETS.get(time_bucket, {}),
        "products": products,
        "departments": departments,
    }


@app.get("/api/trending/homepage")
async def trending_homepage():
    """Get trending sections for the homepage (auto-detects current time)."""
    return get_homepage_trending()


# ── Admin Dashboard Endpoints ──
@app.get("/api/admin/dashboard")
async def admin_dashboard():
    try:
        # Load precomputed CSVs
        base_dir = os.path.join(os.path.dirname(__file__), "../data/precomputed")
        
        orders_dow = pd.read_csv(os.path.join(base_dir, "orders_per_dow.csv")).to_dict(orient="records")
        orders_hour = pd.read_csv(os.path.join(base_dir, "orders_per_hour.csv")).to_dict(orient="records")
        top_overall = pd.read_csv(os.path.join(base_dir, "top_products_overall.csv")).to_dict(orient="records")
        dept_demand = pd.read_csv(os.path.join(base_dir, "dept_demand_dow.csv")).to_dict(orient="records")
        top_aisles = pd.read_csv(os.path.join(base_dir, "top_aisles.csv")).to_dict(orient="records")
        
        return {
            "orders_per_dow": orders_dow,
            "orders_per_hour": orders_hour,
            "top_products_overall": top_overall,
            "dept_demand_dow": dept_demand,
            "top_aisles_overall": top_aisles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/inventory")
async def admin_inventory(search: str = ""):
    try:
        # Load from product_dow_demand.json keys to get product names
        base_dir = os.path.join(os.path.dirname(__file__), "../data/precomputed")
        dow_path = os.path.join(base_dir, "product_dow_demand.json")
        
        if os.path.exists(dow_path):
            with open(dow_path, "r") as f:
                all_dow = json.load(f)
                product_names = list(all_dow.keys())
        else:
            # Fallback to catalog products
            from product_catalog import PRODUCTS
            product_names = [p["name"] for p in PRODUCTS]
            
        # Search/filter matching products
        if search:
            from rapidfuzz import process, fuzz, utils
            matches = process.extract(search, product_names, scorer=fuzz.WRatio, processor=utils.default_process, score_cutoff=60, limit=None)
            product_names = [m[0] for m in matches]
            
        # Return top 100 results formatted as [{"product_name": name}] to be compatible with frontend map
        result = [{"product_name": name} for name in product_names[:100]]
        return {"inventory": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/product/{product_name}")
async def admin_product_detail(product_name: str):
    try:
        base_dir = os.path.join(os.path.dirname(__file__), "../data/precomputed")
        dow_path = os.path.join(base_dir, "product_dow_demand.json")
        
        dow_demand = {}
        if os.path.exists(dow_path):
            with open(dow_path, "r") as f:
                all_dow = json.load(f)
                dow_demand = all_dow.get(product_name, {})
                
        # Calculate total orders as the sum of demand across all days
        total_orders = sum(int(val) for val in dow_demand.values())
        
        # Return with a structure compatible with existing frontend bindings (productDetails.info.total_orders and productDetails.dow_demand)
        return {
            "info": {
                "product_name": product_name,
                "total_orders": total_orders
            },
            "dow_demand": dow_demand
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Admin Segmentation Endpoint ──
@app.get("/api/admin/segmentation")
async def admin_segmentation():
    try:
        base_dir = os.path.join(os.path.dirname(__file__), "../data/precomputed")
        seg_df = pd.read_csv(os.path.join(base_dir, "user_segments.csv"))
        
        segment_counts = seg_df['segment'].value_counts().reset_index()
        segment_counts.columns = ['segment', 'count']
        
        avg_metrics = seg_df.groupby('segment').agg({
            'avg_basket_size': 'mean',
            'avg_reorder_rate': 'mean'
        }).reset_index()
        
        # New: avg order_number and days_since_prior_order per segment
        cluster_metrics = seg_df.groupby('segment').agg(
            avg_order_number=('order_number', 'mean'),
            avg_days_since_prior_order=('days_since_prior_order', 'mean')
        ).reset_index()
        cluster_metrics['avg_order_number'] = cluster_metrics['avg_order_number'].round(1)
        cluster_metrics['avg_days_since_prior_order'] = cluster_metrics['avg_days_since_prior_order'].round(1)

        scatter_sample = seg_df.sample(min(1000, len(seg_df)))[['user_id', 'days_since_prior_order', 'order_number', 'segment']].to_dict(orient='records')
        
        return {
            "counts": segment_counts.to_dict(orient='records'),
            "averages": avg_metrics.to_dict(orient='records'),
            "cluster_metrics": cluster_metrics.to_dict(orient='records'),
            "scatter": scatter_sample
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Health Check ──
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "firebase": db is not None,
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
