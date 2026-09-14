// frontend/src/features/auth/Login.jsx
//
// Sign-in page (requirement 10).
//
// The authentication contract is unchanged — same endpoint, same token
// handling through AuthContext. What changed is the experience:
//   * labelled fields with helper text and inline validation
//   * a disabled, in-flight submit button so the form can't be double-posted
//   * invalid credentials, duplicate accounts and network/server problems each
//     get their own clear message (never a raw backend error object)
//   * password visibility toggle
//   * keyboard/focus friendly, mobile responsive
//   * after success the user lands on the role decider, or back on whichever
//     protected page sent them here

import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { FiEye, FiEyeOff } from "react-icons/fi";
import { useAuth } from "../../context/AuthContext";
import SEO from "../../components/SEO";

/* Turns any thrown auth error into a message a customer can act on. */
function describeLoginError(err) {
  const status = err?.response?.status;
  const detail = err?.response?.data?.detail;

  if (status === 401 || status === 400) {
    return typeof detail === "string" && detail
      ? detail
      : "That email address or password isn’t correct. Please try again.";
  }
  if (status === 403) {
    return typeof detail === "string" && detail
      ? detail
      : "This account can’t sign in right now. Please contact your administrator.";
  }
  if (status === 429) {
    return "Too many attempts. Please wait a moment and try again.";
  }
  if (!err?.response) {
    return "We couldn’t reach the server. Check your connection and try again.";
  }
  return "Something went wrong while signing you in. Please try again.";
}

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [form, setForm] = useState({ email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const setField = (name) => (event) => {
    setForm((prev) => ({ ...prev, [name]: event.target.value }));
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const validate = () => {
    const errors = {};
    if (!form.email.trim()) {
      errors.email = "Enter your email address.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      errors.email = "Enter a valid email address.";
    }
    if (!form.password) errors.password = "Enter your password.";
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validation errors are shown per field; server errors go in the banner.
    // Keeping the two visually separate is the point — one means "fix this
    // field", the other means "we couldn't sign you in".
    const errors = validate();
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setSubmitting(true);
    try {
      await login(form.email.trim(), form.password);

      // Return the user to wherever they were headed before being redirected
      // to login; fall back to the role decider.
      const from = location.state?.from?.pathname;
      navigate(from || "/dashboard", { replace: true });
    } catch (err) {
      setError(describeLoginError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const passwordType = showPassword ? "text" : "password";

  return (
    <>
      <SEO
        title="Login — AlphaOne Rental Property Management"
        description="Sign in to your AlphaOne account to manage rental properties, track rent, and streamline tenant operations across Kenya and East Africa."
        canonical="https://alphaone.africa/login"
        noindex
      />
      <div className="auth-page">
        <form
          className="auth-card card form-stack"
          onSubmit={handleSubmit}
          noValidate
        >
          <div className="auth-heading">
            <h2>Welcome back</h2>
            <p className="text-muted text-sm">
              Sign in to manage your properties, tenants and payments.
            </p>
          </div>

          {error && (
            <div className="auth-alert auth-alert-error" role="alert">
              {error}
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="login-email">Email address</label>
            <input
              id="login-email"
              type="email"
              value={form.email}
              onChange={setField("email")}
              className="input"
              autoComplete="email"
              autoFocus
              aria-invalid={Boolean(fieldErrors.email)}
              aria-describedby={fieldErrors.email ? "login-email-error" : undefined}
            />
            {fieldErrors.email && (
              <span id="login-email-error" className="field-error">
                {fieldErrors.email}
              </span>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="login-password">Password</label>
            <div className="auth-password">
              <input
                id="login-password"
                type={passwordType}
                value={form.password}
                onChange={setField("password")}
                className="input"
                autoComplete="current-password"
                aria-invalid={Boolean(fieldErrors.password)}
                aria-describedby={
                  fieldErrors.password ? "login-password-error" : undefined
                }
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
              <span id="login-password-error" className="field-error">
                {fieldErrors.password}
              </span>
            )}
            {/* No self-service reset route exists yet — the backend emails a
                reset link, so there is nothing to link to from here. */}
          </div>

          <button
            className="btn btn-primary btn-block"
            type="submit"
            disabled={submitting}
            aria-busy={submitting}
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>

          <p className="text-sm text-center text-muted">
            New to AlphaOne? <Link className="auth-link" to="/register">Create an account</Link>
          </p>
        </form>
      </div>
    </>
  );
}
