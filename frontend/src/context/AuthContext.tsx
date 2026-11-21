import React, { createContext, useContext, useState, useEffect } from "react";

export type Role = "teacher" | "student" | "parent" | "admin";

export interface User {
  id: string;
  school_id: string;
  role: Role;
  name: string;
  email: string;
  language: "en" | "ta";
  is_active: boolean;
}

export const DEMO_CREDENTIALS: Record<Role, { email: string; pass: string; label: string; desc: string }> = {
  teacher: {
    email: "teacher@edupulse.demo",
    pass: "Demo@1234",
    label: "Ms. Priya (Teacher)",
    desc: "Class 9A · Early intervention & parent calls",
  },
  student: {
    email: "student@edupulse.demo",
    pass: "Demo@1234",
    label: "Karthik R (Student)",
    desc: "Missions, growth medals & cooperative Class Garden",
  },
  parent: {
    email: "parent@edupulse.demo",
    pass: "Demo@1234",
    label: "Karthik's Mother (Parent)",
    desc: "Weekly progress note & 5-minute call booking",
  },
  admin: {
    email: "admin@edupulse.demo",
    pass: "Demo@1234",
    label: "HM Ramanathan (Admin)",
    desc: "School-wide equity, fairness & demo reset control",
  },
};

interface AuthContextType {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<User>;
  quickLogin: (role: Role) => Promise<User>;
  logout: () => Promise<void>;
  resetDemo: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | null>(null);

const API_BASE =
  import.meta.env.VITE_API_URL ||
  (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
    ? `${window.location.origin}/api/v1`
    : "http://127.0.0.1:8000/api/v1");

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("edupulse_token"));
  const [refreshToken, setRefreshToken] = useState<string | null>(() => localStorage.getItem("edupulse_refresh_token"));
  const [user, setUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem("edupulse_user");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Validate token on initial load
  useEffect(() => {
    async function checkAuth() {
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const userData = await res.json();
          setUser(userData);
          localStorage.setItem("edupulse_user", JSON.stringify(userData));
        } else {
          // Token might be expired, try refreshing
          if (refreshToken) {
            const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });
            if (refreshRes.ok) {
              const refData = await refreshRes.json();
              setToken(refData.access_token);
              setRefreshToken(refData.refresh_token);
              localStorage.setItem("edupulse_token", refData.access_token);
              localStorage.setItem("edupulse_refresh_token", refData.refresh_token);
            } else {
              handleClearAuth();
            }
          } else {
            handleClearAuth();
          }
        }
      } catch {
        // Offline or backend unreachable, keep cached state for prototype demo
      } finally {
        setIsLoading(false);
      }
    }

    checkAuth();
  }, []);

  const handleClearAuth = () => {
    setToken(null);
    setRefreshToken(null);
    setUser(null);
    localStorage.removeItem("edupulse_token");
    localStorage.removeItem("edupulse_refresh_token");
    localStorage.removeItem("edupulse_user");
  };

  const login = async (email: string, pass: string): Promise<User> => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password: pass }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed. Please check your credentials.");
    }

    const data = await res.json();
    setToken(data.access_token);
    setRefreshToken(data.refresh_token);
    setUser(data.user);

    localStorage.setItem("edupulse_token", data.access_token);
    localStorage.setItem("edupulse_refresh_token", data.refresh_token);
    localStorage.setItem("edupulse_user", JSON.stringify(data.user));

    return data.user;
  };

  const quickLogin = async (role: Role): Promise<User> => {
    const creds = DEMO_CREDENTIALS[role];
    return await login(creds.email, creds.pass);
  };

  const logout = async () => {
    if (token) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch {
        // Ignore network failure on logout
      }
    }
    handleClearAuth();
  };

  const resetDemo = async (): Promise<boolean> => {
    try {
      // If user is currently admin, use their token; otherwise quick login as admin
      let authToken = token;
      if (!user || user.role !== "admin") {
        const adminRes = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: DEMO_CREDENTIALS.admin.email,
            password: DEMO_CREDENTIALS.admin.pass,
          }),
        });
        if (adminRes.ok) {
          const adminData = await adminRes.json();
          authToken = adminData.access_token;
        }
      }

      const res = await fetch(`${API_BASE}/demo/reset`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Demo reset failed");
      }
      return true;
    } catch (e) {
      console.error("Demo reset error:", e);
      throw e;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        refreshToken,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        quickLogin,
        logout,
        resetDemo,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
