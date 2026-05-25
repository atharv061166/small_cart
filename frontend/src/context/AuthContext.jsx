import { createContext, useContext, useState, useEffect } from 'react';
import { auth, db } from '../firebase';
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
} from 'firebase/auth';
import { doc, setDoc, getDoc } from 'firebase/firestore';

const AuthContext = createContext(null);

// Helper: Create or get user profile in Firestore
const ensureUserProfile = async (user) => {
  if (!user) return null;
  
  try {
    console.log('[Firestore] Creating/checking profile for user:', user.uid);
    const userRef = doc(db, 'users', user.uid);
    const userDoc = await getDoc(userRef);
    
    const profileData = {
      uid: user.uid,
      email: user.email,
      createdAt: new Date().toISOString(),
      orderCount: 0,
    };

    if (!userDoc.exists()) {
      console.log('[Firestore] Creating new user profile with data:', profileData);
      // Create new user profile — orders are stored in subcollection, not here
      await setDoc(userRef, profileData);
      console.log('[Firestore] Profile created successfully');
    } else {
      console.log('[Firestore] Profile already exists:', userDoc.data());
    }
    
    return profileData;
  } catch (error) {
    console.error('[Firestore] Error ensuring user profile:', error);
    return null;
  }
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (u) => {
      if (u) {
        console.log('[Auth] User signed in:', u.uid);
        // Ensure user profile exists in Firestore
        await ensureUserProfile(u);
      } else {
        console.log('[Auth] User signed out');
      }
      setUser(u);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const login = async (email, password) => {
    const result = await signInWithEmailAndPassword(auth, email, password);
    // Ensure user profile exists on login too
    await ensureUserProfile(result.user);
    return result;
  };

  const signup = async (email, password) => {
    const result = await createUserWithEmailAndPassword(auth, email, password);
    // Create user profile in Firestore immediately after signup
    await ensureUserProfile(result.user);
    return result;
  };

  const logout = () => signOut(auth);

  const getToken = async () => {
    if (user) return user.getIdToken();
    return null;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, getToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
