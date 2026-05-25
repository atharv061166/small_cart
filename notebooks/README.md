# Notebooks Folder — Comprehensive Guide

This document describes all the scripts and notebooks in the `notebooks/` folder, their purpose, their input datasets, the outputs they generate, and how they connect to the recommendation models and the dashboard.

---

## 📊 Overview

The `notebooks/` folder contains exploratory data analysis (EDA), feature engineering, and model prototyping pipelines. These notebooks and scripts process raw transaction data into pre-computed features, model inputs, segmentation data, and inventory metrics, which are then used by the machine learning models, backend recommendation engine, and frontend dashboard.

The folder is structured as follows:
- **Root Directory**: Recommender feature engineering and time-aware trending product score generation.
- **`customer_segmentation/`**: Behavioral analysis and K-Means user clustering.
- **`demand_forecasting/`**: Product demand analysis and supply chain inventory planning.

---

## 📁 Notebooks & Scripts

### 1. **eda.ipynb**

**Type**: Jupyter Notebook

#### 📝 Description
Exploratory Data Analysis (EDA) of the raw Instacart transaction dataset. It analyzes overall dataset statistics, unique users, missing values, ordering distributions by hour of day, day of week, and department popularity.

#### 🔧 Inputs
- `data/combined_instacart_data.csv`

#### 💾 Outputs
- None (purely exploratory visualizations and summaries)

#### 🎯 Purpose
Establishes a baseline understanding of dataset patterns, missing data (e.g., first orders), and customer shopping behavior.

---

### 2. **eda_trending_products.ipynb**

**Type**: Jupyter Notebook

#### 📝 Description
Exploratory analysis focused specifically on trending products across different time buckets. It researches and tests the trending scoring algorithm.

#### 🔧 Inputs
- `data/combined_instacart_data.csv`

#### 💾 Outputs
- None (exploratory notebook for prototyping)

#### 🎯 Purpose
Helped test the trending scoring algorithm, weighting coefficients, and contextual lift limits before they were converted into the production script.

---

### 3. **feature_engineering.ipynb**

**Type**: Jupyter Notebook

#### 📝 Description
The main feature engineering notebook for the recommender model. It constructs three levels of features: user-level, product-level, and user-product interaction level.

#### 🔧 Inputs
- `data/combined_instacart_data.csv`

#### 💾 Outputs
- `outputs/train_features.parquet` — Engineered training matrix containing target labels,all features.
- `outputs/product_names.parquet` — Product ID to name, aisle, and department metadata mapping table.
- `outputs/order_products.parquet` — Substrate order-product mapping file used for market basket rules extraction.

#### 🎯 Purpose
Constructs the primary training feature matrix used to train the LightGBM recommender model.

---

### 4. **feature_engineering_trending.ipynb**

**Type**: Jupyter Noteboo

#### 📝 Description
Interactive notebook version of `build_trending_data.py`, performing the same time-aware trending score calculations and outputting the same trending artifacts.

#### 🔧 Inputs
- `data/combined_instacart_data.csv`

#### 💾 Outputs
- `outputs/trending_scores.parquet`
- `outputs/trending_scores.csv`
- `outputs/trending_departments.parquet`
- `outputs/trending_lookup.pkl`

#### 🎯 Purpose
Used during development to test the diversity reranking algorithm and verify contextual frequency distribution before moving to the Python script version.

---

### 5. **customer_segmentation/customer_segmentation_eda.ipynb**

**Type**: Jupyter Notebook

#### 📝 Description
Exploratory analysis of customer order recency (days since prior order), frequency (total orders), basket size, and reorder rates to define thresholds for user dormancy.

#### 🔧 Inputs
- `data/combined_instacart_data.csv`

#### 💾 Outputs
- `data/precomputed/user_features.csv` — Pre-computed user behavioral metrics.

#### 🎯 Purpose
Identifies general customer segments using rule-based thresholds and prepares behavioral features for unsupervised clustering.

---

### 6. **customer_segmentation/customer_segmentation_fe.ipynb**

**Type**: Jupyter Notebook

#### 📝 Description
Standardizes the user behavioral features and applies K-Means clustering ($K = 4$) to classify users into distinct customer segments.

#### 🔧 Inputs
- `data/precomputed/user_features.csv`

#### 💾 Outputs
- `data/precomputed/user_segments.csv` — User clustering results mapping users to: `champion`, `regular`, `at-risk`, and `dormant`.

#### 🎯 Purpose
Classifies each customer into a segment, allowing the recommendation engine to adjust recommendation strategy based on churn risk.

---

### 7. **demand_forecasting/eda.ipynb**

**Type**: Jupyter Notebook

#### 📝 Description
Explores product demand volume, overall dataset ordering statistics, and trends.

