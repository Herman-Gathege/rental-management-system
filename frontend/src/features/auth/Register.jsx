//frontend/src/features/auth/Register.jsx
import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { checkPasswordStrength } from "../../utils/passwordStrength";
import SEO from "../../components/SEO";

export default function Register() {
  const { register, login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
    organization_name: "",
    phone: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Live password checks. Purely a UX aid — the backend enforces the same
  // rules and rejects on submit if anything's off.
  const pw = useMemo(
    () => checkPasswordStrength(form.password, form.email),
    [form.password, form.email]
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!pw.allPassed) {
      setError("Please meet the password requirements below.");
      return;
    }

    setSubmitting(true);
    try {
      // Create the account (backend sends a WhatsApp OTP to the phone).
      await register(form);
      // Log in immediately so we hold a token, then route to verification.
      // The account is unverified (phone_verified=false) until the OTP is
      // confirmed; ProtectedRoute keeps them on /verify-phone until then.
      await login(form.email, form.password);
      navigate("/verify-phone");
    } catch (err) {
      setError(err?.response?.data?.detail || "Registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <SEO
        title="Create Account — AlphaOne Rental Property Management Kenya"
        description="Join AlphaOne and start managing your rental properties in Kenya and East Africa. Sign up for free to track rent, manage tenants, and streamline property operations."
        canonical="https://alphaone.africa/register"
        noindex
      />
      <div className="auth-page">
      <form className="auth-card card form-stack" onSubmit={handleSubmit}>
        <h2 className="text-center">Create Account</h2>

        {error && <div className="error-text">{error}</div>}

        <input
          className="input"
          placeholder="Organization Name"
          required
          onChange={(e) =>
            setForm({ ...form, organization_name: e.target.value })
          }
        />

        <input
          className="input"
          type="email"
          placeholder="Email"
          required
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />

        <input
          className="input"
          type="tel"
          placeholder="Phone (e.g. 2547XXXXXXXX)"
          required
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
        />
        <p className="text-sm text-muted" style={{ marginTop: "-0.25rem" }}>
          We'll send a verification code to this number on WhatsApp.
        </p>

        <input
          className="input"
          type="password"
          placeholder="Password"
          autoComplete="new-password"
          required
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />

        {/* Password strength gauge — only shows once the user starts typing. */}
        {form.password && <PasswordStrength pw={pw} />}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting || !pw.allPassed}
        >
          {submitting ? "Creating account…" : "Register"}
        </button>
      </form>
    </div>
    </>
  );
}


/* ─── Password strength gauge ─── */

function PasswordStrength({ pw }) {
  const barColor =
    pw.score >= 4 ? "#16a34a" : pw.score >= 3 ? "#f59e0b" : "#ef4444";
  const barWidth = `${(pw.score / 5) * 100}%`;

  return (
    <div style={{ marginTop: "-0.25rem" }}>
      <div
        style={{
          height: "6px",
          background: "#e5e7eb",
          borderRadius: "3px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: barWidth,
            background: barColor,
            transition: "width 0.2s ease, background 0.2s ease",
          }}
        />
      </div>
      <ul
        style={{
          listStyle: "none",
          padding: 0,
          margin: "0.5rem 0 0 0",
          fontSize: "0.8125rem",
          lineHeight: 1.5,
        }}
      >
        <Check ok={pw.checks.length}>At least 10 characters</Check>
        <Check ok={pw.checks.classes}>
          3 of: uppercase, lowercase, digit, symbol
        </Check>
        <Check ok={pw.checks.notCommon}>Not a common password</Check>
        <Check ok={pw.checks.notEmail}>Doesn't contain your email</Check>
      </ul>
    </div>
  );
}

function Check({ ok, children }) {
  return (
    <li style={{ color: ok ? "#16a34a" : "#6b7280" }}>
      {ok ? "✓" : "○"} {children}
    </li>
  );
}
