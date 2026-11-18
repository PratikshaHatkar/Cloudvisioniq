import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('visioniq_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('visioniq_token') || null);
  const [loading, setLoading] = useState(true);

  // Validate and restore session on page mount / refresh
  const restoreSession = useCallback(async () => {
    try {
      // Even without a stored Bearer token, HttpOnly cookie might be present
      const profile = await api.getCurrentUser();
      if (profile && profile.id) {
        setUser(profile);
        localStorage.setItem('visioniq_user', JSON.stringify(profile));
      } else {
        setUser(null);
        localStorage.removeItem('visioniq_user');
        localStorage.removeItem('visioniq_token');
      }
    } catch (_err) {
      setUser(null);
      localStorage.removeItem('visioniq_user');
      localStorage.removeItem('visioniq_token');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  const login = async ({ email, password }) => {
    const res = await api.login({ email, password });
    if (res.access_token) {
      setToken(res.access_token);
      localStorage.setItem('visioniq_token', res.access_token);
    }
    if (res.user) {
      setUser(res.user);
      localStorage.setItem('visioniq_user', JSON.stringify(res.user));
    }
    return res;
  };

  const register = async ({ name, email, password }) => {
    const res = await api.register({ name, email, password });
    if (res.access_token) {
      setToken(res.access_token);
      localStorage.setItem('visioniq_token', res.access_token);
    }
    if (res.user) {
      setUser(res.user);
      localStorage.setItem('visioniq_user', JSON.stringify(res.user));
    }
    return res;
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.warn('Backend logout cleanup notice:', err.message);
    } finally {
      setUser(null);
      setToken(null);
      localStorage.removeItem('visioniq_user');
      localStorage.removeItem('visioniq_token');
    }
  };

  const value = {
    user,
    token,
    isAuthenticated: Boolean(user),
    loading,
    login,
    register,
    logout,
    restoreSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
