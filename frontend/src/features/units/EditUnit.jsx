import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getUnit, updateUnit } from "../../api/units";

export default function EditUnit() {
  const { unitId } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", description: "", bedrooms: "", bathrooms: "", size_sqm: "", rent_amount: "", is_active: true });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await getUnit(unitId);
        setForm({ name: data.name, description: data.description || "", bedrooms: data.bedrooms || "", bathrooms: data.bathrooms || "", size_sqm: data.size_sqm || "", rent_amount: data.rent_amount, is_active: data.is_active });
      } catch (err) {
        setError("Failed to load unit");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [unitId]);

  const handleChange = (e) => {
    const val = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm({ ...form, [e.target.name]: val });
  };

  const handleSubmit = async () => {
    setError("");
    setSubmitting(true);
    try {
      const payload = {
        name: form.name,
        description: form.description || null,
        bedrooms: form.bedrooms ? parseInt(form.bedrooms) : null,
        bathrooms: form.bathrooms ? parseInt(form.bathrooms) : null,
        size_sqm: form.size_sqm ? parseFloat(form.size_sqm) : null,
        rent_amount: parseFloat(form.rent_amount),
        is_active: form.is_active,
      };
      await updateUnit(unitId, payload);
      navigate("/owner/units");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <p>Loading...</p>;

  return (
    <section className="properties-page">
      <h2>Edit Unit</h2>
      {error && <div className="error-text">{error}</div>}
      <div className="property-form card">
        <div className="form-group"><label>Unit Name</label><input className="input" name="name" value={form.name} onChange={handleChange} /></div>
        <div className="form-group"><label>Monthly Rent (KES)</label><input className="input" name="rent_amount" type="number" value={form.rent_amount} onChange={handleChange} /></div>
        <div className="form-group"><label>Description</label><input className="input" name="description" value={form.description} onChange={handleChange} /></div>
        <div className="two-col">
          <div className="form-group"><label>Bedrooms</label><input className="input" name="bedrooms" type="number" value={form.bedrooms} onChange={handleChange} /></div>
          <div className="form-group"><label>Bathrooms</label><input className="input" name="bathrooms" type="number" value={form.bathrooms} onChange={handleChange} /></div>
        </div>
        <div className="form-group"><label>Size (sqm)</label><input className="input" name="size_sqm" type="number" step="0.1" value={form.size_sqm} onChange={handleChange} /></div>
        <div className="form-group"><label><input type="checkbox" name="is_active" checked={form.is_active} onChange={handleChange} /> Active</label></div>
        <div className="flex gap-sm mt-md">
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>{submitting ? "Saving..." : "Save Changes"}</button>
          <button className="btn btn-secondary" onClick={() => navigate("/owner/units")}>Cancel</button>
        </div>
      </div>
    </section>
  );
}
