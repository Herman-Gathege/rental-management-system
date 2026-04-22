// frontend/src/features/dashboard/Dashboard.jsx

import { Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function Dashboard() {
  const { user, loading } = useAuth();

  // While auth state is resolving
  if (loading) return null;

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Role-based decision
  if (user.role === "owner") {
    return <Navigate to="/owner/dashboard" replace />;
  }

  if (user.role === "staff") {
    return <Navigate to="/staff/dashboard" replace />;
  }

  // Fallback (should never happen)
  return <Navigate to="/login" replace />;
}
