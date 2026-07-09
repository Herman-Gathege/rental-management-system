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
    payment_type: "rent",
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

  // Selected lease — used to prefill the amount when the payment type changes.
  const selectedLease = leases.find((l) => l.id === form.lease_id);

  // ─── Sprint 7 polish: smart default when a lease is picked ───
  // Business rule: the security deposit is paid at move-in. So the first
  // payment on a lease is almost always the deposit; every payment after
  // that is rent. Rather than default to "Rent" for every payment (which
  // is what caused a landlord to accidentally record the deposit as rent),
  // we ask the backend whether this lease's deposit charge is still unpaid
  // (lease.deposit_outstanding) and pre-select accordingly. The user can
  // still switch the type manually — this only changes the default.
  useEffect(() => {
    if (!selectedLease) return;

    const shouldDefaultToDeposit =
      selectedLease.deposit_outstanding &&
      Number(selectedLease.deposit_amount) > 0;

    const nextType = shouldDefaultToDeposit ? "deposit" : "rent";
    const nextAmount = shouldDefaultToDeposit
      ? String(selectedLease.deposit_amount || "")
      : String(selectedLease.rent_amount || "");

    setForm((prev) => ({
      ...prev,
      payment_type: nextType,
      amount: nextAmount,
    }));
  }, [form.lease_id, leases]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  // When the user switches type, offer a sensible default amount:
  // rent -> monthly rent; deposit -> deposit amount on the lease.
  const handleTypeChange = (e) => {
    const payment_type = e.target.value;
    let amount = form.amount;
    if (selectedLease) {
      if (payment_type === "deposit" && selectedLease.deposit_amount) {
        amount = String(selectedLease.deposit_amount);
      } else if (payment_type === "rent" && selectedLease.rent_amount) {
        amount = String(selectedLease.rent_amount);
      }
    }
    setForm({ ...form, payment_type, amount });
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

        {/* Payment type — rent vs security deposit. Keeping deposit money
            tagged separately is what stops it inflating rent-collection totals. */}
        <div className="form-group">
          <label htmlFor="payment_type">Payment Type</label>
          <select
            id="payment_type"
            name="payment_type"
            className="input"
            value={form.payment_type}
            onChange={handleTypeChange}
          >
            <option value="rent">Rent</option>
            <option value="deposit">Security Deposit</option>
          </select>
          {form.payment_type === "deposit" && (
            <p className="text-sm text-muted mt-xs">
              Recorded as a deposit — held separately and refundable at move-out,
              minus any damages.
            </p>
          )}
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
