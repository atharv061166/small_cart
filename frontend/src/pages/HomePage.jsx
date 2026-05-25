import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import ProductCard from '../components/ProductCard';
import CartDrawer from '../components/CartDrawer';
import TrendingSection from '../components/TrendingSection';
import CouponModal from '../components/CouponModal';
import { DEPARTMENTS, PRODUCTS, getProductsByDepartment } from '../data/products';
import { fetchRecommendations, fetchUserProfile, fetchHomepageTrending, fetchProducts } from '../api';

export default function HomePage({ isCartDrawerOpen, onCartDrawerClose, searchQuery }) {
  const { user, getToken } = useAuth();
  const { items: cartItems, addItem } = useCart();
  const [selectedDept, setSelectedDept] = useState(null);
  const [products, setProducts] = useState(PRODUCTS);
  const [productsLoading, setProductsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState(null);
  const [recsEngine, setRecsEngine] = useState('');
  const [recsLoading, setRecsLoading] = useState(false);
  const [showRecsModal, setShowRecsModal] = useState(false);
  const [orderCount, setOrderCount] = useState(0);
  const [userOrders, setUserOrders] = useState([]);

  // Trending state
  const [trendingData, setTrendingData] = useState(null);
  const [trendingLoading, setTrendingLoading] = useState(true);

  // Coupon state
  const [couponData, setCouponData] = useState(null);
  const [showCouponModal, setShowCouponModal] = useState(false);

  const displayProducts = products;

  // Load products based on department and search query
  useEffect(() => {
    let active = true;
    const loadProducts = async () => {
      setProductsLoading(true);
      try {
        const res = await fetchProducts(selectedDept, searchQuery);
        if (active) {
          setProducts(res.products || []);
        }
      } catch (err) {
        console.warn('[Search] Backend search failed, falling back to local search:', err.message);
        if (active) {
          let filtered = selectedDept
            ? getProductsByDepartment(selectedDept)
            : PRODUCTS;

          if (searchQuery) {
            const queryLower = searchQuery.toLowerCase().trim();
            filtered = filtered.filter(p => p.name.toLowerCase().includes(queryLower));
          }
          setProducts(filtered);
        }
      } finally {
        if (active) {
          setProductsLoading(false);
        }
      }
    };

    const delay = searchQuery ? 300 : 0;
    const timeout = setTimeout(loadProducts, delay);

    return () => {
      active = false;
      clearTimeout(timeout);
    };
  }, [selectedDept, searchQuery]);

  // Load user profile and orders for recommendations
  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const token = await getToken();
        const profile = await fetchUserProfile(token, user.uid);
        setOrderCount(profile.order_count || profile.orderCount || 0);

        // Handle coupon modal
        if (profile.coupon && !profile.coupon.is_used && !profile.coupon.expired) {
          setCouponData(profile.coupon);
          setShowCouponModal(true);
        }

        const { fetchOrders } = await import('../api');
        const ordersData = await fetchOrders(token, user.uid);
        setUserOrders(ordersData.orders || []);
      } catch {
        // Backend may not be running — that's fine
      }
    })();
  }, [user]);

  // Fetch homepage trending data on mount
  useEffect(() => {
    const loadTrending = async () => {
      setTrendingLoading(true);
      try {
        const data = await fetchHomepageTrending();
        setTrendingData(data);
      } catch (err) {
        console.warn('[Trending] Could not load trending data:', err.message);
        setTrendingData(null);
      } finally {
        setTrendingLoading(false);
      }
    };
    loadTrending();
  }, []);

  // Fetch recommendations when cart changes
  useEffect(() => {
    const loadRecs = async () => {
      setRecsLoading(true);
      try {
        const cartNames = cartItems.map((i) => i.name);
        const token = user ? await getToken() : null;
        const res = await fetchRecommendations(cartNames, orderCount, token, userOrders);
        setRecommendations(res.recommendations || []);
        setRecsEngine(res.engine || 'popularity');
        // Show modal when recommendations are loaded
        if (res.recommendations && res.recommendations.length > 0) {
          setShowRecsModal(true);
        }
      } catch {
        // Backend not running — show empty recs
        setRecommendations([]);
        setShowRecsModal(false);
      } finally {
        setRecsLoading(false);
      }
    };

    // Debounce
    if (cartItems.length === 0) {
      setRecommendations(null);
      setShowRecsModal(false);
      return;
    }
    const timeout = setTimeout(loadRecs, 500);
    return () => clearTimeout(timeout);
  }, [cartItems, orderCount, user, userOrders]);

  const engineLabels = {
    fp_growth: '🧠 FP-Growth',
    hybrid: '⚡ Hybrid',
    lightgbm: '🎯 LightGBM',
    popularity: '🔥 Popular',
  };

  const handleAddRec = (rec) => {
    // Try to find in our catalog
    const product = PRODUCTS.find(
      (p) => p.name.toLowerCase() === rec.product_name.toLowerCase()
    );
    if (product) {
      addItem(product);
    }
  };

  const sections = trendingData?.sections || {};

  return (
    <>
      <CartDrawer isOpen={isCartDrawerOpen} onClose={onCartDrawerClose} />

      {showCouponModal && couponData && (
        <CouponModal
          coupon={couponData}
          onClose={() => setShowCouponModal(false)}
        />
      )}

      <div className="page">
        {/* Hero Section */}
        <div className="hero-banner">
          <div className="hero-content">
            <div className="hero-badge">
              <span className="badge-icon">🧠</span>
              <span className="badge-text">Powered by AI Intelligence</span>
            </div>
            <h1 className="hero-title">Smart Grocery Recommendations</h1>
            <p className="hero-subtitle">Powered by Machine Learning</p>
            <p className="hero-description">
              Add products to your cart and get recommendations instantly
            </p>
            {cartItems.length > 0 && (
              <div className="hero-status">
                <span className="status-dot"></span>
                <span className="status-text">Recommendation Engine Active</span>
              </div>
            )}
          </div>
        </div>

        {/* ── Trending Sections ── */}
        {trendingLoading ? (
          <div className="trending-loading">
            <div className="loading-spinner" />
            <p>Loading trending products...</p>
          </div>
        ) : trendingData ? (
          <div className="trending-container">
            <div className="trending-grid">
              {sections.trending_now && (
                <TrendingSection
                  title={sections.trending_now.title}
                  subtitle={sections.trending_now.subtitle}
                  products={sections.trending_now.products}
                  badge={trendingData.time_bucket_label}
                  icon="fire"
                />
              )}

              {sections.popular_today && (
                <TrendingSection
                  title={sections.popular_today.title}
                  subtitle={sections.popular_today.subtitle}
                  products={sections.popular_today.products}
                  icon="chart"
                />
              )}
            </div>

            {/* Trending departments */}
            {trendingData.trending_departments?.length > 0 && (
              <div className="trending-depts-bar">
                <span className="trending-depts-label">Trending Departments:</span>
                {trendingData.trending_departments.map((dept, i) => (
                  <span key={i} className="trending-dept-chip">
                    {dept.emoji} {dept.department}
                  </span>
                ))}
              </div>
            )}
          </div>
        ) : null}

        {/* Category Filter */}
        <div className="category-filter">
          <button
            className={`category-btn ${!selectedDept ? 'active' : ''}`}
            onClick={() => setSelectedDept(null)}
          >
            All Products
          </button>
          {DEPARTMENTS.map((dept) => (
            <button
              key={dept.id}
              className={`category-btn ${selectedDept === dept.id ? 'active' : ''}`}
              onClick={() => setSelectedDept(selectedDept === dept.id ? null : dept.id)}
            >
              <span className="category-icon">{dept.icon}</span>
              <span className="category-name">{dept.name}</span>
            </button>
          ))}
        </div>

        {/* Products */}
        <div className="section-header">
          <h2 className="section-title">
            {selectedDept
              ? DEPARTMENTS.find((d) => d.id === selectedDept)?.name
              : 'All Products'}
          </h2>
          <span className="section-subtitle">{displayProducts.length} items</span>
        </div>

        <div className="product-grid" style={{ opacity: productsLoading ? 0.6 : 1, transition: 'opacity 0.2s ease' }}>
          {displayProducts.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
          {displayProducts.length === 0 && !productsLoading && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              No products found matching your search.
            </div>
          )}
          {displayProducts.length === 0 && productsLoading && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem' }}>
              <div className="loading-spinner" style={{ margin: '0 auto' }} />
              <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Searching...</p>
            </div>
          )}
        </div>

        {/* Recommendations Modal (Bottom Sheet) */}
        {showRecsModal && (
          <div className="recs-modal-overlay" onClick={() => setShowRecsModal(false)}>
            <div className="recs-modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="recs-modal-header">
                <h2 className="recs-modal-title">✨ Recommended for You</h2>
                <button
                  className="recs-modal-close"
                  onClick={() => setShowRecsModal(false)}
                >
                  ✕
                </button>
              </div>

              {recsLoading ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                  <div className="loading-spinner" />
                  <p style={{ marginTop: '0.5rem', color: 'var(--text-muted)' }}>Loading recommendations...</p>
                </div>
              ) : recommendations && recommendations.length > 0 ? (
                <>
                  <div className="recs-scroll">
                    {recommendations.map((rec, i) => {
                      const product = PRODUCTS.find(
                        (p) => p.name.toLowerCase() === rec.product_name.toLowerCase()
                      );
                      return (
                        <div key={i} className="rec-card glass-card">
                          <div className="rec-emoji">{product?.emoji || '🛍️'}</div>
                          <div className="rec-name">{rec.product_name}</div>
                          {product && (
                            <div className="product-price">₹{product.price}</div>
                          )}
                          <div className="rec-score">
                            Score: {(rec.score * 100).toFixed(0)}%
                          </div>
                          {product && (
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => {
                                handleAddRec(rec);
                                setShowRecsModal(false);
                              }}
                            >
                              + Add
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Engine explanation */}
                  <div style={{ marginTop: '1rem', padding: '1rem', background: 'var(--bg-glass)', borderRadius: 'var(--radius-md)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {recsEngine && (
                      <>
                        {recsEngine === 'fp_growth' && (
                          <>🧠 <strong>New user mode (1-10 orders):</strong> Recommendations powered by FP-Growth association rules + popularity. Place more orders to unlock personalized ML recommendations!</>
                        )}
                        {recsEngine === 'hybrid' && (
                          <>⚡ <strong>Hybrid mode (10-20 orders):</strong> Combining FP-Growth basket analysis with LightGBM predictions for better accuracy.</>
                        )}
                        {recsEngine === 'lightgbm' && (
                          <>🎯 <strong>Personalized mode (20+ orders):</strong> LightGBM model trained on your shopping patterns for maximum relevance.</>
                        )}
                      </>
                    )}
                  </div>
                </>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
