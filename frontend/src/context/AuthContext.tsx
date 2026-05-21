import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import axios from "axios";

const TOKEN_KEY = "quantumlogic_token";
const USER_KEY = "quantumlogic_user";
const JOB_KEY = "quantumlogic_active_job_id";

// One-time migration: clear stale keys from old FairHire branding
["fairhire_token", "fairhire_user", "fairhire_active_job_id"].forEach(
  (k) => localStorage.removeItem(k)
);

export interface AuthUser {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string, role?: string) => Promise<void>;
  googleLogin: (credential: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  /** Imperatively clear auth state — called by the 401 interceptor. */
  clearAuth: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function loadStored(): { user: AuthUser | null; token: string | null } {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const user = localStorage.getItem(USER_KEY);
    return { token, user: user ? JSON.parse(user) : null };
  } catch {
    return { token: null, user: null };
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const stored = loadStored();
  const [token, setToken] = useState<string | null>(stored.token);
  const [user, setUser] = useState<AuthUser | null>(stored.user);

  const clearAuth = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(JOB_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const persist = useCallback((tokenVal: string, userVal: AuthUser) => {
    // Clear stale job if switching to a different user
    const prevRaw = localStorage.getItem(USER_KEY);
    const prev = prevRaw ? JSON.parse(prevRaw) : null;
    if (prev?.user_id !== userVal.user_id) {
      localStorage.removeItem(JOB_KEY);
    }
    localStorage.setItem(TOKEN_KEY, tokenVal);
    localStorage.setItem(USER_KEY, JSON.stringify(userVal));
    setToken(tokenVal);
    setUser(userVal);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const { data } = await axios.post("/api/v1/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    persist(data.access_token, {
      user_id: data.user_id,
      email: data.email,
      full_name: data.full_name,
      role: data.role,
    });
  }, [persist]);

  const register = useCallback(async (
    email: string,
    password: string,
    full_name: string,
    role = "hr",
  ) => {
    const { data } = await axios.post("/api/v1/auth/register", { email, password, full_name, role });
    persist(data.access_token, {
      user_id: data.user_id,
      email: data.email,
      full_name: data.full_name,
      role: data.role,
    });
  }, [persist]);

  const googleLogin = useCallback(async (credential: string) => {
    const { data } = await axios.post("/api/v1/auth/google", { credential });
    persist(data.access_token, {
      user_id: data.user_id,
      email: data.email,
      full_name: data.full_name,
      role: data.role,
    });
  }, [persist]);

  const logout = clearAuth;

  // Global 401 interceptor — auto-logout on expired / invalid token
  useEffect(() => {
    const id = axios.interceptors.response.use(
      (res) => res,
      (err) => {
        if (axios.isAxiosError(err) && err.response?.status === 401) {
          clearAuth();
        }
        return Promise.reject(err);
      }
    );
    return () => axios.interceptors.response.eject(id);
  }, [clearAuth]);

  const value = useMemo(
    () => ({ user, token, login, register, googleLogin, logout, clearAuth, isAuthenticated: !!token }),
    [user, token, login, register, googleLogin, logout, clearAuth]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
