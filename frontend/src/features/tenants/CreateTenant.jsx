//frontend\src\features\tenants\CreateTenant.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createTenant } from "../../api/tenants";

export default function CreateTenant() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    phone: "",
    email: "",
    id_number: "",
    emergency_contact: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await createTenant(form);
      navigate("/owner/tenants");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create tenant");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="properties-page">
      <h2>Add New Tenant</h2>
      {error && <div className="error-text">{error}</div>}

      <div className="property-form card">
        <div className="form-group">
          <label htmlFor="full_name">Full Name</label>
          <input id="full_name" name="full_name" className="input" placeholder="e.g. John Kamau" value={form.full_name} onChange={handleChange} required />
        </div>

        <div className="form-group">
          <label htmlFor="phone">Phone Number</label>
          <input id="phone" name="phone" className="input" placeholder="e.g. 0712345678" value={form.phone} onChange={handleChange} required />
        </div>

        <div className="form-group">
          <label htmlFor="email">Email (optional)</label>
          <input id="email" name="email" className="input" type="email" placeholder="e.g. john@email.com" value={form.email} onChange={handleChange} />
        </div>

        <div className="form-group">
          <label htmlFor="id_number">National ID Number (optional)</label>
          <input id="id_number" name="id_number" className="input" placeholder="e.g. 12345678" value={form.id_number} onChange={handleChange} />
        </div>

        <div className="form-group">
          <label htmlFor="emergency_contact">Emergency Contact (optional)</label>
          <input id="emergency_contact" name="emergency_contact" className="input" placeholder="e.g. Jane Kamau - 0798765432" value={form.emergency_contact} onChange={handleChange} />
        </div>

        <div className="flex gap-sm mt-md">
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting || !form.full_name || !form.phone}>
            {submitting ? "Creating..." : "Add Tenant"}
          </button>
          <button className="btn btn-secondary" onClick={() => navigate("/owner/tenants")} type="button">Cancel</button>
        </div>
      </div>
    </section>
  );
}

