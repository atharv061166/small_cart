import { db } from './firebase';
import { doc, getDoc, setDoc, addDoc, collection, getDocs, query, orderBy, updateDoc, increment } from 'firebase/firestore';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function apiFetch(path, options = {}) {
  const { headers: optHeaders, ...restOptions } = options;
  const res = await fetch(`${API_URL}${path}`, {
    ...restOptions,
    headers: {
      'Content-Type': 'application/json',
      ...optHeaders,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API error');
  }
  return res.json();
}

export async function fetchRecommendations(cartItems = [], orderCount = 0, token = null, userOrders = null) {
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  
  return apiFetch('/api/recommendations', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      cart_items: cartItems,
      order_count: orderCount,
      user_orders: userOrders,
    }),
  });
}

// Save order to Firestore subcollection: users/{uid}/orders/{auto-id}
async function saveOrderToFirestore(userId, orderData) {
  if (!userId) {
    console.warn('[Firestore] No userId provided');
    return null;
  }

  try {
    console.log('[Firestore] Saving order for user:', userId);
    
    // Ensure the user document exists
    const userRef = doc(db, 'users', userId);
    const userDoc = await getDoc(userRef);
    
    if (!userDoc.exists()) {
      // Create user document if it doesn't exist
      await setDoc(userRef, {
        uid: userId,
        orderCount: 0,
        createdAt: new Date().toISOString(),
      });
      console.log('[Firestore] Created user document');
    }
    
    // Add order to subcollection: users/{uid}/orders/{auto-generated-id}
    const ordersCollectionRef = collection(db, 'users', userId, 'orders');
    const orderDocRef = await addDoc(ordersCollectionRef, orderData);
    console.log('[Firestore] Order saved to subcollection with ID:', orderDocRef.id);
    
    // Update the order count on the user document
    await updateDoc(userRef, {
      orderCount: increment(1),
      lastOrderAt: new Date().toISOString(),
    });
    console.log('[Firestore] User order count updated');
    
    return orderDocRef.id;
  } catch (error) {
    console.error('[Firestore] Error saving order:', error);
    throw error;
  }
}

// Create order — saves to Firestore as primary, backend API as secondary
export async function createOrder(items, token, userId, coupon = null) {
  // Build the order data with full product details
  const orderItems = items.map((item) => ({
    product_id: item.product_id || item.id,
    product_name: item.name,
    department: item.department || '',
    price: item.price,
    quantity: item.quantity,
    item_total: Math.round(item.price * item.quantity * 100) / 100,
    emoji: item.emoji || '📦',
  }));

  const subtotal = Math.round(items.reduce((sum, item) => sum + (item.price * item.quantity), 0) * 100) / 100;
  const discountAmount = coupon ? coupon.amount : 0;
  const finalTotal = Math.max(0, subtotal - discountAmount);

  const orderData = {
    items: orderItems,
    subtotal: subtotal,
    discount_amount: discountAmount,
    coupon_id: coupon ? coupon.issued_at : null,
    total: finalTotal,
    item_count: items.reduce((sum, item) => sum + item.quantity, 0),
    created_at: new Date().toISOString(),
    status: 'completed',
  };

  console.log('[Order] Creating order:', {
    userId,
    itemCount: items.length,
    subtotal: subtotal,
    discount: discountAmount,
    finalTotal: finalTotal,
  });

  // Step 1: Save to Firestore (primary storage — always works with client SDK)
  let firestoreOrderId = null;
  if (userId) {
    try {
      firestoreOrderId = await saveOrderToFirestore(userId, orderData);
      console.log('[Firestore] Order saved successfully, ID:', firestoreOrderId);
    } catch (firestoreError) {
      console.error('[Firestore] Failed to save order:', firestoreError);
      // Don't throw yet — try backend as fallback
    }
  }

  // Step 2: Also try backend API (for recommendation engine tracking)
  try {
    const backendItems = items.map((i) => ({
      product_id: i.product_id || i.id,
      quantity: i.quantity,
    }));

    const result = await apiFetch('/api/orders', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ items: backendItems, coupon: coupon }),
    });
    console.log('[API] Backend order also created:', result);
  } catch (backendError) {
    // Backend failing is OK — Firestore is our primary store
    console.warn('[API] Backend order creation failed (non-critical):', backendError.message);
  }

  if (firestoreOrderId) {
    return { order_id: firestoreOrderId, order: orderData };
  }

  // If both Firestore and backend failed, throw
  throw new Error('Failed to save order. Please check your internet connection and try again.');
}

