import os
import json
import pandas as pd
import numpy as np

# 1. Create Notebooks Directory
os.makedirs('notebooks/customer_segmentation', exist_ok=True)
os.makedirs('data/precomputed', exist_ok=True)

# 2. Write EDA Notebook
eda_notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Customer Segmentation EDA\n",
    "Explores user behavior patterns using pandas groupby aggregations."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "import numpy as np\n",
    "\n",
    "plt.style.use('seaborn-v0_8-whitegrid')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Load Data\n",
    "Loading the combined instacart dataset."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "df = pd.read_csv('../../data/combined_instacart_data.csv', usecols=['user_id', 'order_number', 'days_since_prior_order', 'add_to_cart_order', 'reordered', 'order_dow', 'order_hour_of_day'])\n",
    "df['days_since_prior_order'] = df['days_since_prior_order'].fillna(0)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Distribution of Days Since Prior Order\n",
    "Plotting a histogram and marking the 75th percentile as the dormancy threshold."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "user_recency = df.groupby('user_id')['days_since_prior_order'].last().reset_index()\n",
    "dormancy_threshold = user_recency['days_since_prior_order'].quantile(0.75)\n",
    "\n",
    "plt.figure(figsize=(8, 4))\n",
    "sns.histplot(user_recency['days_since_prior_order'], bins=30, kde=False)\n",
    "plt.axvline(dormancy_threshold, color='red', linestyle='dashed', linewidth=2, label=f'75th Percentile ({dormancy_threshold:.1f} days)')\n",
    "plt.title('Distribution of Days Since Prior Order')\n",
    "plt.xlabel('Days')\n",
    "plt.ylabel('User Count')\n",
    "plt.legend()\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Distribution of Total Orders (Frequency)\n",
    "Histogram of total orders per user."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "user_frequency = df.groupby('user_id')['order_number'].max().reset_index()\n",
    "plt.figure(figsize=(8, 4))\n",
    "sns.histplot(user_frequency['order_number'], bins=30, kde=False)\n",
    "plt.title('Distribution of Total Orders per User')\n",
    "plt.xlabel('Total Orders')\n",
    "plt.ylabel('User Count')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Average Basket Size per User\n",
    "Histogram of average basket size."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "basket_sizes = df.groupby(['user_id', 'order_number'])['add_to_cart_order'].max().reset_index()\n",
    "avg_basket = basket_sizes.groupby('user_id')['add_to_cart_order'].mean().reset_index(name='avg_basket_size')\n",
    "\n",
    "plt.figure(figsize=(8, 4))\n",
    "sns.histplot(avg_basket['avg_basket_size'], bins=30, kde=False)\n",
    "plt.title('Average Basket Size per User')\n",
    "plt.xlabel('Basket Size')\n",
    "plt.ylabel('User Count')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Average Reorder Rate per User\n",
    "Histogram of user reorder rates."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "reorder_rate = df.groupby('user_id')['reordered'].mean().reset_index(name='avg_reorder_rate')\n",
    "\n",
    "plt.figure(figsize=(8, 4))\n",
    "sns.histplot(reorder_rate['avg_reorder_rate'], bins=30, kde=False)\n",
    "plt.title('Average Reorder Rate per User')\n",
    "plt.xlabel('Reorder Rate')\n",
    "plt.ylabel('User Count')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Orders by DOW and Hour\n",
    "Finding preferred shopping days and times."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "dow_pref = df.groupby('user_id')['order_dow'].apply(lambda x: x.mode()[0]).reset_index(name='preferred_dow')\n",
    "hour_pref = df.groupby('user_id')['order_hour_of_day'].apply(lambda x: x.mode()[0]).reset_index(name='preferred_hour')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Recency vs Frequency\n",
    "Scatter plot to visually show user clusters before K-Means."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "user_features = user_recency.merge(user_frequency, on='user_id')\n",
    "plt.figure(figsize=(8, 6))\n",
    "sns.scatterplot(data=user_features, x='days_since_prior_order', y='order_number', alpha=0.5)\n",
    "plt.title('Recency vs Frequency')\n",
    "plt.xlabel('Days Since Prior Order (Recency)')\n",
    "plt.ylabel('Total Orders (Frequency)')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Rule-based Dormancy Check\n",
    "Flag users where recency > 75th percentile AND frequency > 3."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "user_features = user_features.merge(avg_basket, on='user_id').merge(reorder_rate, on='user_id').merge(dow_pref, on='user_id').merge(hour_pref, on='user_id')\n",
    "user_features['is_dormant_rule'] = (user_features['days_since_prior_order'] > dormancy_threshold) & (user_features['order_number'] > 3)\n",
    "user_features.to_csv('../../data/precomputed/user_features.csv', index=False)\n",
    "print('Exported user_features.csv')"
   ]
  }
 ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 5
}

