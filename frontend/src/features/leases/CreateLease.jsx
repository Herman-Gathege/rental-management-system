//frontend\src\features\leases\CreateLease.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createLease } from "../../api/leases";
import { getUnits } from "../../api/units";
import { getTenants } from "../../api/tenants";

export default function CreateLease() {
  const navigate = useNavigate();

  const [units, setUnits] = useState([]);
  const [tenants, setTenants] = useState([]);

  const [form, setForm] = useState({
    unit_id: "",
    tenant_id: "",
    start_date: "",
    end_date: "",
    rent_amount: "",
    deposit_amount: "",
    billing_day: "1",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const [unitData, tenantData] = await Promise.all([
          getUnits(),
          getTenants(),
        ]);
        // Only show vacant units
        setUnits(unitData.filter((u) => u.occupancy_status === "vacant" && u.is_active));
        setTenants(tenantData);
      } catch (err) {
        console.error(err);
      }
    };
    fetch();
  }, []);

  // Auto-fill rent when unit is selected
  useEffect(() => {
    if (form.unit_id) {
      const unit = units.find((u) => u.id === form.unit_id);
      if (unit) {
        setForm((prev) => ({ ...prev, rent_amount: String(unit.rent_amount) }));
      }
    }
  }, [form.unit_id, units]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const payload = {
        unit_id: form.unit_id,
        tenant_id: form.tenant_id,
        start_date: form.start_date,
        end_date: form.end_date || null,
        rent_amount: parseFloat(form.rent_amount),
        deposit_amount: form.deposit_amount ? parseFloat(form.deposit_amount) : 0,
        billing_day: parseInt(form.billing_day),
      };
      await createLease(payload);
      navigate("/owner/leases");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create lease");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="properties-page">
      <h2>Create New Lease</h2>
      {error && <div className="error-text">{error}</div>}

      <div className="property-form card">
        <div className="form-group">
          <label htmlFor="unit_id">Unit (vacant only)</label>
          <select id="unit_id" name="unit_id" className="input" value={form.unit_id} onChange={handleChange} required>
            <option value="">Select unit...</option>
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name} — {u.property_name} (KES {Number(u.rent_amount).toLocaleString()})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="tenant_id">Tenant</label>
          <select id="tenant_id" name="tenant_id" className="input" value={form.tenant_id} onChange={handleChange} required>
            <option value="">Select tenant...</option>
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>{t.full_name} — {t.phone}</option>
            ))}
          </select>
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="start_date">Start Date</label>
            <input id="start_date" name="start_date" className="input" type="date" value={form.start_date} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label htmlFor="end_date">End Date (optional)</label>
            <input id="end_date" name="end_date" className="input" type="date" value={form.end_date} onChange={handleChange} />
          </div>
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="rent_amount">Monthly Rent (KES)</label>
            <input id="rent_amount" name="rent_amount" className="input" type="number" value={form.rent_amount} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label htmlFor="deposit_amount">Security Deposit (KES)</label>
            <input id="deposit_amount" name="deposit_amount" className="input" type="number" placeholder="0" value={form.deposit_amount} onChange={handleChange} />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="billing_day">Billing Day (day of month)</label>
          <input id="billing_day" name="billing_day" className="input" type="number" min="1" max="28" value={form.billing_day} onChange={handleChange} />
        </div>

        <div className="flex gap-sm mt-md">
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting || !form.unit_id || !form.tenant_id || !form.start_date || !form.rent_amount}>
            {submitting ? "Creating..." : "Create Lease"}
          </button>
          <button className="btn btn-secondary" onClick={() => navigate("/owner/leases")} type="button">Cancel</button>
        </div>
      </div>
    </section>
  );
}

