import React, { useEffect, useState } from 'react';

export default function CouponModal({ coupon, onClose }) {
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    if (!coupon || !coupon.expires_at) return;

    const timer = setInterval(() => {
      const now = new Date();
      const expires = new Date(coupon.expires_at);
      const diff = expires - now;

      if (diff <= 0) {
        setTimeLeft('Expired');
        clearInterval(timer);
        onClose(); // Automatically close if expired while viewing
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const mins = Math.floor((diff / 1000 / 60) % 60);

      setTimeLeft(`${days} day${days !== 1 ? 's' : ''} ${hours} hr${hours !== 1 ? 's' : ''} ${mins} min${mins !== 1 ? 's' : ''}`);
    }, 1000);

    return () => clearInterval(timer);
  }, [coupon, onClose]);

  if (!coupon) return null;

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        <div style={headerStyle}>
          <h2 style={{ margin: 0, fontSize: '1.5rem', color: '#ff6b6b' }}>🎉 You have a special offer waiting!</h2>
        </div>
        
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#00C49F', marginBottom: '1rem' }}>
            ₹{coupon.amount} OFF
          </div>
          <p style={{ fontSize: '1.2rem', marginBottom: '1.5rem', color: 'var(--text-color)' }}>
            your next order!
          </p>
          
          <div style={{ background: 'rgba(255, 107, 107, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <span style={{ fontWeight: 'bold', color: '#ff6b6b' }}>⏱️ Shop fast! Your coupon expires in:</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', marginTop: '0.5rem', color: 'var(--text-color)' }}>
              {timeLeft || 'Calculating...'}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <button 
              onClick={onClose}
              style={{ padding: '1rem', background: '#0088FE', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '1.2rem', fontWeight: 'bold', cursor: 'pointer' }}
            >
              Shop Now
            </button>
            <button 
              onClick={onClose}
              style={{ background: 'transparent', color: 'var(--text-muted)', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
            >
              Remind me later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const overlayStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.7)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 1000,
  backdropFilter: 'blur(5px)'
};

const modalStyle = {
  background: 'var(--card-bg)',
  borderRadius: '20px',
  width: '90%',
  maxWidth: '450px',
  boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
  overflow: 'hidden',
  border: '1px solid var(--border-color)'
};

const headerStyle = {
  background: 'rgba(255, 107, 107, 0.1)',
  padding: '1.5rem',
  textAlign: 'center',
  borderBottom: '1px solid rgba(255, 107, 107, 0.2)'
};
