import { useCart } from '../context/CartContext';
import { PRODUCTS } from '../data/products';

const SECTION_ICONS = {
  fire: '🔥',
  chart: '📈',
  star: '🎉',
  clock: '⏰',
  trending: '📊',
};

export default function TrendingSection({ title, subtitle, badge, products = [], icon = 'fire' }) {
  const { addItem } = useCart();

  if (!products || products.length === 0) return null;

  const handleAdd = (trendingProduct) => {
    // Try to find in app catalog first
    const catalogProduct = PRODUCTS.find(
      (p) => p.name.toLowerCase() === trendingProduct.product_name.toLowerCase()
    );
    if (catalogProduct) {
      addItem(catalogProduct);
    } else {
      // Add non-catalog product with available info
      addItem({
        id: trendingProduct.product_name.toLowerCase().replace(/\s+/g, '_'),
        name: trendingProduct.product_name,
        department: trendingProduct.department || 'other',
        price: 0,
        emoji: trendingProduct.emoji || '📦',
      });
    }
  };

  return (
    <div className="trending-section">
      <div className="trending-header">
        <div className="trending-title-group">
          <span className="trending-icon">{SECTION_ICONS[icon] || '🔥'}</span>
          <div>
            <h2 className="trending-title">{title}</h2>
            {subtitle && <p className="trending-subtitle">{subtitle}</p>}
          </div>
        </div>
        {badge && (
          <span className="trending-badge">{badge}</span>
        )}
      </div>

      <div className="trending-scroll">
        {products.map((product, i) => {
          const catalogMatch = PRODUCTS.find(
            (p) => p.name.toLowerCase() === product.product_name.toLowerCase()
          );
          const isInCatalog = !!catalogMatch;

          return (
            <div
              key={`${product.product_name}-${i}`}
              className="trending-card glass-card"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className="trending-rank">#{i + 1}</div>
              <div className="trending-card-emoji">
                {catalogMatch?.emoji || product.emoji || '📦'}
              </div>
              <div className="trending-card-name">{product.product_name}</div>
              <div className="trending-card-dept">{product.department}</div>


              {/* Reorder rate indicator */}
              {product.reorder_rate > 0 && (
                <div className="trending-reorder-rate">
                  🔄 {(product.reorder_rate * 100).toFixed(0)}% reorder
                </div>
              )}

              {isInCatalog && catalogMatch.price > 0 && (
                <div className="trending-card-price">₹{catalogMatch.price}</div>
              )}

              <button
                className="btn btn-primary btn-sm trending-add-btn"
                onClick={() => handleAdd(product)}
              >
                + Add
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
