"""
product_catalog.py
------------------
Static product catalog for the Instacart Smart Grocery app.
8 departments, ~40 products with prices in INR.
"""

DEPARTMENTS = [
    {"id": "produce",       "name": "Produce",       "icon": "🥬", "color": "#4CAF50"},
    {"id": "dairy_eggs",    "name": "Dairy & Eggs",   "icon": "🥛", "color": "#42A5F5"},
    {"id": "beverages",     "name": "Beverages",      "icon": "☕", "color": "#AB47BC"},
    {"id": "snacks",        "name": "Snacks",         "icon": "🍿", "color": "#FF7043"},
    {"id": "bakery",        "name": "Bakery",         "icon": "🍞", "color": "#FFA726"},
    {"id": "frozen",        "name": "Frozen",         "icon": "🧊", "color": "#26C6DA"},
    {"id": "breakfast",     "name": "Breakfast",      "icon": "🥣", "color": "#FFCA28"},
    {"id": "pantry",        "name": "Pantry",         "icon": "🫙", "color": "#8D6E63"},
]

PRODUCTS = [
    # ── Produce ──
    {"id": "banana",            "name": "Banana",            "department": "produce",    "price": 40,  "emoji": "🌙"},
    {"id": "organic_banana",    "name": "Organic Banana",    "department": "produce",    "price": 60,  "emoji": "🌙"},
    {"id": "avocado",           "name": "Avocado",           "department": "produce",    "price": 120, "emoji": "🥑"},
    {"id": "strawberries",      "name": "Strawberries",      "department": "produce",    "price": 199, "emoji": "🍓"},
    {"id": "lemon",             "name": "Lemon",             "department": "produce",    "price": 30,  "emoji": "🍋"},
    {"id": "garlic",            "name": "Garlic",            "department": "produce",    "price": 40,  "emoji": "🧄"},
    {"id": "onion",             "name": "Onion",             "department": "produce",    "price": 35,  "emoji": "🧅"},
    {"id": "tomato",            "name": "Tomato",            "department": "produce",    "price": 45,  "emoji": "🍅"},
    {"id": "spinach",           "name": "Spinach",           "department": "produce",    "price": 30,  "emoji": "🥬"},
    {"id": "apple",             "name": "Apple",             "department": "produce",    "price": 150, "emoji": "🍎"},

    # ── Dairy & Eggs ──
    {"id": "whole_milk",        "name": "Whole Milk",        "department": "dairy_eggs", "price": 68,  "emoji": "🥛"},
    {"id": "organic_milk",      "name": "Organic Milk",      "department": "dairy_eggs", "price": 95,  "emoji": "🥛"},
    {"id": "greek_yogurt",      "name": "Greek Yogurt",      "department": "dairy_eggs", "price": 120, "emoji": "🥣"},
    {"id": "yogurt",            "name": "Yogurt",            "department": "dairy_eggs", "price": 55,  "emoji": "🥣"},
    {"id": "eggs",              "name": "Eggs",              "department": "dairy_eggs", "price": 85,  "emoji": "🥚"},
    {"id": "butter",            "name": "Butter",            "department": "dairy_eggs", "price": 56,  "emoji": "🧈"},
    {"id": "cottage_cheese",    "name": "Cottage Cheese",    "department": "dairy_eggs", "price": 90,  "emoji": "🧀"},
    {"id": "cheese_sticks",     "name": "Cheese Sticks",     "department": "dairy_eggs", "price": 130, "emoji": "🧀"},

    # ── Bakery ──
    {"id": "bread",             "name": "Bread",             "department": "bakery",     "price": 45,  "emoji": "🍞"},
    {"id": "whole_wheat_bread", "name": "Whole Wheat Bread", "department": "bakery",     "price": 55,  "emoji": "🍞"},
    {"id": "tortillas",         "name": "Tortillas",         "department": "bakery",     "price": 80,  "emoji": "🌕"},
    {"id": "bagels",            "name": "Bagels",            "department": "bakery",     "price": 120, "emoji": "🥯"},

    # ── Snacks ──
    {"id": "chips",             "name": "Chips",             "department": "snacks",     "price": 50,  "emoji": "🍟"},
    {"id": "crackers",          "name": "Crackers",          "department": "snacks",     "price": 60,  "emoji": "🍘"},
    {"id": "granola_bars",      "name": "Granola Bars",      "department": "snacks",     "price": 150, "emoji": "🍫"},
    {"id": "popcorn",           "name": "Popcorn",           "department": "snacks",     "price": 70,  "emoji": "🍿"},
    {"id": "cookies",           "name": "Cookies",           "department": "snacks",     "price": 99,  "emoji": "🍪"},

    # ── Beverages ──
    {"id": "sparkling_water",   "name": "Sparkling Water",   "department": "beverages",  "price": 60,  "emoji": "💧"},
    {"id": "orange_juice",      "name": "Orange Juice",      "department": "beverages",  "price": 99,  "emoji": "🍊"},
    {"id": "almond_milk",       "name": "Almond Milk",       "department": "beverages",  "price": 180, "emoji": "🥛"},
    {"id": "coffee",            "name": "Coffee",            "department": "beverages",  "price": 250, "emoji": "☕"},
    {"id": "soda",              "name": "Soda",              "department": "beverages",  "price": 40,  "emoji": "🥤"},

    # ── Frozen ──
    {"id": "frozen_pizza",      "name": "Frozen Pizza",      "department": "frozen",     "price": 299, "emoji": "🍕"},
    {"id": "ice_cream",         "name": "Ice Cream",         "department": "frozen",     "price": 199, "emoji": "🍦"},
    {"id": "frozen_vegetables", "name": "Frozen Vegetables",  "department": "frozen",     "price": 120, "emoji": "🥦"},

    # ── Breakfast ──
    {"id": "cereal",            "name": "Cereal",            "department": "breakfast",  "price": 180, "emoji": "🥣"},
    {"id": "oatmeal",           "name": "Oatmeal",           "department": "breakfast",  "price": 130, "emoji": "🥣"},
    {"id": "pancake_mix",       "name": "Pancake Mix",       "department": "breakfast",  "price": 150, "emoji": "🥞"},
    {"id": "granola",           "name": "Granola",           "department": "breakfast",  "price": 220, "emoji": "🥜"},

    # ── Pantry ──
    {"id": "rice",              "name": "Rice",              "department": "pantry",     "price": 90,  "emoji": "🍚"},
    {"id": "pasta",             "name": "Pasta",             "department": "pantry",     "price": 75,  "emoji": "🍝"},
    {"id": "canned_beans",      "name": "Canned Beans",      "department": "pantry",     "price": 60,  "emoji": "🥫"},
    {"id": "olive_oil",         "name": "Olive Oil",         "department": "pantry",     "price": 450, "emoji": "🍾"},
]


def get_all_products():
    return PRODUCTS


def get_products_by_department(dept_id: str):
    return [p for p in PRODUCTS if p["department"] == dept_id]


def get_product_by_id(product_id: str):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None


def get_product_by_name(name: str):
    name_lower = name.lower().strip()
    for p in PRODUCTS:
        if p["name"].lower() == name_lower:
            return p
    return None


POPULARITY_RANKING = [
    "banana", "organic_banana", "strawberries", "avocado", "spinach",
    "whole_milk", "eggs", "greek_yogurt", "bread", "butter",
    "apple", "lemon", "onion", "tomato", "garlic",
    "orange_juice", "coffee", "chips", "crackers", "cereal",
    "organic_milk", "yogurt", "almond_milk", "sparkling_water", "bagels",
    "tortillas", "whole_wheat_bread", "cottage_cheese", "cheese_sticks",
    "granola_bars", "popcorn", "cookies", "soda",
    "frozen_pizza", "ice_cream", "frozen_vegetables",
    "oatmeal", "pancake_mix", "granola",
    "rice", "pasta", "canned_beans", "olive_oil",
]
