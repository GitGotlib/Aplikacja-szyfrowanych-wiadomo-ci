import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../api/endpoints';
import { ApiError, UnauthorizedError } from '../api/errors';
import type { LoginRequest, UserPublic } from '../types/dto';

type AuthState = {
  user: UserPublic | null;
  loading: boolean;
  error: string | null;

  refreshMe: () => Promise<void>;
  register: (args: { email: string; username: string; password: string }) => Promise<void>;
  login: (args: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider(props: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refreshMe() {
    try {
      const res = await api.me();
      setUser(res.user);
      setError(null);
    } catch (e) {
      if (e instanceof UnauthorizedError) {
        setUser(null);
        setError(null);
        return;
      }
      setError(e instanceof ApiError ? e.message : 'Nie udało się pobrać sesji.');
    }
  }

  async function register(args: { email: string; username: string; password: string }) {
    setError(null);
    try {
      await api.register(args);
    } catch (e) {
      throw e;
    }
  }

  async function login(args: LoginRequest) {
    setError(null);
    await api.login(args);
    await refreshMe();
  }

  async function logout() {
    setError(null);
    try {
      await api.logout();
    } finally {
      setUser(null);
    }
  }

  useEffect(() => {
    (async () => {
      setLoading(true);
      await refreshMe();
      setLoading(false);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo<AuthState>(
    () => ({ user, loading, error, refreshMe, register, login, logout }),
    [user, loading, error],
  );

  return <AuthContext.Provider value={value}>{props.children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
