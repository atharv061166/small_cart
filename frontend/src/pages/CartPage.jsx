import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { createOrder, fetchRecommendations, fetchTrending, fetchUserProfile } from '../api';
import { PRODUCTS } from '../data/products';
import TrendingSection from '../components/TrendingSection';
import Toast from '../components/Toast';

// Instacart day mapping: 0=Saturday, 1=Sunday, ..., 6=Friday
const DAYS = [
  { dow: 1, label: 'Sun', full: 'Sunday' },
  { dow: 2, label: 'Mon', full: 'Monday' },
  { dow: 3, label: 'Tue', full: 'Tuesday' },
  { dow: 4, label: 'Wed', full: 'Wednesday' },
  { dow: 5, label: 'Thu', full: 'Thursday' },
  { dow: 6, label: 'Fri', full: 'Friday' },
  { dow: 0, label: 'Sat', full: 'Saturday' },
];

const TIME_BUCKETS = [
  { key: 'morning', label: '🌅 Morning', hours: '5 AM – 12 PM', representativeHour: 9 },
  { key: 'afternoon', label: '☀️ Afternoon', hours: '12 PM – 6 PM', representativeHour: 14 },
  { key: 'night', label: '🌙 Night', hours: '6 PM – 5 AM', representativeHour: 21 },
];

// Map JS getDay() (0=Sunday) to Instacart dow (0=Saturday)
function jsToInstacartDow(jsDay) {
  const map = { 0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0 };
  return map[jsDay];
}

function getCurrentTimeBucketIndex() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour <= 11) return 0;
  if (hour >= 12 && hour <= 17) return 1;
  return 2;
}

