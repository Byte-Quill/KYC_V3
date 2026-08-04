import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import * as api from "./api";
import type { User } from "./types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      if (!api.isAuthenticated()) {
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        const currentUser = await api.fetchMe();
        setUser(currentUser);
      } catch {
        api.clearTokens();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    void initializeAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await api.login(email, password);
    api.setTokens(tokens.access, tokens.refresh);
    setUser(await api.fetchMe());
  }, []);

  const logout = useCallback(() => {
    api.clearTokens();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, logout }),
    [user, loading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
