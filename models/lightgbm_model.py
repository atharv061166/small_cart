import pandas as pd
import numpy as np
import joblib
import os
import warnings
import gc
from memory_utils import reduce_mem_usage, clear_memory

warnings.filterwarnings('ignore')

import lightgbm as lgb
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import f1_score, classification_report

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../outputs/")
FEATURE_COLS = [
    'user_total_orders', 'user_avg_basket_size', 'user_reorder_rate',
    'user_avg_days_since_prior', 'user_fav_hour', 'user_fav_dow',
    'product_total_orders', 'product_unique_users', 'product_reorder_rate',
    'product_avg_position', 'aisle_id', 'department_id',
    'up_times_ordered', 'up_reorder_rate', 'up_last_order_number',
    'up_first_order_number', 'up_order_recency', 'up_order_freq_ratio',
    'user_vs_global_affinity', 'product_log_popularity'
]


def load_data():
    print("Loading features...")
    # Load only necessary columns to save memory
    cols_to_load = FEATURE_COLS + ['target', 'user_id']
    df = pd.read_parquet(OUTPUTS_DIR + 'train_features.parquet', columns=cols_to_load)
    df = reduce_mem_usage(df)
    return df


def split_by_user(train, test_size=0.2, random_state=42):
    unique_users = train['user_id'].unique()
    np.random.seed(random_state)
    test_users = np.random.choice(unique_users, size=int(len(unique_users) * test_size), replace=False)
    mask = train['user_id'].isin(test_users)
    train_df = train[~mask].copy()
    test_df = train[mask].copy()
    
    # Explicitly delete the original dataframe to free memory
    del train
    clear_memory()
    
    return train_df, test_df


def prepare_xy(df):
    cols = [c for c in FEATURE_COLS if c in df.columns]
    X = df[cols].fillna(0) # Keep types as optimized by reduce_mem_usage
    y = df['target'].values
    return X, y, cols


def tune_and_train(X_train, y_train, X_val, y_val, feature_cols):
    param_grid = {
        'num_leaves':        [31, 63, 127],
        'learning_rate':     [0.01, 0.05, 0.1],
        'min_child_samples': [20, 50, 100],
        'lambda_l1':         [0.0, 0.1],
        'lambda_l2':         [0.0, 0.1],
        'feature_fraction':  [0.7, 0.8],
        'bagging_fraction':  [0.8],
        'bagging_freq':      [5],
        'n_estimators':      [200],
    }

    base = lgb.LGBMClassifier(
        objective='binary',
        n_jobs=-1,
        random_state=42,
        verbosity=-1
    )

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    grid = RandomizedSearchCV(
        base, param_grid,
        n_iter=10,
        scoring='f1',
        cv=cv,
        n_jobs=2,
        random_state=42,
        verbose=1
    )

    print("Running RandomizedSearchCV for LightGBM...")
    
    # Calculate sample weights to down-weight popular products
    train_weights = 1.0 / np.log1p(X_train['product_total_orders'])
    val_weights = 1.0 / np.log1p(X_val['product_total_orders'])

    grid.fit(X_train, y_train, sample_weight=train_weights)
    print(f"Best params : {grid.best_params_}")
    print(f"Best CV F1  : {grid.best_score_:.4f}")

    # Retrain best model with early stopping on val set
    best_params = grid.best_params_
    best_params.update({
        'objective': 'binary',
        'metric': 'binary_logloss',
        'verbosity': -1,
        'n_jobs': 2, 
        'random_state': 42
    })
    
    # Pop n_estimators so it doesn't conflict with num_boost_round
    best_params.pop('n_estimators', None)

    dtrain = lgb.Dataset(X_train, label=y_train, feature_name=feature_cols, weight=train_weights)
    dval   = lgb.Dataset(X_val,   label=y_val,   reference=dtrain, weight=val_weights)

    callbacks = [lgb.early_stopping(50, verbose=False), lgb.log_evaluation(period=100)]

    def lgb_f1_score(preds, train_data):
        y_true = train_data.get_label()
        y_pred = (preds >= 0.5).astype(int)
        return 'f1', f1_score(y_true, y_pred), True

    final_model = lgb.train(
        best_params, dtrain,
        num_boost_round=1000,
        valid_sets=[dtrain, dval],
        valid_names=['train', 'val'],
        callbacks=callbacks,
        feval=lgb_f1_score
    )

    print(f"Best iteration: {final_model.best_iteration}")

    # Threshold tuning: sweep from 0.20 to 0.65 in steps of 0.01 on validation set
    y_val_prob = final_model.predict(X_val[feature_cols].fillna(0))
    best_threshold = 0.5
    best_score = -1.0
    thresholds = np.arange(0.20, 0.66, 0.01)
    for t in thresholds:
        y_val_pred = (y_val_prob >= t).astype(int)
        score = f1_score(y_val, y_val_pred)
        if score > best_score:
            best_score = score
            best_threshold = t

    print(f"Optimal threshold on validation set: {best_threshold:.2f} (F1: {best_score:.4f})")
    return final_model, best_threshold


def evaluate(model, test_df, feature_cols, threshold):
    X_test, y_test, _ = prepare_xy(test_df)
    y_prob = model.predict(X_test[feature_cols].fillna(0))
    y_pred = (y_prob >= threshold).astype(int)
    print(f"\nTest F1-Score : {f1_score(y_test, y_pred):.4f} (using threshold {threshold:.2f})")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Not Reorder', 'Reorder']))

    fi = pd.Series(
        model.feature_importance(importance_type='gain'),
        index=model.feature_name()
    ).sort_values(ascending=False)
    print("\nTop 10 Feature Importances (gain):")
    print(fi.head(10).to_string())


def save_artifacts(model, feature_cols, threshold):
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    model.save_model(OUTPUTS_DIR + 'lgbm_model.txt')
    joblib.dump(feature_cols, OUTPUTS_DIR + 'lgbm_feature_cols.pkl')
    
    # Save optimal threshold
    import json
    with open(OUTPUTS_DIR + 'lgbm_threshold.json', 'w') as f:
        json.dump({'threshold': float(threshold)}, f)
        
    print(f"\nSaved: lgbm_model.txt | lgbm_feature_cols.pkl | lgbm_threshold.json (optimal threshold: {threshold:.2f})")


def main():
    train = load_data()
    train_df, test_df = split_by_user(train)

    # Further split train into train/val for early stopping
    train_df, val_df = split_by_user(train_df, test_size=0.15)
    print(f"Train: {len(train_df):,}  |  Val: {len(val_df):,}  |  Test: {len(test_df):,}")

    X_train, y_train, feature_cols = prepare_xy(train_df)
    X_val,   y_val,   _            = prepare_xy(val_df)
    
    # Free up memory
    del train_df, val_df
    clear_memory()

    model, threshold = tune_and_train(X_train, y_train, X_val, y_val, feature_cols)
    evaluate(model, test_df, feature_cols, threshold)
    save_artifacts(model, feature_cols, threshold)
    print("\nDone. Now run: python inference/run_lightgbm.py")


if __name__ == "__main__":
    main()
