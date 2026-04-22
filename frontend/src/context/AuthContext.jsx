//frontend/src/context/AuthContext.jsx
import { createContext, useContext, useEffect, useState } from "react";
import { loginUser, registerUser, getMe } from "../api/auth";


const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children  }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  /* Restore session on page refresh */
  useEffect(() => {
    const init = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) throw new Error();

        const me = await getMe();
        setUser(me);
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

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);

    const me = await getMe();
    setUser(me);
  };

  /* REGISTER */
  const register = async (payload) => {
    await registerUser(payload);
  };

  /* LOGOUT */
  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}