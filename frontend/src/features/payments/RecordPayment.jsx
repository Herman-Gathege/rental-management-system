//frontend\src\features\payments\RecordPayment.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { recordPayment } from "../../api/payments";
import { getLeases } from "../../api/leases";
import { getTenants } from "../../api/tenants";

export default function RecordPayment() {
  const navigate = useNavigate();
  const [leases, setLeases] = useState([]);
  const [tenants, setTenants] = useState([]);

  const [form, setForm] = useState({
    tenant_id: "",
    lease_id: "",
    amount: "",
    payment_method: "mpesa",
    reference: "",
    payment_date: new Date().toISOString().split("T")[0],
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const [leaseData, tenantData] = await Promise.all([
          getLeases({ status: "active" }),
          getTenants(),
        ]);
        setLeases(leaseData);
        setTenants(tenantData);
      } catch (err) {
        console.error(err);
      }
    };
    fetch();
  }, []);

  // Auto-fill lease when tenant is selected
  useEffect(() => {
    if (form.tenant_id) {
      const tenantLeases = leases.filter((l) => l.tenant_id === form.tenant_id);
      if (tenantLeases.length === 1) {
        setForm((prev) => ({ ...prev, lease_id: tenantLeases[0].id }));
      }
    }
  }, [form.tenant_id, leases]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await recordPayment({
        ...form,
        amount: parseFloat(form.amount),
      });
      navigate("/owner/payments");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to record payment");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="properties-page">
      <h2>Record Payment</h2>
      {error && <div className="error-text">{error}</div>}

      <div className="property-form card">
        <div className="form-group">
          <label htmlFor="tenant_id">Tenant</label>
          <select id="tenant_id" name="tenant_id" className="input" value={form.tenant_id} onChange={handleChange} required>
            <option value="">Select tenant...</option>
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>{t.full_name} — {t.phone}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="lease_id">Lease</label>
          <select id="lease_id" name="lease_id" className="input" value={form.lease_id} onChange={handleChange} required>
            <option value="">Select lease...</option>
            {leases
              .filter((l) => !form.tenant_id || l.tenant_id === form.tenant_id)
              .map((l) => (
                <option key={l.id} value={l.id}>
                  {l.unit_name} — {l.property_name} (KES {Number(l.rent_amount).toLocaleString()}/mo)
                </option>
              ))}
          </select>
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="amount">Amount (KES)</label>
            <input id="amount" name="amount" className="input" type="number" placeholder="e.g. 15000" value={form.amount} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label htmlFor="payment_date">Payment Date</label>
            <input id="payment_date" name="payment_date" className="input" type="date" value={form.payment_date} onChange={handleChange} required />
          </div>
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="payment_method">Payment Method</label>
            <select id="payment_method" name="payment_method" className="input" value={form.payment_method} onChange={handleChange}>
              <option value="mpesa">M-Pesa</option>
              <option value="cash">Cash</option>
              <option value="bank">Bank Transfer</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="reference">Reference (optional)</label>
            <input id="reference" name="reference" className="input" placeholder="e.g. MPESA code" value={form.reference} onChange={handleChange} />
          </div>
        </div>

        <div className="flex gap-sm mt-md">
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting || !form.tenant_id || !form.lease_id || !form.amount}>
            {submitting ? "Recording..." : "Record Payment"}
          </button>
          <button className="btn btn-secondary" onClick={() => navigate("/owner/payments")} type="button">Cancel</button>
        </div>
      </div>
    </section>
  );
}
