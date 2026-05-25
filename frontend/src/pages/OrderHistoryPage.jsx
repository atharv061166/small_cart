import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { fetchOrders } from '../api';
import { PRODUCTS } from '../data/products';

export default function OrderHistoryPage() {
  const { user, getToken } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedOrder, setExpandedOrder] = useState(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    const loadOrders = async () => {
      try {
        const token = await getToken();
        const res = await fetchOrders(token, user.uid);
        setOrders(res.orders || []);
      } catch (err) {
        setError('Could not load orders. Make sure the backend is running.');
      } finally {
        setLoading(false);
      }
    };

    loadOrders();
  }, [user]);

  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const getProductEmoji = (productName) => {
    const product = PRODUCTS.find(
      (p) => p.name.toLowerCase() === productName?.toLowerCase()
    );
    return product?.emoji || '📦';
  };

  if (loading) {
    return (
      <div className="page">
        <div className="loading-spinner" />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="cart-container">
        <div className="page-header">
          <h1 className="page-title">Order History</h1>
          <p className="page-subtitle">
            {orders.length > 0
              ? `${orders.length} order${orders.length > 1 ? 's' : ''} placed`
              : 'No orders yet'}
          </p>
        </div>

        {error && (
          <div className="auth-error" style={{ marginBottom: '1.5rem' }}>
            {error}
          </div>
        )}

        {orders.length === 0 && !error ? (
          <div className="empty-state glass-card">
            <div className="empty-icon">📋</div>
            <p className="empty-text">No orders yet. Start shopping!</p>
            <button
              className="btn btn-primary"
              onClick={() => navigate('/')}
              style={{ marginTop: '1rem' }}
            >
              Browse Products
            </button>
          </div>
        ) : (
          orders.map((order) => (
            <div key={order.id} className="order-card glass-card">
              <div
                className="order-header"
                onClick={() =>
                  setExpandedOrder(expandedOrder === order.id ? null : order.id)
                }
              >
                <div>
                  <div className="order-id">#{order.id?.slice(-8)}</div>
                  <div className="order-date">{formatDate(order.created_at)}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span className="order-status">{order.status || 'completed'}</span>
                  <span className="order-total">₹{order.total}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {expandedOrder === order.id ? '▲' : '▼'}
                  </span>
                </div>
              </div>

              {expandedOrder === order.id && order.items && (
                <div className="order-items-list">
                  {order.items.map((item, i) => (
                    <div key={i} className="order-item-row">
                      <div className="order-item-left">
                        <span className="order-item-emoji">
                          {getProductEmoji(item.product_name)}
                        </span>
                        <span>{item.product_name}</span>
                        <span style={{ color: 'var(--text-muted)' }}>×{item.quantity}</span>
                      </div>
                      <span style={{ fontWeight: 600, color: 'var(--accent-green)' }}>
                        ₹{item.item_total}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
