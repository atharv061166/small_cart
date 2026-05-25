import { useCart } from '../context/CartContext';
import { getDepartmentById } from '../data/products';
import { useState } from 'react';

export default function ProductCard({ product, onOpenCart }) {
  const { addItem } = useCart();
  const [added, setAdded] = useState(false);
  const dept = getDepartmentById(product.department);

  const handleAdd = () => {
    addItem(product);
    setAdded(true);
    if (onOpenCart) {
      onOpenCart();
    }
    setTimeout(() => setAdded(false), 600);
  };

  return (
    <div className="product-card">
      <div
        className="product-emoji-area"
        style={{
          background: dept
            ? `linear-gradient(135deg, ${dept.color}15, ${dept.color}08)`
            : 'var(--bg-glass)',
        }}
      >
        {product.emoji}
      </div>
      <div className="product-info">
        <div className="product-name">{product.name}</div>
        <div className="product-dept">{dept?.name || product.department}</div>
        <div className="product-footer">
          <span className="product-price">₹{product.price}</span>
          <button
            className={`add-btn ${added ? 'added' : ''}`}
            onClick={handleAdd}
            aria-label={`Add ${product.name} to cart`}
          >
            {added ? '✓' : '+'}
          </button>
        </div>
      </div>
    </div>
  );
}
