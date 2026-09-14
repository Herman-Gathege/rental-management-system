//frontend/src/features/auth/Register.jsx
import { useState, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FiEye, FiEyeOff } from "react-icons/fi";
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
  const [fieldErrors, setFieldErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [confirmPassword, setConfirmPassword] = useState("");

  // Live password checks. Purely a UX aid — the backend enforces the same
  // rules and rejects on submit if anything's off.
  const pw = useMemo(
    () => checkPasswordStrength(form.password, form.email),
    [form.password, form.email]
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Inline validation first (distinct from server errors, which go in the
    // banner below). The backend enforces all of this again.
    const errors = {};
    if (!form.organization_name.trim()) {
      errors.organization_name = "Enter your organisation or portfolio name.";
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      errors.email = "Enter a valid email address.";
    }
    const phoneDigits = form.phone.replace(/[^\d]/g, "");
    const normalisedPhone =
      phoneDigits.startsWith("0") && phoneDigits.length === 10
        ? `254${phoneDigits.slice(1)}`
        : phoneDigits;
    if (!/^254\d{9}$/.test(normalisedPhone)) {
      errors.phone = "Enter a valid phone number, e.g. 254712345678.";
    }
    if (!pw.allPassed) {
      errors.password = "Please meet all the password requirements.";
    }
    if (confirmPassword && confirmPassword !== form.password) {
      errors.confirmPassword = "Passwords don’t match.";
    }
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setError("");
      return;
    }

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
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      if (status === 400 || status === 409) {
        setError(
          typeof detail === "string" && detail
            ? detail
            : "We couldn’t create this account. That email or phone number may already be registered.",
        );
      } else if (status === 429) {
        setError("Too many attempts. Please wait a moment and try again.");
      } else if (!err?.response) {
        setError(
          "We couldn’t reach the server. Check your connection and try again.",
        );
      } else {
        setError("Registration failed. Please try again in a moment.");
      }
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
      <form className="auth-card card form-stack" onSubmit={handleSubmit} noValidate>
        <div className="auth-heading">
          <h2>Create your account</h2>
          <p className="text-muted text-sm">
            Set up your portfolio in a couple of minutes. We’ll verify your
            phone number on WhatsApp.
          </p>
        </div>

        {error && (
          <div className="auth-alert auth-alert-error" role="alert">
            {error}
          </div>
        )}

        <div className="auth-field">
          <label htmlFor="register-org">Organisation name</label>
          <input
            id="register-org"
            className="input"
            value={form.organization_name}
            placeholder="e.g. Sirali Properties"
            autoComplete="organization"
            aria-invalid={Boolean(fieldErrors.organization_name)}
            onChange={(e) => {
              setForm({ ...form, organization_name: e.target.value });
              setFieldErrors((prev) => ({ ...prev, organization_name: undefined }));
            }}
          />
          {fieldErrors.organization_name && (
            <span className="field-error">{fieldErrors.organization_name}</span>
          )}
          <small>This is the portfolio name your team will see.</small>
        </div>

        <div className="auth-field">
          <label htmlFor="register-email">Email address</label>
          <input
            id="register-email"
            className="input"
            type="email"
            value={form.email}
            autoComplete="email"
            aria-invalid={Boolean(fieldErrors.email)}
            onChange={(e) => {
              setForm({ ...form, email: e.target.value });
              setFieldErrors((prev) => ({ ...prev, email: undefined }));
            }}
          />
          {fieldErrors.email && (
            <span className="field-error">{fieldErrors.email}</span>
          )}
          <small>You’ll use this address to sign in.</small>
        </div>

        <div className="auth-field">
          <label htmlFor="register-phone">Phone number</label>
          <input
            id="register-phone"
            className="input"
            type="tel"
            value={form.phone}
            placeholder="254712345678"
            autoComplete="tel"
            aria-invalid={Boolean(fieldErrors.phone)}
            onChange={(e) => {
              setForm({ ...form, phone: e.target.value });
              setFieldErrors((prev) => ({ ...prev, phone: undefined }));
            }}
          />
          {fieldErrors.phone && (
            <span className="field-error">{fieldErrors.phone}</span>
          )}
          <small>We’ll send a verification code to this number on WhatsApp.</small>
        </div>

        <div className="auth-field">
          <label htmlFor="register-password">Password</label>
          <div className="auth-password">
            <input
              id="register-password"
              className="input"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              value={form.password}
              aria-invalid={Boolean(fieldErrors.password)}
              onChange={(e) => {
                setForm({ ...form, password: e.target.value });
                setFieldErrors((prev) => ({ ...prev, password: undefined }));
              }}
            />
            <button
              type="button"
              className="auth-password-toggle"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              aria-pressed={showPassword}
            >
              {showPassword ? <FiEyeOff /> : <FiEye />}
            </button>
          </div>
          {fieldErrors.password && (
            <span className="field-error">{fieldErrors.password}</span>
          )}
        </div>

        {/* Password strength gauge — only shows once the user starts typing. */}
        {form.password && <PasswordStrength pw={pw} />}

        <div className="auth-field">
          <label htmlFor="register-confirm">Confirm password</label>
          <input
            id="register-confirm"
            className="input"
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            aria-invalid={Boolean(fieldErrors.confirmPassword)}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              setFieldErrors((prev) => ({ ...prev, confirmPassword: undefined }));
            }}
          />
          {fieldErrors.confirmPassword && (
            <span className="field-error">{fieldErrors.confirmPassword}</span>
          )}
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-block"
          disabled={submitting || !pw.allPassed}
          aria-busy={submitting}
        >
          {submitting ? "Creating account…" : "Create account"}
        </button>

        <p className="text-sm text-center text-muted">
          Already have an account?{" "}
          <Link className="auth-link" to="/login">Sign in</Link>
        </p>
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
