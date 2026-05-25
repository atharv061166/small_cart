export const DEPARTMENTS = [
  { id: 'produce',     name: 'Produce',       icon: '🥬', color: '#4CAF50', gradient: 'linear-gradient(135deg, #43A047, #66BB6A)' },
  { id: 'dairy_eggs',  name: 'Dairy & Eggs',   icon: '🥛', color: '#42A5F5', gradient: 'linear-gradient(135deg, #1E88E5, #64B5F6)' },
  { id: 'beverages',   name: 'Beverages',      icon: '☕', color: '#AB47BC', gradient: 'linear-gradient(135deg, #8E24AA, #CE93D8)' },
  { id: 'snacks',      name: 'Snacks',         icon: '🍿', color: '#FF7043', gradient: 'linear-gradient(135deg, #E64A19, #FF8A65)' },
  { id: 'bakery',      name: 'Bakery',         icon: '🍞', color: '#FFA726', gradient: 'linear-gradient(135deg, #EF6C00, #FFB74D)' },
  { id: 'frozen',      name: 'Frozen',         icon: '🧊', color: '#26C6DA', gradient: 'linear-gradient(135deg, #00838F, #4DD0E1)' },
  { id: 'breakfast',   name: 'Breakfast',      icon: '🥣', color: '#FFCA28', gradient: 'linear-gradient(135deg, #F9A825, #FFD54F)' },
  { id: 'pantry',      name: 'Pantry',         icon: '🫙', color: '#8D6E63', gradient: 'linear-gradient(135deg, #5D4037, #A1887F)' },
];

export const PRODUCTS = [
  // Produce
  { id: 'banana',            name: 'Banana',            department: 'produce',    price: 40,  emoji: '🍌' },
  { id: 'organic_banana',    name: 'Organic Banana',    department: 'produce',    price: 60,  emoji: '🍌' },
  { id: 'avocado',           name: 'Avocado',           department: 'produce',    price: 120, emoji: '🥑' },
  { id: 'strawberries',      name: 'Strawberries',      department: 'produce',    price: 199, emoji: '🍓' },
  { id: 'lemon',             name: 'Lemon',             department: 'produce',    price: 30,  emoji: '🍋' },
  { id: 'garlic',            name: 'Garlic',            department: 'produce',    price: 40,  emoji: '🧄' },
  { id: 'onion',             name: 'Onion',             department: 'produce',    price: 35,  emoji: '🧅' },
  { id: 'tomato',            name: 'Tomato',            department: 'produce',    price: 45,  emoji: '🍅' },
  { id: 'spinach',           name: 'Spinach',           department: 'produce',    price: 30,  emoji: '🥬' },
  { id: 'apple',             name: 'Apple',             department: 'produce',    price: 150, emoji: '🍎' },

  // Dairy & Eggs
  { id: 'whole_milk',        name: 'Whole Milk',        department: 'dairy_eggs', price: 68,  emoji: '🥛' },
  { id: 'organic_milk',      name: 'Organic Milk',      department: 'dairy_eggs', price: 95,  emoji: '🥛' },
  { id: 'greek_yogurt',      name: 'Greek Yogurt',      department: 'dairy_eggs', price: 120, emoji: '🥣' },
  { id: 'yogurt',            name: 'Yogurt',            department: 'dairy_eggs', price: 55,  emoji: '🥣' },
  { id: 'eggs',              name: 'Eggs',              department: 'dairy_eggs', price: 85,  emoji: '🥚' },
  { id: 'butter',            name: 'Butter',            department: 'dairy_eggs', price: 56,  emoji: '🧈' },
  { id: 'cottage_cheese',    name: 'Cottage Cheese',    department: 'dairy_eggs', price: 90,  emoji: '🧀' },
  { id: 'cheese_sticks',     name: 'Cheese Sticks',     department: 'dairy_eggs', price: 130, emoji: '🧀' },

  // Bakery
  { id: 'bread',             name: 'Bread',             department: 'bakery',     price: 45,  emoji: '🍞' },
  { id: 'whole_wheat_bread', name: 'Whole Wheat Bread', department: 'bakery',     price: 55,  emoji: '🍞' },
  { id: 'tortillas',         name: 'Tortillas',         department: 'bakery',     price: 80,  emoji: '🫓' },
  { id: 'bagels',            name: 'Bagels',            department: 'bakery',     price: 120, emoji: '🥯' },

  // Snacks
  { id: 'chips',             name: 'Chips',             department: 'snacks',     price: 50,  emoji: '🍟' },
  { id: 'crackers',          name: 'Crackers',          department: 'snacks',     price: 60,  emoji: '🍘' },
  { id: 'granola_bars',      name: 'Granola Bars',      department: 'snacks',     price: 150, emoji: '🍫' },
  { id: 'popcorn',           name: 'Popcorn',           department: 'snacks',     price: 70,  emoji: '🍿' },
  { id: 'cookies',           name: 'Cookies',           department: 'snacks',     price: 99,  emoji: '🍪' },

  // Beverages
  { id: 'sparkling_water',   name: 'Sparkling Water',   department: 'beverages',  price: 60,  emoji: '💧' },
  { id: 'orange_juice',      name: 'Orange Juice',      department: 'beverages',  price: 99,  emoji: '🍊' },
  { id: 'almond_milk',       name: 'Almond Milk',       department: 'beverages',  price: 180, emoji: '🥛' },
  { id: 'coffee',            name: 'Coffee',            department: 'beverages',  price: 250, emoji: '☕' },
  { id: 'soda',              name: 'Soda',              department: 'beverages',  price: 40,  emoji: '🥤' },

  // Frozen
  { id: 'frozen_pizza',      name: 'Frozen Pizza',      department: 'frozen',     price: 299, emoji: '🍕' },
  { id: 'ice_cream',         name: 'Ice Cream',         department: 'frozen',     price: 199, emoji: '🍦' },
  { id: 'frozen_vegetables', name: 'Frozen Vegetables', department: 'frozen',     price: 120, emoji: '🥦' },

  // Breakfast
  { id: 'cereal',            name: 'Cereal',            department: 'breakfast',  price: 180, emoji: '🥣' },
  { id: 'oatmeal',           name: 'Oatmeal',           department: 'breakfast',  price: 130, emoji: '🥣' },
  { id: 'pancake_mix',       name: 'Pancake Mix',       department: 'breakfast',  price: 150, emoji: '🥞' },
  { id: 'granola',           name: 'Granola',           department: 'breakfast',  price: 220, emoji: '🥜' },

  // Pantry
  { id: 'rice',              name: 'Rice',              department: 'pantry',     price: 90,  emoji: '🍚' },
  { id: 'pasta',             name: 'Pasta',             department: 'pantry',     price: 75,  emoji: '🍝' },
  { id: 'canned_beans',      name: 'Canned Beans',      department: 'pantry',     price: 60,  emoji: '🫘' },
  { id: 'olive_oil',         name: 'Olive Oil',         department: 'pantry',     price: 450, emoji: '🫒' },
];

export function getProductsByDepartment(deptId) {
  return PRODUCTS.filter(p => p.department === deptId);
}

export function getDepartmentById(deptId) {
  return DEPARTMENTS.find(d => d.id === deptId);
}

export function getProductById(productId) {
  return PRODUCTS.find(p => p.id === productId);
}
