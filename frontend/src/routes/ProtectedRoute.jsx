//frontend/src/routes/ProtectedRoute.jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import SEO from "../components/SEO";

// `skipPhoneGate` is set on the /verify-phone route itself so the gate doesn't
// redirect it back onto itself (infinite loop). Everywhere else, an
// authenticated-but-unverified LANDLORD is sent to /verify-phone.
export default function ProtectedRoute({ children, allowedRoles, skipPhoneGate = false }) {
  const { user, loading } = useAuth();

  if (loading) return <p>Loading...</p>;

  if (!user) return <Navigate to="/login" />;

  // ⭐ Sprint 6.2 #6: phone-verification gate. LANDLORD only — that's the
  // role that goes through the /auth/register flow with a phone captured on
  // the users table and a WhatsApp OTP sent as part of signup. Tenants /
  // property managers / finance staff are INVITED by a landlord (their user
  // row has no phone; the tenant's phone lives on the tenants table instead),
  // so gating them here traps them on a verify screen whose resend endpoint
  // has no phone to send to. Skipping the gate for non-landlords matches the
  // original Sprint 6.2 #6 scope: "phone verification at landlord signup".
  if (
    !skipPhoneGate &&
    user.role === "LANDLORD" &&
    user.phone_verified === false
  ) {
    return <Navigate to="/verify-phone" />;
  }

  // ⭐ role-based protection
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" />; // redirect to decision layer
  }

  return (
    <SEO noindex>
      {children}
    </SEO>
  );
}
