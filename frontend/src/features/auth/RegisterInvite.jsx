//frontend\src\features\auth\RegisterInvite.jsx
//
// Invite acceptance for tenant / property_manager / finance roles. Mirrors
// the landlord Register.jsx password UX so anyone joining via invite sees
// the same live strength gauge and requirements checklist.
//
// Sprint 7 cleanup:
//   - Fetches invitation details (email, role, org name) from a public
//     GET endpoint using the token, so the strength gauge can run the
//     "doesn't contain your email" check against the invitee's real
//     email and the page can show which org they're joining.
//   - Adds the PasswordStrength component (copied from Register.jsx so
//     the two flows stay in sync visually).

import { useState, useMemo, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import API from "../../api/client";
import { checkPasswordStrength } from "../../utils/passwordStrength";

export default function RegisterInvite() {
  const { token } = useParams();
  const navigate = useNavigate();

  const [invitation, setInvitation] = useState(null);
  const [loadingInvite, setLoadingInvite] = useState(true);
  const [inviteError, setInviteError] = useState("");

  const [form, setForm] = useState({ password: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Fetch invitation details on mount. We need the email for the password
  // strength check and the org / role labels for display.
  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await API.get(
          `/organizations/invitations/by-token/${token}`
        );
        setInvitation(data);
      } catch (err) {
        setInviteError(
          err?.response?.data?.detail || "Invalid or expired invitation"
        );
      } finally {
        setLoadingInvite(false);
      }
    };
    load();
  }, [token]);

  // Live password checks — same shape as landlord Register.jsx. The email
  // rule needs invitation.email; falls back to empty string until the
  // invite loads (rule just always passes in that window — the backend
  // still enforces on submit).
  const pw = useMemo(
    () => checkPasswordStrength(form.password, invitation?.email || ""),
    [form.password, invitation?.email]
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
      const { data } = await API.post(
        `/organizations/register-invite/${token}`,
        form
      );

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("role", data.role);

      switch (data.role) {
        case "LANDLORD":
          navigate("/owner/dashboard");
          break;
        case "PROPERTY_MANAGER":
          navigate("/manager/dashboard");
          break;
        case "FINANCE":
          navigate("/finance");
          break;
        case "TENANT":
          navigate("/tenant");
          break;
        default:
          navigate("/dashboard");
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingInvite) {
    return (
      <div className="auth-page">
        <div className="auth-card card form-stack">
          <p className="text-center text-muted">Loading invitation…</p>
        </div>
      </div>
    );
  }

  if (inviteError) {
    return (
      <div className="auth-page">
        <div className="auth-card card form-stack">
          <h2 className="text-center">Invitation not valid</h2>
          <p className="error-text text-center">{inviteError}</p>
        </div>
      </div>
    );
  }

  const roleLabel = (invitation.role || "").replace(/_/g, " ").toLowerCase();

  return (
    <div className="auth-page">
      <form className="auth-card card form-stack" onSubmit={handleSubmit}>
        <div className="text-center mb-md">
          <h2 className="mb-sm">Join {invitation.organization_name}</h2>
          <p className="text-muted text-sm">
            Setting up <strong>{invitation.email}</strong>
            {roleLabel ? <> · Role: <strong>{roleLabel}</strong></> : null}
          </p>
        </div>

        {error && <div className="error-text">{error}</div>}

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
          className="btn btn-primary w-full"
          disabled={submitting || !pw.allPassed}
        >
          {submitting ? "Creating account…" : "Create Account"}
        </button>
      </form>
    </div>
  );
}


/* ─── Password strength gauge (mirrors Register.jsx) ─── */

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