export default function CartPage() {
  const { user, getToken } = useAuth();
  const { items, addItem, updateQuantity, removeItem, clearCart, totalItems, totalPrice } = useCart();
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [recs, setRecs] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const navigate = useNavigate();

  // Coupon state
  const [coupon, setCoupon] = useState(null);
  const [applyCoupon, setApplyCoupon] = useState(false);

  // Trending state
  const now = new Date();
  const [selectedDow, setSelectedDow] = useState(jsToInstacartDow(now.getDay()));
  const [selectedBucketIdx, setSelectedBucketIdx] = useState(getCurrentTimeBucketIndex());
  const [trendingProducts, setTrendingProducts] = useState([]);
  const [trendingLoading, setTrendingLoading] = useState(false);
  const [trendingMeta, setTrendingMeta] = useState({});

  // Fetch user profile to get coupon when logged in
  useEffect(() => {
    if (!user) return;
    
    const fetchProfile = async () => {
      try {
        const token = await getToken();
        console.log('[CartPage] Fetching profile for user:', user.uid);
        const profile = await fetchUserProfile(token, user.uid);
        console.log('[CartPage] Profile received:', profile);
        console.log('[CartPage] Coupon data:', profile.coupon);
        
        if (profile.coupon && !profile.coupon.is_used && !profile.coupon.expired) {
          console.log('[CartPage] Setting coupon and applyCoupon to true');
          setCoupon(profile.coupon);
          setApplyCoupon(true); // Auto-apply if available
        } else {
          console.log('[CartPage] Coupon not available - is_used:', profile.coupon?.is_used, 'expired:', profile.coupon?.expired);
        }
      } catch (err) {
        console.error('[CartPage] Failed to load profile:', err);
      }
    };
    
    fetchProfile();
  }, [user, getToken]);

  // Fetch FP-Growth recommendations whenever cart changes
  useEffect(() => {
    if (items.length === 0) {
      setRecs([]);
      return;
    }

    const loadRecs = async () => {
      setRecsLoading(true);
      try {
        const cartNames = items.map((i) => i.name);
        const token = user ? await getToken() : null;
        // Force FP-Growth by sending order_count=0
        const res = await fetchRecommendations(cartNames, 0, token);
        // Filter to only FP-Growth results (not popularity fallback)
        const fpRecs = (res.recommendations || []).filter(
          (r) => r.source === 'fp_growth'
        );
        setRecs(fpRecs.slice(0, 6));
      } catch {
        setRecs([]);
      } finally {
        setRecsLoading(false);
      }
    };

    const timeout = setTimeout(loadRecs, 400);
    return () => clearTimeout(timeout);
  }, [items, user]);

  // Fetch trending products when day/time selection changes
  useEffect(() => {
    const loadTrending = async () => {
      setTrendingLoading(true);
      try {
        const bucket = TIME_BUCKETS[selectedBucketIdx];
        const res = await fetchTrending(selectedDow, bucket.representativeHour, 10);
        setTrendingProducts(res.products || []);
        setTrendingMeta({
          day: res.day,
          timeBucket: res.time_bucket,
          timeBucketInfo: res.time_bucket_info,
        });
      } catch (err) {
        console.warn('[Trending] Error:', err.message);
        setTrendingProducts([]);
      } finally {
        setTrendingLoading(false);
      }
    };
    loadTrending();
  }, [selectedDow, selectedBucketIdx]);

  const handlePlaceOrder = async () => {
    if (!user) {
      navigate('/login');
      return;
    }

    if (items.length === 0) return;

    setLoading(true);
    try {
      const token = await getToken();
      const orderItems = items.map((i) => ({
        product_id: i.id,
        quantity: i.quantity,
        // Also include full details for Firestore
        name: i.name,
        price: i.price,
        emoji: i.emoji,
      }));

      // Pass coupon info to createOrder
      await createOrder(orderItems, token, user.uid, applyCoupon && coupon ? coupon : null);
      clearCart();
      setCoupon(null); // Clear coupon after order
      setApplyCoupon(false);
      setToast({ message: 'Order placed successfully! 🎉', type: 'success' });
      setTimeout(() => navigate('/orders'), 2000);
    } catch (err) {
      setToast({ message: err.message || 'Failed to place order', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleAddRec = (rec) => {
    const product = PRODUCTS.find(
      (p) => p.name.toLowerCase() === rec.product_name.toLowerCase()
    );
    if (product) {
      addItem(product);
      setToast({ message: `${product.name} added to cart!`, type: 'success' });
    }
  };

  const selectedDayFull = DAYS.find((d) => d.dow === selectedDow)?.full || '';
  const selectedBucketLabel = TIME_BUCKETS[selectedBucketIdx]?.label || '';

  return (
    <div className="page">
      <div className="cart-container">
        <div className="page-header">
          <h1 className="page-title">Your Cart</h1>
          <p className="page-subtitle">
            {totalItems > 0
              ? `${totalItems} item${totalItems > 1 ? 's' : ''} in your cart`
              : 'Your cart is empty'}
          </p>
        </div>

        {items.length === 0 ? (
          <div className="cart-empty glass-card">
            <div className="cart-empty-icon">🛒</div>
            <p className="cart-empty-text">Nothing here yet!</p>
            <button className="btn btn-primary" onClick={() => navigate('/')}>
              Start Shopping
            </button>
          </div>
        ) : (
          <>
            <div className="glass-card">
              {items.map((item) => (
                <div key={item.id} className="cart-item">
                  <div className="cart-item-emoji">{item.emoji}</div>
                  <div className="cart-item-details">
                    <div className="cart-item-name">{item.name}</div>
                    <div className="cart-item-price">₹{item.price} each</div>
                  </div>
                  <div className="cart-item-controls">
                    <button
                      className="qty-btn"
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    >
                      −
                    </button>
                    <span className="qty-value">{item.quantity}</span>
                    <button
                      className="qty-btn"
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    >
                      +
                    </button>
                  </div>
                  <div className="cart-item-total">
                    ₹{item.price * item.quantity}
                  </div>
                  <button
                    className="cart-remove-btn"
                    onClick={() => removeItem(item.id)}
                    aria-label={`Remove ${item.name}`}
                  >
                    ✕
                  </button>
                </div>
              ))}

              <div className="cart-summary">
                <div style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span className="cart-total-label">Subtotal</span>
                    <span>₹{totalPrice}</span>
                  </div>
                  
                  {applyCoupon && coupon && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', color: '#00C49F', fontWeight: 'bold' }}>
                      <span>🎉 Coupon Discount</span>
                      <span>-₹{coupon.amount}</span>
                    </div>
                  )}
                  
                  <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.5rem', display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', fontSize: '1.1rem' }}>
                    <span>Total</span>
                    <span>₹{applyCoupon && coupon ? Math.max(0, totalPrice - coupon.amount) : totalPrice}</span>
                  </div>
                </div>
              </div>

              {coupon && !applyCoupon && (
                <div style={{ background: 'rgba(0, 196, 159, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem', border: '1px solid #00C49F' }}>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-color)', marginBottom: '0.5rem' }}>
                    ✨ You have a ₹{coupon.amount} coupon available!
                  </div>
                  <button 
                    onClick={() => setApplyCoupon(true)}
                    style={{ background: '#00C49F', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    Apply Coupon
                  </button>
                </div>
              )}
              
              {applyCoupon && coupon && (
                <div style={{ background: 'rgba(0, 196, 159, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem', border: '1px solid #00C49F' }}>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-color)', marginBottom: '0.5rem' }}>
                    ✅ Coupon applied: ₹{coupon.amount} discount
                  </div>
                  <button 
                    onClick={() => setApplyCoupon(false)}
                    style={{ background: 'transparent', color: '#00C49F', border: '1px solid #00C49F', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    Remove Coupon
                  </button>
                </div>
              )}

              <div className="cart-actions">
                <button
                  className="btn btn-secondary"
                  onClick={clearCart}
                  style={{ flex: 1 }}
                >
                  Clear Cart
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handlePlaceOrder}
                  disabled={loading}
                  style={{ flex: 2 }}
                >
                  {loading ? 'Placing Order...' : `Place Order — ₹${applyCoupon && coupon ? Math.max(0, totalPrice - coupon.amount) : totalPrice}`}
                </button>
              </div>
            </div>

            {/* FP-Growth: Frequently Bought Together */}
            {recs.length > 0 && (
              <div className="recs-section" style={{ marginTop: '2rem', borderTop: 'none' }}>
                <div className="recs-header">
                  <h2 className="recs-title">🧠 Frequently Bought Together</h2>
                  <span className="recs-engine-badge engine-fp_growth">FP-Growth</span>
                </div>
                {recsLoading ? (
                  <div className="loading-spinner" />
                ) : (
                  <div className="recs-scroll">
                    {recs.map((rec, i) => {
                      const product = PRODUCTS.find(
                        (p) => p.name.toLowerCase() === rec.product_name.toLowerCase()
                      );
                      const alreadyInCart = items.some(
                        (item) => item.name.toLowerCase() === rec.product_name.toLowerCase()
                      );
                      return (
                        <div key={i} className="rec-card glass-card">
                          <div className="rec-emoji">{product?.emoji || '🛍️'}</div>
                          <div className="rec-name">{rec.product_name}</div>
                          {product && (
                            <div className="product-price">₹{product.price}</div>
                          )}

                          {product && !alreadyInCart && (
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => handleAddRec(rec)}
                            >
                              + Add
                            </button>
                          )}
                          {alreadyInCart && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--accent-green)' }}>
                              ✓ In cart
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
                <div style={{ marginTop: '0.75rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Based on association rules from your basket — powered by FP-Growth algorithm
                </div>
              </div>
            )}
          </>
        )}

        {/* ── Trending Products Section with Day/Time Selector ── */}
        <div className="trending-explorer">
          <div className="trending-explorer-header">
            <h2 className="trending-explorer-title">📊 Trending Products Explorer</h2>
            <p className="trending-explorer-subtitle">
              Discover what shoppers buy at different times
            </p>
          </div>

          {/* Day Selector */}
          <div className="time-selector-group">
            <label className="time-selector-label">Select Day</label>
            <div className="time-selector-row">
              {DAYS.map((day) => (
                <button
                  key={day.dow}
                  className={`time-btn ${selectedDow === day.dow ? 'active' : ''}`}
                  onClick={() => setSelectedDow(day.dow)}
                >
                  {day.label}
                </button>
              ))}
            </div>
          </div>

          {/* Time Bucket Selector */}
          <div className="time-selector-group">
            <label className="time-selector-label">Select Time</label>
            <div className="time-selector-row">
              {TIME_BUCKETS.map((bucket, idx) => (
                <button
                  key={bucket.key}
                  className={`time-btn time-btn-wide ${selectedBucketIdx === idx ? 'active' : ''}`}
                  onClick={() => setSelectedBucketIdx(idx)}
                >
                  <span>{bucket.label}</span>
                  <span className="time-btn-hours">{bucket.hours}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Trending Results */}
          {trendingLoading ? (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
              <div className="loading-spinner" />
              <p style={{ marginTop: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Loading trending products...
              </p>
            </div>
          ) : trendingProducts.length > 0 ? (
            <TrendingSection
              title={`Trending on ${selectedDayFull} ${selectedBucketLabel}`}
              subtitle={`Top products shoppers buy during this time`}
              products={trendingProducts}
              badge="Data-Driven"
              icon="trending"
            />
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No trending data available for this time slot.
            </div>
          )}
        </div>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
