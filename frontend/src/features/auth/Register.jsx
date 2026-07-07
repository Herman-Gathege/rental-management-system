//frontend/src/features/auth/Register.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
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
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Creating account…" : "Register"}
        </button>
      </form>
    </div>
  );
}