#### 🔧 Inputs
- `data/combined_instacart_data.csv`

#### 💾 Outputs
- `data/precomputed/orders_per_dow.csv`
- `data/precomputed/orders_per_hour.csv`
- `data/precomputed/dept_demand_dow.csv`
- `data/precomputed/top_products_dow.csv`
- `data/precomputed/top_products_overall.csv`

#### 🎯 Purpose
Performs overall demand exploration and extracts key order volume distributions.

---

### 8. **demand_forecasting/fe.ipynb**

**Type**: Jupyter Notebook

#### 📝 Description
Extracts demand velocity and daily patterns for all products.

#### 🔧 Inputs
- `data/combined_instacart_data.csv`

#### 💾 Outputs
- `data/precomputed/product_dow_demand.json` — Product-to-day-of-week demand mapping for interactive lookups.

#### 🎯 Purpose
Provides pre-computed daily demand mapping, loaded by the frontend dashboard to display detailed order lookups for store operators.

---

## 🔄 Data Pipeline Flowchart

The following flowchart shows how each notebook reads raw data and precomputed files, outputs intermediate data tables, and feeds into downstream machine learning models, backend engines, and frontend dashboards:

```
[ Raw Instacart Data ] (data/combined_instacart_data.csv)
  │
  ├─► [ customer_segmentation_eda.ipynb ] ──► (user_features.csv)
  │                                                │
  │                                                ▼
  │                                    [ customer_segmentation_fe.ipynb ] ──► (user_segments.csv) ──► [ Frontend Admin Dashboard ]
  │
  ├─► [ demand_forecasting/eda.ipynb ] ──► (orders_per_dow.csv, etc.)
  │
  ├─► [ demand_forecasting/fe.ipynb ] ───► (product_dow_demand.json) ──► [ Frontend Admin Dashboard ]
  │
  ├─► [ feature_engineering.ipynb ] (or reconstruct_features.py)
  │       ├─► (train_features.parquet) ──► [ LightGBM Model ] (models/lightgbm_model.py) ──► (lgbm_model.txt) ──► [ recommendation_engine.py ]
  │       ├─► (product_names.parquet) ───► [ recommendation_engine.py ] / API response
  │       └─► (order_products.parquet) ──► [ FP-Growth Model ] (models/market_basket.py) ──► (mba_rules.pkl) ───► [ recommendation_engine.py ]
  │
  └─► [ build_trending_data.py ] (or feature_engineering_trending.ipynb)
          ├─► (trending_lookup.pkl) ─────► [ Trending Engine ] (backend/trending_engine.py)
          └─► (trending_departments.parquet)
```

---

## 🚀 Execution & Regeneration Guide

If you need to update features or regenerate dataset tables:

### 1. Customer Segmentation Pipeline
To regenerate the customer clusters used for segmenting dashboard users:
```bash
# Step 1: Extract customer features and rule-based dormancy
# Open and run customer_segmentation/customer_segmentation_eda.ipynb
# Output: data/precomputed/user_features.csv

# Step 2: Fit K-Means model to standard clusters
# Open and run customer_segmentation/customer_segmentation_fe.ipynb
# Output: data/precomputed/user_segments.csv
```

### 2. Demand Forecasting & Product Order Velocity Pipeline
To update product order velocity and day of week demand mapping:
```bash
# Step 1: Generate order volume breakdowns by Day of Week
# Open and run demand_forecasting/eda.ipynb
# Output: data/precomputed/orders_per_dow.csv, data/precomputed/orders_per_hour.csv, etc.

# Step 2: Compute product day of week demand JSON mapping
# Open and run demand_forecasting/fe.ipynb
# Output: data/precomputed/product_dow_demand.json
```

### 3. Recommender Training Features Pipeline
To regenerate the full LightGBM feature matrix:
```bash
python notebooks/reconstruct_features.py
# Output: outputs/train_features.parquet, outputs/product_names.parquet
```

### 4. Trending Contextual Pipeline
To recalculate trending items and update the lookup dictionary for the API:
```bash
python notebooks/build_trending_data.py
# Output: outputs/trending_lookup.pkl, outputs/trending_departments.parquet, outputs/trending_scores.parquet
```

---

## 📚 References

- Outputs Comprehensive Guide: `outputs/README.md`
- Backend Recommendation Engine: `backend/recommendation_engine.py`
- Backend Trending Engine: `backend/trending_engine.py`
- Frontend Dashboard Page: `frontend/src/pages/AdminDashboardPage.jsx`
- Customer Segmentation Guide: `docs/CUSTOMER_SEGMENTATION_README.md`
- Contextual Trending Guide: `docs/TRENDING_README.md`
