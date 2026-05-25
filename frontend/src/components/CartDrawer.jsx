import { useCart } from '../context/CartContext';
import { Link } from 'react-router-dom';

export default function CartDrawer({ isOpen, onClose }) {
  const { items, removeItem, updateQuantity, totalPrice, clearCart } = useCart();

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="cart-drawer-overlay"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="cart-drawer">
        <div className="cart-drawer-header">
          <h2 className="cart-drawer-title">Your Cart</h2>
          <button
            className="cart-drawer-close"
            onClick={onClose}
            aria-label="Close cart"
          >
            ✕
          </button>
        </div>

        <div className="cart-drawer-content">
          {items.length === 0 ? (
            <div className="cart-empty">
              <div className="cart-empty-icon">🛒</div>
              <p className="cart-empty-text">Your cart is empty</p>
            </div>
          ) : (
            <>
              <div className="cart-items-list">
                {items.map((item) => (
                  <div key={item.id} className="cart-drawer-item">
                    <div className="cart-item-emoji">{item.emoji}</div>
                    <div className="cart-item-info">
                      <div className="cart-item-name">{item.name}</div>
                      <div className="cart-item-price">₹{item.price} each</div>
                    </div>
                    <div className="cart-item-qty-control">
                      <button
                        className="qty-btn"
                        onClick={() => updateQuantity(item.id, item.quantity - 1)}
                        aria-label="Decrease quantity"
                      >
                        −
                      </button>
                      <span className="qty-value">{item.quantity}</span>
                      <button
                        className="qty-btn"
                        onClick={() => updateQuantity(item.id, item.quantity + 1)}
                        aria-label="Increase quantity"
                      >
                        +
                      </button>
                    </div>
                    <div className="cart-item-subtotal">₹{(item.price * item.quantity).toFixed(2)}</div>
                    <button
                      className="cart-remove-btn"
                      onClick={() => removeItem(item.id)}
                      aria-label="Remove item"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>

              <div className="cart-drawer-summary">
                <div className="summary-row">
                  <span className="summary-label">Subtotal:</span>
                  <span className="summary-value">₹{totalPrice.toFixed(2)}</span>
                </div>
                <div className="summary-row">
                  <span className="summary-label">Delivery:</span>
                  <span className="summary-value">FREE</span>
                </div>
                <div className="summary-row total">
                  <span className="summary-label">Total:</span>
                  <span className="summary-value">₹{totalPrice.toFixed(2)}</span>
                </div>
              </div>

              <div className="cart-drawer-actions">
                <Link
                  to="/cart"
                  className="btn btn-primary"
                  onClick={onClose}
                >
                  View Full Cart
                </Link>
                <button
                  className="btn btn-secondary"
                  onClick={clearCart}
                >
                  Clear Cart
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
