import pandas as pd
import numpy as np
import joblib
import os
import warnings
import gc
from memory_utils import reduce_mem_usage, clear_memory

warnings.filterwarnings('ignore')

from mlxtend.frequent_patterns import fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder

OUTPUTS_DIR = "../outputs/"


def load_data():
    print("Loading order-product data...")
    df = pd.read_parquet(OUTPUTS_DIR + 'order_products.parquet')
    df = reduce_mem_usage(df)
    return df


def build_transactions(order_products, min_product_orders=50, sample_orders=50000):
    """
    Build transaction list for FP-Growth.
    - min_product_orders : drop products ordered fewer than N times (reduces matrix size)
    - sample_orders      : sample N orders to keep memory safe on M3 Air
    """
    popular = order_products['product_name'].value_counts()
    popular = popular[popular >= min_product_orders].index
    filtered = order_products[order_products['product_name'].isin(popular)]

    print(f"Products after frequency filter: {len(popular):,}")

    if sample_orders and sample_orders < filtered['order_id'].nunique():
        sampled_ids = filtered['order_id'].drop_duplicates().sample(n=sample_orders, random_state=42)
        filtered = filtered[filtered['order_id'].isin(sampled_ids)]
        print(f"Sampled {sample_orders:,} orders")

    transactions = (
        filtered
        .groupby('order_id')['product_name']
        .apply(lambda x: list(set(x)))
        .tolist()
    )
    transactions = [t for t in transactions if len(t) >= 2]
    print(f"Transactions for FP-Growth: {len(transactions):,}")
    
    # Explicitly clear memory
    del filtered
    clear_memory()
    
    return transactions


def encode_transactions(transactions):
    print("Encoding transactions...")
    te = TransactionEncoder()
    # Use sparse=True to save a massive amount of memory
    te_array = te.fit_transform(transactions, sparse=True)
    df_enc = pd.DataFrame.sparse.from_spmatrix(te_array, columns=te.columns_)
    print(f"Encoded matrix (sparse): {df_enc.shape}")
    return df_enc, list(te.columns_)


def run_fpgrowth(df_enc, min_support=0.01):
    print(f"Running FP-Growth (min_support={min_support})...")
    frequent_itemsets = fpgrowth(df_enc, min_support=min_support, use_colnames=True)
    frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(len)
    print(f"Frequent itemsets: {len(frequent_itemsets):,}")
    return frequent_itemsets


def build_rules(frequent_itemsets, min_confidence=0.1, min_lift=1.5):
    print(f"Generating association rules (confidence>={min_confidence}, lift>={min_lift})...")
    rules = association_rules(frequent_itemsets, metric='confidence', min_threshold=min_confidence)
    
    # Calculate Zhang's metric
    supp_A = rules['antecedent support']
    supp_B = rules['consequent support']
    supp_AB = rules['support']
    
    numerator = supp_AB - (supp_A * supp_B)
    denominator = np.maximum(supp_AB * (1 - supp_A), supp_A * (supp_B - supp_AB))
    # Add a small epsilon to avoid division by zero
    rules['zhangs_metric'] = numerator / (denominator + 1e-10)
    
    # Apply filters to eliminate popularity bias
    rules = rules[
        (rules['consequent support'] <= 0.30) &
        (rules['lift'] > min_lift) &
        (rules['zhangs_metric'] > 0.2)
    ]
    
    rules = rules.sort_values('lift', ascending=False).reset_index(drop=True)
    print(f"Rules after popularity bias filtering: {len(rules):,}")
    return rules


def save_artifacts(rules):
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    joblib.dump(rules, OUTPUTS_DIR + 'mba_rules.pkl')
    print("\nSaved: mba_rules.pkl")


def main():
    order_products = load_data()

    transactions = build_transactions(
        order_products,
        min_product_orders=50,
        sample_orders=50000
    )
    
    del order_products
    clear_memory()

    df_enc, _ = encode_transactions(transactions)
    
    del transactions
    clear_memory()

    frequent_itemsets = run_fpgrowth(df_enc, min_support=0.01)

    del df_enc  # free memory
    clear_memory()

    rules = build_rules(frequent_itemsets, min_confidence=0.1, min_lift=1.5)

    print("\nSample top rules by lift:")
    print(rules[['antecedents','consequents','support','confidence','lift']].head(10).to_string(index=False))

    save_artifacts(rules)
    print("\nDone. Now run: python inference/run_market_basket.py")


if __name__ == "__main__":
    main()
