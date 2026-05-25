# Models Folder — Recommendation Engine, Firebase Ingestion & LightGBM API Guide

This document describes how the adaptive recommendation engine works, how user transaction data is fetched in real time from Firebase Firestore, how live features are engineered, and how they are served to the LightGBM model for inference.

---

## Table of Contents
- [Overview of the Recommendation Architecture](#overview)
- [Firebase Authentication & Data Ingestion](#firebase-auth)
- [The Adaptive Switch Engine](#adaptive-switch)
- [Live Feature Engineering Pipeline](#live-features)
- [Model Inference & Reranking](#model-inference)
- [Recommendations API Specification](#api-spec)

---

## <a id="overview"></a>📊 Overview of the Recommendation Architecture

The recommendation system uses an **adaptive routing strategy** that selects the most suitable model based on a user's transaction history (order count). This solves the cold-start problem for new users while leveraging the power of gradient boosting (LightGBM) for highly active users.

```
                    [ POST /api/recommendations ]
                                 │
                     (Verify Firebase ID Token)
                                 │
                    [ Fetch User Order History ]
                     (Firestore / Memory Store)
                                 │
                   ───► Check User Order Count ◄───
                  │              │                 │
             (0-9 Orders)   (10-20 Orders)   (21+ Orders)
                  │              │                 │
                  ▼              ▼                 ▼
             [ FP-Growth ]   [ Hybrid ]       [ LightGBM ]
             + Popularity     MBA + LGBM       Inference
                  │              │                 │
                  └──────────────┼─────────────────┘
                                 ▼
                     [ Popularity Penalty ]
                                 │
                     [ Diversity Reranker ]
                                 │
                   [ Return Top-10 Products ]
```

---

## <a id="firebase-auth"></a>🔑 Firebase Authentication & Data Ingestion

### 1. Token Verification (Stateless JWT)
When a client requests recommendations from `/api/recommendations`, they pass a Firebase ID token in the `Authorization` header (`Bearer <token>`).
- The backend verifies this token statelessly in `verify_firebase_token()` using Google's public certificates (`https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com`).
- Upon successful validation, the backend extracts the Firebase User ID (`uid`).

### 2. Live Ingestion from Firestore
If the user is authenticated, the backend queries the database client (`db`) initialized using `backend/serviceAccountKey.json`.
- It fetches up to the **last 50 orders** placed by the user, sorted descending by creation time:
  ```python
  db.collection("users").document(uid).collection("orders")\
    .order_by("created_at", direction=firestore.Query.DESCENDING).limit(50).stream()
  ```
- **In-Memory Fallback**: If Firebase credentials are not provided (running locally without GCP configurations), the backend seamlessly falls back to an in-memory dictionary (`_memory_store[uid]["orders"]`) to retrieve the user's order history.

---

## <a id="adaptive-switch"></a>🏃 The Adaptive Switch Engine

Once the user's order history is loaded, the backend dynamically routes the request:

| User Segment | Order Count | Primary Recommendation Engine | Fallback Strategy |
| :--- | :--- | :--- | :--- |
| **New User** | 0 - 9 orders | **FP-Growth (Market Basket)**: Recommends items associated with the current cart using `mba_rules.pkl`. | Top popular products from the catalog. |
| **Growing User** | 10 - 20 orders | **Hybrid**: Blends and average-scores results from both FP-Growth and LightGBM. | Top popular products from the catalog. |
| **Active User** | 21+ orders | **LightGBM**: Personalizes recommendations by scoring candidate products. | Top popular products from the catalog. |

---

## <a id="live-features"></a>🔧 Live Feature Engineering Pipeline

When LightGBM is triggered (Hybrid or Active modes), the system must represent the user-product state as a feature matrix. Since user transactions live in Firestore and product features are pre-computed, the system constructs this matrix on the fly.

### Step 1: User & User-Product Features Extraction
`extract_live_features(user_orders)` iterates over the user's transaction history to compute:
- **User-level metrics**: Total orders and average basket size.
- **User-Product interaction metrics**: Purchase count (`up_times_ordered`), the index of their first order containing the item (`up_first_order_number`), and the index of the last order containing the item (`up_last_order_number`).
- **Recency & frequency**: Recency (`user_total_orders - up_last_order_number`) and frequency ratio (`up_times_ordered / user_total_orders`).

### Step 2: Popular Candidate Generation
If the model only scored products the user had previously bought, the user would never receive recommendations for new products.
- To solve this, the engine appends the **top 100 most popular products** in the store catalog as "candidates".
- For these candidates, interaction features are initialized to zero (`up_times_ordered = 0`, `up_first_order_number = 0`, `up_last_order_number = 0`).

### Step 3: Merging Pre-computed Product Features
The live user-product rows are merged with the static product features loaded from `train_features.parquet` on `product_id`:
- `product_total_orders`
- `product_unique_users`
- `product_reorder_rate`
- `product_avg_position`
- `aisle_id`
- `department_id`

### Step 4: Final Feature Schema
The feature matrix is aligned to match the schema in `lgbm_feature_cols.pkl`. It includes the following features:

| Feature Name | Level | Type | Description |
| :--- | :--- | :--- | :--- |
| `user_total_orders` | User | Integer | Total orders placed by the user. |
| `user_avg_basket_size` | User | Float | Average items per order. |
| `user_reorder_rate` | User | Float | Overall user reorder rate (defaulted to `0.5`). |
| `user_avg_days_since_prior` | User | Float | Average days between orders (defaulted to `7.0`). |
| `user_fav_hour` | User | Integer | Favorite hour of the day (defaulted to `12`). |
| `user_fav_dow` | User | Integer | Favorite day of the week (defaulted to `0` / Saturday). |
| `up_times_ordered` | Interaction | Integer | How many times this user ordered this product. |
| `up_reorder_rate` | Interaction | Float | Reorder rate of this product for this user. |
| `up_last_order_number` | Interaction | Integer | Index of the last order containing this product. |
| `up_first_order_number` | Interaction | Integer | Index of the first order containing this product. |
| `up_order_recency` | Interaction | Integer | Orders elapsed since the user last bought this product. |
| `up_order_freq_ratio` | Interaction | Float | Ratio of orders containing this product to user total orders. |
| `product_total_orders` | Product | Integer | Global popularity (total times ordered). |
| `product_unique_users` | Product | Integer | Global reach (number of unique users who bought it). |
| `product_reorder_rate` | Product | Float | Global reorder likelihood. |
| `product_avg_position` | Product | Float | Average position in the cart when added. |
| `aisle_id` | Product | Category | Categorical aisle identifier. |
| `department_id` | Product | Category | Categorical department identifier. |
| `product_log_popularity` | Engineered | Float | Log-normalized global popularity. |
| `user_vs_global_affinity` | Engineered | Float | User purchase frequency relative to global product popularity. |

---

## <a id="model-inference"></a>🔮 Model Inference & Reranking

### 1. Scoring (LightGBM Booster)
The aligned feature matrix is passed to the LightGBM model booster loaded from `lgbm_model.txt`:
```python
raw_scores = _lgbm_model.predict(X)
```

### 2. Popularity Penalty
To introduce diversity and prevent the model from always recommending the most popular items (like bananas or milk), the raw probability scores are penalized based on global popularity:
$$\text{Score} = \text{Raw Score} \times \left(1.0 - 0.3 \times \frac{\text{Product Total Orders}}{\text{Max Catalog Orders}}\right)$$

### 3. Cart Filtering & Diversity Reranking
- **Cart Filtering**: Products currently in the user's cart are removed from the recommendation candidates.
- **Reranker**: The remaining top candidates are passed through the diversity reranking algorithm (`backend/reranker.py`), which penalizes items belonging to departments/aisles that are already heavily represented. This ensures the final top 10 recommended items span a diverse set of categories.

---

## <a id="api-spec"></a>📡 Recommendations API Specification

### Endpoint
* **URL**: `/api/recommendations`
* **Method**: `POST`
* **Headers**: `Authorization: Bearer <Firebase_ID_Token>` (Optional)

### Request Body (`RecommendationRequest`)
```json
{
  "cart_items": ["Organic Banana", "Organic Whole Milk"],
  "order_count": 12,
  "user_id": 202279,
  "user_orders": []
}
```
*Note: If `user_orders` is empty and a valid Firebase token is present, the server fetches orders from Firestore.*

### Response
```json
{
  "engine": "lightgbm",
  "recommendations": [
    {
      "product_name": "Organic Strawberries",
      "score": 0.7452,
      "source": "lightgbm"
    },
    {
      "product_name": "Organic Hass Avocado",
      "score": 0.6121,
      "source": "lightgbm"
    }
  ]
}
```
