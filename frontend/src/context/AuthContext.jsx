//frontend/src/context/AuthContext.jsx
import { createContext, useContext, useEffect, useState } from "react";
import { loginUser, registerUser, getMe } from "../api/auth";
import { getMyOrganization } from "../api/organizations";

const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);

  /* Restore session on page refresh */
  useEffect(() => {
    const init = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) throw new Error();

        const me = await getMe();
        setUser(me);

        // Fetch organization data
        try {
          const orgData = await getMyOrganization();
          setOrganization(orgData.organization);
        } catch {
          // User may not have an org yet
          setOrganization(null);
        }
      } catch {
        logout();
      } finally {
        setLoading(false);
      }
    };

    init();
  }, []);

  /* LOGIN */
  const login = async (email, password) => {
    const data = await loginUser(email, password);

    if (!data?.access_token) {
      throw new Error("Invalid login response");
    }

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);

    const me = await getMe();

    if (!me) throw new Error("Failed to fetch user");
    setUser(me);

    // Fetch organization after login
    try {
      const orgData = await getMyOrganization();
      setOrganization(orgData.organization);
    } catch {
      setOrganization(null);
    }

    return me;
  };

  /* REGISTER */
  const register = async (payload) => {
    await registerUser(payload);
  };

  /* LOGOUT */
  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("active_property_id");
    setUser(null);
    setOrganization(null);
  };

  return (
    <AuthContext.Provider value={{ user, organization, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
