import { useEffect, useState } from "react";
import {
  useNavigate,
  useParams,
  Link,
} from "react-router-dom";

import { acceptInvitation } from "../../api/organizations";
import SEO from "../../components/SEO";

export default function AcceptInvitation() {
  const { token } = useParams();

  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);

  const [success, setSuccess] = useState(false);

  const [message, setMessage] = useState("");

  const [role, setRole] = useState("");

  useEffect(() => {
    handleAccept();
  }, []);

  const handleAccept = async () => {
    try {
      const data = await acceptInvitation(token);

      if (data.requires_registration) {
        navigate(`/register-invite/${token}`);
        return;
      }

      setSuccess(true);
      setMessage(data.message);
      setRole(data.role);

      setTimeout(() => {
        navigate("/dashboard");
      }, 2500);

    } catch (err) {
      setSuccess(false);

      setMessage(
        err?.response?.data?.detail ||
          "Failed to accept invitation."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <SEO
        title="Accept Invitation — AlphaOne Rental Property Management"
        description="Accept your invitation to join an AlphaOne organization. Manage rental properties, tenants, and operations across Kenya and East Africa."
        canonical="https://alphaone.africa/accept-invite"
        noindex
      />
      <div className="auth-page">
      <div className="auth-card card text-center form-stack">
        {loading ? (
          <>
            <h2>Accepting Invitation...</h2>

            <p className="text-muted">
              Please wait while we verify your invite.
            </p>
          </>
        ) : success ? (
          <>
            <h2 className="text-success">
              🎉 Invitation Accepted
            </h2>

            <p className="text-muted">
              {message}
            </p>

            <div className="card-w">
              <p className="text-sm text-muted">
                Assigned Role
              </p>

              <h3 className="mt-sm">
                {role}
              </h3>
            </div>

            <p className="text-sm text-muted">
              Redirecting to dashboard...
            </p>
          </>
        ) : (
          <>
            <h2 className="text-error">
              ❌ Invitation Failed
            </h2>

            <p className="text-muted">
              {message}
            </p>

            <Link
              to={`/register-invite/${token}`}
              className="btn btn-primary w-full"
            >
              Create Account to Join
            </Link>

            <div className="mt-sm">
              <p className="text-sm text-muted">
                Already have an account?
              </p>

              <Link
                to="/login"
                className="text-sm"
              >
                Login
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
    </>
  );
}