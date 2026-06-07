import { createContext, useContext, useEffect, useState } from 'react';
import { auth } from '../api.js';


const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    auth.me()
      .then((u) => { if (!cancelled) setUser(u); })
      .catch(() => { if (!cancelled) setUser(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function login(credentials) {
    const data = await auth.login(credentials);
    setUser(data.user);
    return data.user;
  }

  async function register(payload) {
    const data = await auth.register(payload);
    return data;
  }

  async function verifyEmail(payload) {
    const data = await auth.verifyEmail(payload);
    setUser(data.user);
    return data.user;
  }

  async function updateUsername(username) {
    const updated = await auth.updateUsername({ username });
    setUser(updated);
    return updated;
  }

  async function deleteAccount() {
    await auth.deleteAccount();
    setUser(null);
  }

  async function logout() {
    try {
      await auth.logout();
    } catch {
      /* ignore */
    }
    setUser(null);
  }

  const value = { user, loading, login, register, verifyEmail, logout, deleteAccount, updateUsername };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
