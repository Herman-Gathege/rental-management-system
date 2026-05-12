import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getTenant, updateTenant } from "../../api/tenants";

export default function EditTenant() {
  const { tenantId } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", phone: "", email: "", id_number: "", emergency_contact: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await getTenant(tenantId);
        setForm({ full_name: data.full_name, phone: data.phone, email: data.email || "", id_number: data.id_number || "", emergency_contact: data.emergency_contact || "" });
      } catch (err) {
        setError("Failed to load tenant");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [tenantId]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async () => {
    setError("");
    setSubmitting(true);
    try {
      await updateTenant(tenantId, form);
      navigate("/owner/tenants");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <p>Loading...</p>;

  return (
    <section className="properties-page">
      <h2>Edit Tenant</h2>
      {error && <div className="error-text">{error}</div>}
      <div className="property-form card">
        <div className="form-group"><label>Full Name</label><input className="input" name="full_name" value={form.full_name} onChange={handleChange} /></div>
        <div className="form-group"><label>Phone</label><input className="input" name="phone" value={form.phone} onChange={handleChange} /></div>
        <div className="form-group"><label>Email</label><input className="input" name="email" type="email" value={form.email} onChange={handleChange} /></div>
        <div className="form-group"><label>ID Number</label><input className="input" name="id_number" value={form.id_number} onChange={handleChange} /></div>
        <div className="form-group"><label>Emergency Contact</label><input className="input" name="emergency_contact" value={form.emergency_contact} onChange={handleChange} /></div>
        <div className="flex gap-sm mt-md">
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>{submitting ? "Saving..." : "Save Changes"}</button>
          <button className="btn btn-secondary" onClick={() => navigate("/owner/tenants")}>Cancel</button>
        </div>
      </div>
    </section>
  );
}
