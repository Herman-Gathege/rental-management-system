/*frontend\src\features\properties\createproperty.jsx*/
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createProperty } from "../../api/properties";
import { useProperty } from "../../context/PropertyContext";
// import "./Properties.css";

export default function CreateProperty() {
  const navigate = useNavigate();
  const { refreshProperties } = useProperty();

  const [form, setForm] = useState({
    name: "",
    address: "",
    city: "",
    country: "Kenya",
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
      await createProperty(form);
      await refreshProperties();
      navigate("/owner/properties");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create property");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="properties-page">
      <h2>Add New Property</h2>

      {error && <div className="error-text">{error}</div>}

      <div className="property-form card">
        <div className="form-group">
          <label htmlFor="name">Property Name</label>
          <input
            id="name"
            name="name"
            className="input"
            placeholder="e.g. Sunset Apartments"
            value={form.name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="address">Address</label>
          <input
            id="address"
            name="address"
            className="input"
            placeholder="e.g. 123 Moi Avenue"
            value={form.address}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="city">City</label>
          <input
            id="city"
            name="city"
            className="input"
            placeholder="e.g. Nairobi"
            value={form.city}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="country">Country</label>
          <input
            id="country"
            name="country"
            className="input"
            placeholder="e.g. Kenya"
            value={form.country}
            onChange={handleChange}
            required
          />
        </div>

        <div className="flex gap-sm">
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={submitting || !form.name || !form.address || !form.city}
          >
            {submitting ? "Creating..." : "Create Property"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => navigate("/owner/properties")}
            type="button"
          >
            Cancel
          </button>
        </div>
      </div>
    </section>
  );
}
