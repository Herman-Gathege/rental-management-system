//frontend\src\features\tickets\CreateTicket.jsx
//
// Create ticket form (Sprint 6). Role-aware:
//   Tenant  → property/unit pre-resolved from their lease (backend scopes it).
//             They don't pick a property — the backend fills that from their
//             tenant record. We still show a simple form: title, category,
//             description, priority.
//   PM/Owner → full property + unit + tenant dropdowns.
// On success → navigate to the new ticket's detail page.

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createTicket } from "../../api/tickets";
import { getProperties } from "../../api/properties";
import { getUnits } from "../../api/units";
import { useAuth } from "../../context/AuthContext";

const CATEGORIES = [
  "maintenance", "repairs", "electricity", "water", "security",
  "cleaning", "noise", "lease_question", "billing_question",
  "complaint", "suggestion", "other",
];

const PRIORITIES = ["low", "medium", "high", "critical"];

function dashboardBase(role) {
  switch (role) {
    case "property_manager": return "/manager";
    case "finance":          return "/finance";
    case "tenant":           return "/tenant";
    default:                 return "/owner";
  }
}

export default function CreateTicket() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const role = user?.role?.toLowerCase();
  const base = dashboardBase(role);
  const isTenant = role === "tenant";

  const [properties, setProperties] = useState([]);
  const [units, setUnits] = useState([]);

  const [form, setForm] = useState({
    property_id: "",
    unit_id: "",
    title: "",
    description: "",
    category: "maintenance",
    priority: "medium",
  });

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Load properties for non-tenant roles
  useEffect(() => {
    if (isTenant) return;
    getProperties()
      .then(setProperties)
      .catch(() => setProperties([]));
  }, [isTenant]);

  // Load units when property changes
  useEffect(() => {
    if (!form.property_id) { setUnits([]); return; }
    getUnits(form.property_id)
      .then(setUnits)
      .catch(() => setUnits([]));
  }, [form.property_id]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handlePropertyChange = (e) => {
    setForm({ ...form, property_id: e.target.value, unit_id: "" });
  };

  const handleSubmit = async () => {
    setError("");
    if (!form.title.trim()) { setError("Title is required"); return; }
    if (!form.description.trim()) { setError("Description is required"); return; }
    if (!isTenant && !form.property_id) { setError("Property is required"); return; }

    setSubmitting(true);
    try {
      const payload = {
        title: form.title.trim(),
        description: form.description.trim(),
        category: form.category,
        priority: form.priority,
        // Tenants don't pick a property — backend resolves it from their tenant record.
        // We pass a placeholder property_id that the backend will override; however
        // our backend requires property_id, so for tenants we pass an empty string
        // and the backend 400s if their property isn't resolvable — in practice,
        // tenants always have a lease + property. Non-tenants must pick one.
        property_id: isTenant ? (form.property_id || "") : form.property_id,
        unit_id: form.unit_id || null,
      };
      const ticket = await createTicket(payload);
      navigate(`${base}/tickets/${ticket.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create ticket");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="properties-page">
      <h2>Report an Issue</h2>
      {error && <div className="error-text">{error}</div>}

      <div className="property-form card">
        {/* Property + unit — staff only */}
        {!isTenant && (
          <>
            <div className="form-group">
              <label htmlFor="property_id">Property</label>
              <select
                id="property_id"
                name="property_id"
                className="input"
                value={form.property_id}
                onChange={handlePropertyChange}
                required
              >
                <option value="">Select property...</option>
                {properties.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="unit_id">
                Unit <span className="text-sm text-muted">(optional)</span>
              </label>
              <select
                id="unit_id"
                name="unit_id"
                className="input"
                value={form.unit_id}
                onChange={handleChange}
                disabled={!form.property_id}
              >
                <option value="">
                  {form.property_id ? "Whole property / no specific unit" : "Select a property first"}
                </option>
                {units.map((u) => (
                  <option key={u.id} value={u.id}>{u.name}</option>
                ))}
              </select>
            </div>
          </>
        )}

        {/* Tenant: simple property selector if they have multiple properties */}
        {isTenant && properties.length > 1 && (
          <div className="form-group">
            <label htmlFor="property_id">Property</label>
            <select
              id="property_id"
              name="property_id"
              className="input"
              value={form.property_id}
              onChange={handlePropertyChange}
            >
              <option value="">My property</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="title">Title</label>
          <input
            id="title"
            name="title"
            className="input"
            type="text"
            placeholder="e.g. Kitchen tap is leaking"
            value={form.title}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            className="input"
            rows={4}
            placeholder="Describe the issue in detail — location, when it started, severity..."
            value={form.description}
            onChange={handleChange}
            required
          />
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="category">Category</label>
            <select
              id="category"
              name="category"
              className="input"
              value={form.category}
              onChange={handleChange}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="priority">Priority</label>
            <select
              id="priority"
              name="priority"
              className="input"
              value={form.priority}
              onChange={handleChange}
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
        </div>

        {form.priority === "critical" && (
          <div className="card info-banner-warning">
            <p className="text-sm">
              <strong>Critical priority</strong> — reserved for emergencies
              (fire, burst pipe, gas leak, security breach). Your report will
              be flagged immediately.
            </p>
          </div>
        )}

        <div className="flex gap-sm mt-md">
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={
              submitting ||
              !form.title.trim() ||
              !form.description.trim() ||
              (!isTenant && !form.property_id)
            }
          >
            {submitting ? "Submitting..." : "Submit Ticket"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => navigate(`${base}/tickets`)}
            type="button"
          >
            Cancel
          </button>
        </div>
      </div>
    </section>
  );
}