// Fetch orders from Firestore subcollection
export async function fetchOrders(token, userId) {
  if (!userId) {
    throw new Error('User not authenticated');
  }

  try {
    console.log('[Firestore] Fetching orders for user:', userId);
    const ordersCollectionRef = collection(db, 'users', userId, 'orders');
    const q = query(ordersCollectionRef, orderBy('created_at', 'desc'));
    const snapshot = await getDocs(q);
    
    const orders = [];
    snapshot.forEach((doc) => {
      orders.push({
        id: doc.id,
        ...doc.data(),
      });
    });
    
    console.log('[Firestore] Fetched', orders.length, 'orders');
    return { orders };
  } catch (firestoreError) {
    console.error('[Firestore] Error fetching orders:', firestoreError);
    
    // Fallback: try backend API
    try {
      console.log('[API] Trying backend as fallback...');
      const result = await apiFetch('/api/orders', {
        headers: { Authorization: `Bearer ${token}` },
      });
      return result;
    } catch (backendError) {
      console.error('[API] Backend also failed:', backendError);
      // Return empty orders rather than crashing
      return { orders: [] };
    }
  }
}

// Fetch user profile from Firestore
export async function fetchUserProfile(token, userId) {
  if (!userId) {
    return { order_count: 0, email: '', coupon: null };
  }

  // Call backend API to trigger coupon calculation logic
  try {
    console.log('[Profile] Fetching from backend:', userId);
    const result = await apiFetch('/api/user/profile', {
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log('[Profile] Backend response:', result);
    return result;
  } catch (backendError) {
    console.error('[Profile] Backend error:', backendError);
    
    // Fallback: read directly from Firestore if backend fails
    try {
      console.log('[Firestore] Fallback: Reading from Firestore');
      const userRef = doc(db, 'users', userId);
      const userDoc = await getDoc(userRef);
      
      if (userDoc.exists()) {
        const data = userDoc.data();
        const profile = {
          order_count: data.orderCount || data.order_count || 0,
          email: data.email || '',
          uid: data.uid || userId,
          coupon: data.coupon || null,
        };
        console.log('[Firestore] Profile loaded:', profile);
        return profile;
      }
      
      return { order_count: 0, email: '', uid: userId, coupon: null };
    } catch {
      return { order_count: 0, email: '', uid: userId, coupon: null };
    }
  }
}

// ── Trending Products API ──

export async function fetchTrending(dow, hour, n = 10) {
  return apiFetch(`/api/trending?dow=${dow}&hour=${hour}&n=${n}`);
}

export async function fetchHomepageTrending() {
  return apiFetch('/api/trending/homepage');
}

// ── Admin API ──

export async function fetchAdminDashboardData() {
  return apiFetch('/api/admin/dashboard');
}

export async function fetchAdminInventory(search = '') {
  return apiFetch(`/api/admin/inventory?search=${encodeURIComponent(search)}`);
}

export async function fetchAdminProductDetail(productName) {
  return apiFetch(`/api/admin/product/${encodeURIComponent(productName)}`);
}

export async function fetchAdminSegmentation() {
  return apiFetch('/api/admin/segmentation');
}

export async function fetchProducts(department = null, search = '') {
  const query = [];
  if (department) {
    query.push(`department=${encodeURIComponent(department)}`);
  }
  if (search) {
    query.push(`search=${encodeURIComponent(search)}`);
  }
  const queryString = query.length > 0 ? `?${query.join('&')}` : '';
  return apiFetch(`/api/products${queryString}`);
}

