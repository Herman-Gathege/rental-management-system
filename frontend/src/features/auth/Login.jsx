//frontend/src/features/auth/Login.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import SEO from "../../components/SEO";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(form.email, form.password);
      navigate("/dashboard"); // ⭐ single entry point
    } catch {
      alert("Login failed");
    }
  };

  return (
    <>
      <SEO
        title="Login — AlphaOne Rental Property Management"
        description="Sign in to your AlphaOne account to manage rental properties, track rent, and streamline tenant operations across Kenya and East Africa."
        canonical="https://alphaone.africa/login"
      />
      <div className="auth-page">
      <form className="auth-card card form-stack" onSubmit={handleSubmit}>
        <h2 className="text-center">Login</h2>

        <input
          type="email"
          placeholder="Email"
          required
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          className="input"
          autoComplete="email"
        />

        <input
          type="password"
          placeholder="Password"
          required
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          className="input"
          autoComplete="current-password"
        />

        <button className="btn btn-primary" type="submit">
          Login
        </button>
      </form>
    </div>
    </>
  );
}
