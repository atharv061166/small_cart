import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import CartPage from './pages/CartPage';
import OrderHistoryPage from './pages/OrderHistoryPage';
import AdminDashboardPage from './pages/AdminDashboardPage';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-spinner" />;
  if (!user) return <Navigate to="/login" />;
  return children;
}

function AppRoutes() {
  const { user, loading } = useAuth();
  const [cartDrawerOpen, setCartDrawerOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div className="loading-spinner" />
      </div>
    );
  }

  return (
    <>
      <Navbar 
        onCartClick={() => setCartDrawerOpen(true)} 
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
      />
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" /> : <LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <HomePage 
                isCartDrawerOpen={cartDrawerOpen} 
                onCartDrawerClose={() => setCartDrawerOpen(false)}
                onOpenCart={() => setCartDrawerOpen(true)}
                searchQuery={searchQuery}
              />
            </ProtectedRoute>
          }
        />
        <Route
          path="/cart"
          element={
            <ProtectedRoute>
              <CartPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/orders"
          element={
            <ProtectedRoute>
              <OrderHistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <CartProvider>
            <AppRoutes />
          </CartProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
