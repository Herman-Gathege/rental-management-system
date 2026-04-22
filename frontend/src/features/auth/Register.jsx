//frontend/src/features/auth/Login.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
    organization_name: "",
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await register(form);
      alert("Account created. Please login.");
      navigate("/login");
    } catch {
      alert("Registration failed");
    }
  };

  return (
    <div className="auth-page">
      <form onSubmit={handleSubmit}>
        <h2 className="text-center">Create Account</h2>
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
          type="password"
          placeholder="Password"
          autoComplete="new-password"
          required
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />

        <button type="submit" className="btn btn-primary">
          Register
        </button>
      </form>
    </div>
  );
}
