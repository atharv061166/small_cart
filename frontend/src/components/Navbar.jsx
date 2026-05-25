import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { useTheme } from '../context/ThemeContext';
import { useState, useEffect, useRef } from 'react';

export default function Navbar({ onCartClick, searchQuery, setSearchQuery }) {
  const { user, logout } = useAuth();
  const { totalItems } = useCart();
  const { isDark, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const isActive = (path) => location.pathname === path ? 'active' : '';

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    setIsMenuOpen(false);
  }, [location]);

  // If on cart page, don't show cart icon click handler
  const handleCartClick = () => {
    if (location.pathname !== '/cart' && onCartClick) {
      onCartClick();
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <Link to="/" className="navbar-brand">
          <span className="brand-icon">🍎</span>
          <div className="brand-info">
            <span className="brand-name">Instacart Basket</span>
            <span className="brand-subtitle">AI-Growth Intelligence</span>
          </div>
        </Link>
      </div>

      <div className="navbar-center">
        <div className="search-container">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search products..."
            className="search-input"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              if (location.pathname !== '/' && e.target.value.trim() !== '') {
                navigate('/');
              }
            }}
          />
        </div>
      </div>

      <div className="navbar-right">
        {user ? (
          <>
            <button 
              className="navbar-icon-btn" 
              title={isDark ? 'Light mode' : 'Dark mode'}
              onClick={toggleTheme}
            >
              {isDark ? '☀️' : '🌙'}
            </button>
            {location.pathname === '/' ? (
              <button 
                className={`navbar-icon-btn cart-badge ${totalItems > 0 ? 'has-items' : ''}`}
                onClick={handleCartClick}
                title="Open cart"
              >
                🛒
                {totalItems > 0 && <span className="cart-count">{totalItems}</span>}
              </button>
            ) : (
              <Link 
                to="/cart" 
                className={`navbar-icon-btn cart-badge ${isActive('/cart')} ${totalItems > 0 ? 'has-items' : ''}`}
                title="View cart"
              >
                🛒
                {totalItems > 0 && <span className="cart-count">{totalItems}</span>}
              </Link>
            )}
            <div className="navbar-menu" ref={menuRef}>
              <button 
                className="navbar-icon-btn" 
                title="Menu"
                onClick={() => setIsMenuOpen(!isMenuOpen)}
              >
                ⋮
              </button>
              <div className={`navbar-dropdown ${isMenuOpen ? 'show' : ''}`}>
                <Link to="/orders" className="dropdown-item">
                  📋 Order History
                </Link>
                <Link to="/admin" className="dropdown-item">
                  📊 Admin Dashboard
                </Link>
                <hr className="dropdown-divider" />
                <button className="dropdown-item logout-btn" onClick={logout}>
                  🚪 Logout
                </button>
              </div>
            </div>
          </>
        ) : (
          <Link to="/login" className="btn btn-primary btn-sm">
            Sign In
          </Link>
        )}
      </div>
    </nav>
  );
}
