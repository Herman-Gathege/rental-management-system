//frontend/src/routes/ProtectedRoute.jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// `skipPhoneGate` is set on the /verify-phone route itself so the gate doesn't
// redirect it back onto itself (infinite loop). Everywhere else, an
// authenticated-but-unverified user is sent to /verify-phone.
export default function ProtectedRoute({ children, allowedRoles, skipPhoneGate = false }) {
  const { user, loading } = useAuth();

  if (loading) return <p>Loading...</p>;

  if (!user) return <Navigate to="/login" />;

  // ⭐ Sprint 6.2 #6: phone-verification gate. Until phone_verified is true,
  // hold the user on the verification screen regardless of role.
  if (!skipPhoneGate && user.phone_verified === false) {
    return <Navigate to="/verify-phone" />;
  }

  // ⭐ role-based protection
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" />; // redirect to decision layer
  }

  return children;
}
