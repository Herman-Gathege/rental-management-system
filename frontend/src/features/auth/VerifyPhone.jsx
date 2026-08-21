//frontend/src/features/auth/VerifyPhone.jsx
//
// Phone verification screen (Sprint 6.2 #6). Shown to a signed-in but
// unverified landlord. ProtectedRoute routes here whenever user.phone_verified
// is false; on success we refresh the user (flag flips true) and send them on
// to the dashboard.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { verifyOtp, resendOtp } from "../../api/auth";
import { getMe } from "../../api/auth";
import SEO from "../../components/SEO";

const RESEND_SECONDS = 60;

export default function VerifyPhone() {
  const { user, setUser, logout } = useAuth();
  const navigate = useNavigate();

  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [cooldown, setCooldown] = useState(RESEND_SECONDS);

  // If somehow already verified, don't sit on this screen.
  useEffect(() => {
    if (user && user.phone_verified) {
      navigate("/dashboard");
    }
  }, [user, navigate]);

  // Resend cooldown ticker.
  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setInterval(() => setCooldown((c) => (c > 0 ? c - 1 : 0)), 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  const handleVerify = async (e) => {
    e.preventDefault();
    setError("");
    setInfo("");
    setSubmitting(true);
    try {
      await verifyOtp(code.trim());
      // Refresh the user so phone_verified flips to true, then proceed.
      const me = await getMe();
      setUser(me);
      navigate("/dashboard");
    } catch (err) {
      setError(err?.response?.data?.detail || "Verification failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleResend = async () => {
    setError("");
    setInfo("");
    try {
      await resendOtp();
      setInfo("A new code has been sent.");
      setCooldown(RESEND_SECONDS);
    } catch (err) {
      // Backend returns 429 with a "wait N seconds" message when throttled.
      setError(err?.response?.data?.detail || "Could not resend the code.");
    }
  };

  const masked = user?.phone
    ? user.phone.replace(/.(?=.{3})/g, "•")
    : "your phone";

  return (
    <>
      <SEO
        title="Verify Phone — AlphaOne Rental Property Management"
        description="Verify your phone number to complete your AlphaOne account setup. Manage rental properties and tenant operations across Kenya and East Africa."
        canonical="https://alphaone.africa/verify-phone"
        noindex
      />
      <div className="auth-page">
      <form className="auth-card card form-stack" onSubmit={handleVerify}>
        <h2 className="text-center">Verify your phone</h2>
        <p className="text-center text-muted text-sm">
          We sent a 6-digit code on WhatsApp to {masked}. Enter it below to
          finish setting up your account.
        </p>

        {error && <div className="error-text">{error}</div>}
        {info && <div className="success-banner">{info}</div>}

        <input
          className="input"
          type="text"
          inputMode="numeric"
          maxLength={6}
          placeholder="Enter 6-digit code"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          required
        />

        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting || code.length !== 6}
        >
          {submitting ? "Verifying…" : "Verify"}
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleResend}
          disabled={cooldown > 0}
        >
          {cooldown > 0 ? `Resend code (${cooldown}s)` : "Resend code"}
        </button>

        <button
          type="button"
          className="btn btn-link text-sm"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          Sign out
        </button>
      </form>
    </div>
    </>
  );
}
