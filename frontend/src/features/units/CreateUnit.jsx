//frontend\src\features\units\CreateUnit.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createUnit } from "../../api/units";
import { getProperties } from "../../api/properties";
import { useProperty } from "../../context/PropertyContext";

export default function CreateUnit() {
  const navigate = useNavigate();
  const { activeProperty } = useProperty();
  const [properties, setProperties] = useState([]);

  const [form, setForm] = useState({
    property_id: activeProperty?.id || "",
    name: "",
    description: "",
    bedrooms: "",
    bathrooms: "",
    size_sqm: "",
    rent_amount: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await getProperties();
        setProperties(data);
      } catch (err) {
        console.error(err);
      }
    };
    fetch();
  }, []);

  useEffect(() => {
    if (activeProperty?.id) {
      setForm((prev) => ({ ...prev, property_id: activeProperty.id }));
    }
  }, [activeProperty]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const payload = {
        ...form,
        bedrooms: form.bedrooms ? parseInt(form.bedrooms) : null,
        bathrooms: form.bathrooms ? parseInt(form.bathrooms) : null,
        size_sqm: form.size_sqm ? parseFloat(form.size_sqm) : null,
        rent_amount: parseFloat(form.rent_amount),
      };
      await createUnit(payload);
      navigate("/owner/units");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create unit");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="properties-page">
      <h2>Add New Unit</h2>
      {error && <div className="error-text">{error}</div>}

      <div className="property-form card">
        <div className="form-group">
          <label htmlFor="property_id">Property</label>
          <select
            id="property_id"
            name="property_id"
            className="input"
            value={form.property_id}
            onChange={handleChange}
            required
          >
            <option value="">Select property...</option>
            {properties.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="name">Unit Name</label>
          <input id="name" name="name" className="input" placeholder="e.g. Apartment 1A" value={form.name} onChange={handleChange} required />
        </div>

        <div className="form-group">
          <label htmlFor="rent_amount">Monthly Rent (KES)</label>
          <input id="rent_amount" name="rent_amount" className="input" type="number" placeholder="e.g. 25000" value={form.rent_amount} onChange={handleChange} required />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description (optional)</label>
          <input id="description" name="description" className="input" placeholder="e.g. Ground floor, parking included" value={form.description} onChange={handleChange} />
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="bedrooms">Bedrooms</label>
            <input id="bedrooms" name="bedrooms" className="input" type="number" value={form.bedrooms} onChange={handleChange} />
          </div>
          <div className="form-group">
            <label htmlFor="bathrooms">Bathrooms</label>
            <input id="bathrooms" name="bathrooms" className="input" type="number" value={form.bathrooms} onChange={handleChange} />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="size_sqm">Size (sqm)</label>
          <input id="size_sqm" name="size_sqm" className="input" type="number" step="0.1" value={form.size_sqm} onChange={handleChange} />
        </div>

        <div className="flex gap-sm mt-md">
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting || !form.name || !form.rent_amount || !form.property_id}>
            {submitting ? "Creating..." : "Create Unit"}
          </button>
          <button className="btn btn-secondary" onClick={() => navigate("/owner/units")} type="button">Cancel</button>
        </div>
      </div>
    </section>
  );
}

