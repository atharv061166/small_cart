import pandas as pd
import json
import os

print("Loading combined data...")
cols = ['product_name', 'order_dow']
df = pd.read_csv('data/combined_instacart_data.csv', usecols=cols)

print("Calculating DOW demand per product...")
dow_demand = df.groupby(['product_name', 'order_dow']).size().reset_index(name='demand')

print("Saving to JSON...")
# Keep it manageable. Maybe just top 5000 products, or save all if it's not too big.
# For a lookup table, it's better to have all if we can, but a dict of {product_name: {dow: demand}} will be around 10-20MB.
dow_dict = {}
for prod, group in dow_demand.groupby('product_name'):
    dow_dict[str(prod)] = group.set_index('order_dow')['demand'].to_dict()

out_path = 'data/precomputed/product_dow_demand.json'
with open(out_path, 'w') as f:
    json.dump(dow_dict, f)

print(f"Successfully saved to {out_path}")
