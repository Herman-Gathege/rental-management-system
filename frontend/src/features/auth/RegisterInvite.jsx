import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import API from "../../api/client";

export default function RegisterInvite() {
  const { token } = useParams();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    password: "",
  });

  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const { data } = await API.post(
        `/organizations/register-invite/${token}`,
        form
      );

      localStorage.setItem(
        "access_token",
        data.access_token
      ); 

      localStorage.setItem("role", data.role);

      alert("Account created & joined organization!");

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
      alert(err?.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card card form-stack" onSubmit={handleSubmit}>
        <div className="text-center mb-md">
          <h2 className="mb-sm">Joining Organization</h2>
          <p className="text-muted text-sm">
            Complete your account setup
          </p>
        </div>

        {/* <input
          className="input"
          type="email"
          placeholder="Email Address"
          required
          onChange={(e) =>
            setForm({ ...form, email: e.target.value })
          }
        /> */}

        <input
          className="input"
          type="password"
          placeholder="Password"
          required
          onChange={(e) =>
            setForm({ ...form, password: e.target.value })
          }
        />

        <button className="btn btn-primary w-full" disabled={loading}>
          {loading ? "Creating Account..." : "Create Account"}
        </button>
      </form>
    </div>
  );
}