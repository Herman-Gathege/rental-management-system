import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getProperty } from "../../api/properties";
import API from "../../api/client";

export default function EditProperty() {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", address: "", city: "", country: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await getProperty(propertyId);
        setForm({ name: data.name, address: data.address, city: data.city, country: data.country });
      } catch (err) {
        setError("Failed to load property");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [propertyId]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async () => {
    setError("");
    setSubmitting(true);
    try {
      await API.put(`/properties/${propertyId}`, form);
      navigate(`/owner/properties/${propertyId}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <p>Loading...</p>;

  return (
    <section className="properties-page">
      <h2>Edit Property</h2>
      {error && <div className="error-text">{error}</div>}
      <div className="property-form card">
        <div className="form-group"><label>Name</label><input className="input" name="name" value={form.name} onChange={handleChange} /></div>
        <div className="form-group"><label>Address</label><input className="input" name="address" value={form.address} onChange={handleChange} /></div>
        <div className="form-group"><label>City</label><input className="input" name="city" value={form.city} onChange={handleChange} /></div>
        <div className="form-group"><label>Country</label><input className="input" name="country" value={form.country} onChange={handleChange} /></div>
        <div className="flex gap-sm mt-md">
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>{submitting ? "Saving..." : "Save Changes"}</button>
          <button className="btn btn-secondary" onClick={() => navigate(`/owner/properties/${propertyId}`)}>Cancel</button>
        </div>
      </div>
    </section>
  );
}
