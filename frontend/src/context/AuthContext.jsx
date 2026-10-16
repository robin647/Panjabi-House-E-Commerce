import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, setAuthLostHandler, tokenStore } from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(() => !tokenStore.get());

  useEffect(() => {
    setAuthLostHandler(() => setUser(null));
    if (!tokenStore.get()) {
      setReady(true);
      return undefined;
    }
    let alive = true;
    api
      .get("/profile/", { auth: true })
      .then((r) => alive && setUser(r.data))
      .catch(() => tokenStore.clear())
      .finally(() => alive && setReady(true));
    return () => {
      alive = false;
    };
  }, []);

  const login = useCallback(async (identifier, password) => {
    const { data } = await api.post("/auth/login/", { identifier, password });
    tokenStore.set(data.tokens);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (payload) => {
    const { data } = await api.post("/auth/register/", payload);
    tokenStore.set(data.tokens);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    const tokens = tokenStore.get();
    try {
      if (tokens?.refresh) await api.post("/auth/logout/", { refresh: tokens.refresh }, { auth: true });
    } catch {
      /* the local session is cleared regardless */
    }
    tokenStore.clear();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, ready, login, register, logout, setUser }), [user, ready, login, register, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
