# Instacart Smart Grocery — Frontend Client

This is the React + Vite frontend client for the **Instacart Smart Grocery** application. It provides a modern, premium, and highly responsive user interface for both shoppers and administrators.

---

## 🚀 Getting Started

### 1. Installation
Install all dependencies using npm:
```bash
npm install
```

### 2. Development Server
Start the local development server on [http://localhost:5173/](http://localhost:5173/):
```bash
npm run dev
```

### 3. Build for Production
Compile and bundle the application for production:
```bash
npm run build
```

---

## 🎨 Design System & Aesthetics
The frontend is built using standard React and Vanilla CSS (`index.css`), featuring a custom glassmorphism design, vibrant dark/light themes, and micro-animations (transitions, hover scales, and loading states).

Key theme colors:
- **Dark Mode Background**: `#0a0e17`
- **Light Mode Background**: `#ffffff`
- **Accent Primary**: `#22c55e` (Instacart Green)
- **Glass Panel Fill**: `rgba(255, 255, 255, 0.05)`

---

## 📂 Project Structure

```
frontend/
├── public/                 # Static assets and images
├── src/
│   ├── assets/             # Global graphics and icons
│   ├── components/         # Shared UI Components (Cart, Navbar, Modals)
│   ├── context/            # Global state managers (Auth, Cart, Theme)
│   ├── pages/              # Application Pages
│   │   ├── AdminDashboardPage.jsx  # Admin Metrics and Analysis
│   │   ├── CartPage.jsx            # Checkout & Shopping Cart
│   │   ├── HomePage.jsx            # Store catalog & recommendations
│   │   ├── LoginPage.jsx           # User Authentication
│   │   └── OrderHistoryPage.jsx    # Previous user orders list
│   ├── api.js              # REST client wrapper for FastAPI backend
│   ├── App.jsx             # Main Router and routes definition
│   ├── index.css           # Global custom stylesheet
│   └── main.jsx            # Application entrypoint
└── package.json            # Configuration and dependencies
```

---

## 📊 Pages & Feature Breakdowns

### 1. Homepage & Storefront
- **Personalized Recommendations**: PERSONALIZED and dynamic carousels fed by the LightGBM recommender model.
- **Trending Products**: Time-aware trending items that change dynamically based on the current day of the week and hour bucket.
- **Department Browsing**: Quick filter buttons to explore catalog items by department.

### 2. Shopping Cart & checkout
- **Cart Drawer**: Sliding right-hand panel for quick cart additions/deletions.
- **Reactivation Coupon**: Automatically detects if a user qualifies for a reactivation discount based on past order dormancy (e.g. 5–10 days since last purchase).

### 3. Admin Dashboard (`/admin`)
An advanced operations console visualizing Instacart order behaviors:
- **Total Orders per Day of Week**: BarChart highlighting busy shopping days.
- **Order Volume by Hour**: LineChart showing peak hours of day.
- **Top 10 Products Overall**: Horizontal BarChart identifying top-selling inventory.
- **Department vs Day of Week**: Dynamic heatmap grid mapping order intensity per department.
- **Product Order Lookup (Refactored)**:
  - Search input box to quickly filter through thousands of products.
  - Dropdown select list to focus on a specific product.
  - Displays **Total Orders** for the selected product and an **Orders by Day of Week** BarChart (layered with a `z-index: 10000` hover tooltip fix).
- **Customer Segmentation**: Donut Chart of segment distribution (`champion`, `regular`, `at-risk`, `dormant`) and a Scatter Plot showing user Recency (days since prior order) vs Frequency (number of orders).
