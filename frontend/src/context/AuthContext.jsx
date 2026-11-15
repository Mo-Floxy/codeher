import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { api, endpoints, onUnauthorized, tokenStore } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  // undefined = unknown (splash), false = no session, true = signed in.
  const [status, setStatus] = useState(undefined);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const loadSession = useCallback(async () => {
    if (!tokenStore.access && !tokenStore.refresh) {
      setStatus(false);
      return;
    }
    try {
      const data = await api.get(endpoints.me);
      if (!mounted.current) return;
      setUser(data.user);
      setProfile(data.profile);
      setStatus(true);
    } catch {
      if (!mounted.current) return;
      tokenStore.clear();
      setUser(null);
      setProfile(null);
      setStatus(false);
    }
  }, []);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  useEffect(
    () =>
      onUnauthorized(() => {
        setUser(null);
        setProfile(null);
        setStatus(false);
      }),
    []
  );

  const applySession = useCallback((data) => {
    tokenStore.set({ access: data.access, refresh: data.refresh });
    setUser(data.user);
    setProfile(data.profile ?? null);
    setStatus(true);
    return data.user;
  }, []);

  const login = useCallback(
    async (credentials) => {
      const data = await api.post(endpoints.login, credentials);
      applySession(data);
      // The token endpoints return the user only; the profile needs /auth/me/.
      await loadSession();
      return data.user;
    },
    [applySession, loadSession]
  );

  const register = useCallback(
    async (payload) => {
      const data = await api.post(endpoints.register, payload);
      applySession(data);
      await loadSession();
      return data.user;
    },
    [applySession, loadSession]
  );

  const logout = useCallback(async () => {
    const refresh = tokenStore.refresh;
    tokenStore.clear();
    setUser(null);
    setProfile(null);
    setStatus(false);
    if (refresh) {
      // Best effort — the local session is already gone either way.
      await api.post(endpoints.logout, { refresh }).catch(() => {});
    }
  }, []);

  const updateProfile = useCallback((next) => {
    setProfile((prev) => (next && typeof next === "object" ? { ...prev, ...next } : prev));
  }, []);

  const updateUser = useCallback((next) => {
    setUser((prev) => (next && typeof next === "object" ? { ...prev, ...next } : prev));
  }, []);

  // Derived once here so role checks never drift between components.
  const value = useMemo(
    () => ({
      user,
      profile,
      isAuthenticated: status === true,
      isBooting: status === undefined,
      role: user?.role ?? "learner",
      isAdmin: user?.role === "admin" || Boolean(user?.is_staff),
      isMentor: user?.role === "mentor" || user?.role === "admin",
      login,
      register,
      logout,
      reload: loadSession,
      updateProfile,
      updateUser,
    }),
    [user, profile, status, login, register, logout, loadSession, updateProfile, updateUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