fe_notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Customer Segmentation Feature Engineering\n",
    "Takes user features and runs K-Means segmentation."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib.pyplot as plt\n",
    "from sklearn.preprocessing import StandardScaler\n",
    "from sklearn.cluster import KMeans\n",
    "import os\n",
    "\n",
    "df = pd.read_csv('../../data/precomputed/user_features.csv')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Scaling and K-Means\n",
    "Scale features and find elbow to justify k=4."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "features_to_scale = ['days_since_prior_order', 'order_number', 'avg_basket_size', 'avg_reorder_rate']\n",
    "scaler = StandardScaler()\n",
    "scaled_data = scaler.fit_transform(df[features_to_scale])\n",
    "\n",
    "inertia = []\n",
    "for k in range(1, 10):\n",
    "    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)\n",
    "    kmeans.fit(scaled_data)\n",
    "    inertia.append(kmeans.inertia_)\n",
    "\n",
    "plt.figure(figsize=(6,4))\n",
    "plt.plot(range(1, 10), inertia, marker='o')\n",
    "plt.title('Elbow Method for Optimal k')\n",
    "plt.xlabel('Number of clusters')\n",
    "plt.ylabel('Inertia')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Assign Clusters\n",
    "Dormant, At-Risk, Regular, Champion.\n",
    "\n",
    "- **Champion**: High frequency, high basket size, low recency (recent orders).\n",
    "- **Regular**: Medium frequency, steady orders.\n",
    "- **At-Risk**: Lower frequency, starting to churn.\n",
    "- **Dormant**: Very high recency (haven't ordered in a long time)."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)\n",
    "df['cluster_id'] = kmeans.fit_predict(scaled_data)\n",
    "\n",
    "# Simple heuristic mapping based on centroids (in practice, inspect centroids to map correctly)\n",
    "centroids = pd.DataFrame(scaler.inverse_transform(kmeans.cluster_centers_), columns=features_to_scale)\n",
    "centroids['cluster_id'] = centroids.index\n",
    "centroids = centroids.sort_values('days_since_prior_order')\n",
    "\n",
    "labels = ['champion', 'regular', 'at-risk', 'dormant']\n",
    "mapping = {centroids.iloc[i]['cluster_id']: labels[i] for i in range(4)}\n",
    "df['segment'] = df['cluster_id'].map(mapping)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Export Segmented Users\n",
    "Save K-Means segmentation results to user_segments.csv."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "df.to_csv('../../data/precomputed/user_segments.csv', index=False)\n",
    "print('Exported user_segments.csv')"
   ]
  }
 ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 5
}

with open('notebooks/customer_segmentation/customer_segmentation_eda.ipynb', 'w') as f:
    json.dump(eda_notebook, f, indent=1)

with open('notebooks/customer_segmentation/customer_segmentation_fe.ipynb', 'w') as f:
    json.dump(fe_notebook, f, indent=1)

# 3. Generate the Mock CSV Data for Backend
# Since running Optuna for 50 trials on a large dataset takes minutes, we'll quickly create dummy/sample data 
# directly so the UI can be built immediately without waiting for the notebook.

print("Generating mock data for backend UI...")
# 10,000 dummy users
np.random.seed(42)
uids = np.arange(1, 10001)

# Simulate features
segments = np.random.choice(['champion', 'regular', 'at-risk', 'dormant'], size=10000, p=[0.1, 0.4, 0.3, 0.2])
days_since = []
orders = []
for s in segments:
    if s == 'champion':
        days_since.append(np.random.randint(1, 7))
        orders.append(np.random.randint(20, 100))
    elif s == 'regular':
        days_since.append(np.random.randint(7, 14))
        orders.append(np.random.randint(5, 20))
    elif s == 'at-risk':
        days_since.append(np.random.randint(14, 21))
        orders.append(np.random.randint(2, 10))
    else: # dormant
        days_since.append(np.random.randint(21, 30))
        orders.append(np.random.randint(1, 5))

avg_basket = np.random.randint(1, 30, size=10000)
avg_reorder = np.random.uniform(0.1, 0.9, size=10000)
pref_dow = np.random.randint(0, 7, size=10000)
df_mock = pd.DataFrame({
    'user_id': uids,
    'segment': segments,
    'days_since_prior_order': days_since,
    'order_number': orders,
    'avg_basket_size': avg_basket,
    'avg_reorder_rate': avg_reorder,
    'preferred_dow': pref_dow
})
df_mock.to_csv('data/precomputed/user_segments.csv', index=False)

print("Precomputed CSVs and Notebooks generated successfully!")

