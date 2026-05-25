import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isSignup) {
        await signup(email, password);
      } else {
        await login(email, password);
      }
      navigate('/');
    } catch (err) {
      const msg = err.message || 'Authentication failed';
      if (msg.includes('user-not-found') || msg.includes('wrong-password') || msg.includes('invalid-credential')) {
        setError('Invalid email or password.');
      } else if (msg.includes('email-already-in-use')) {
        setError('An account with this email already exists.');
      } else if (msg.includes('weak-password')) {
        setError('Password must be at least 6 characters.');
      } else if (msg.includes('invalid-email')) {
        setError('Please enter a valid email address.');
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card glass-card">
        <div style={{ textAlign: 'center', fontSize: '3rem', marginBottom: '0.5rem' }}>🛒</div>
        <h1 className="auth-title">
          {isSignup ? 'Create Account' : 'Welcome Back'}
        </h1>
        <p className="auth-subtitle">
          {isSignup
            ? 'Join SmartCart for personalized grocery recommendations'
            : 'Sign in to your SmartCart account'}
        </p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email</label>
            <input
              id="email"
              className="form-input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              className="form-input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary auth-btn"
            disabled={loading}
          >
            {loading ? 'Please wait...' : isSignup ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div className="auth-switch">
          {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button
            className="auth-switch-link"
            onClick={() => {
              setIsSignup(!isSignup);
              setError('');
            }}
          >
            {isSignup ? 'Sign In' : 'Sign Up'}
          </button>
        </div>
      </div>
    </div>
  );
}
