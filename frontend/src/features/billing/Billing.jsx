//frontend\src\features\billing\Billing.jsx
import { useEffect, useState } from "react";
import { generateMonthlyCharges, getCharges } from "../../api/charges";
import { useProperty } from "../../context/PropertyContext";

const money = (n) => Number(n || 0).toLocaleString();

// A charge is "late" for display purposes if it still owes a balance and its
// due date is strictly before today (a charge due *today* is not yet late).
const startOfToday = () => {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
};
const isLate = (c) => Number(c.balance) > 0 && new Date(c.due_date) < startOfToday();

// A tenant is "in credit" when they've overpaid against their total charges.
// That overpayment is lease-level (it isn't on any single charge), so the
// backend sends it as account_credit. When it exists, every (settled) charge
// row for that lease shows the credit instead of a 0 balance.
const hasCredit = (c) => Number(c.account_credit) > 0;

// Balance colour: green when in credit, red when past-due, plain otherwise.
const balanceClass = (c) =>
  hasCredit(c) ? "balance-credit" : isLate(c) ? "balance-late" : "";

// What to print in the Balance column: the credit (as a negative, e.g.
// "-27,500") when overpaid, otherwise the charge's own balance.
const balanceText = (c) =>
  hasCredit(c) ? `-${money(c.account_credit)}` : money(c.balance);

const pillClass = (status) =>
  status === "paid"
    ? "status-ok"
    : status === "overdue"
    ? "status-owed"
    : status === "partial"
    ? "status-partial"
    : "status-paid"; // pending

export default function Billing() {
  const { activeProperty } = useProperty();
  const [charges, setCharges] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [generating, setGenerating] = useState(false);

  const fetchCharges = async () => {
    try {
      setLoading(true);
      const data = await getCharges(statusFilter || null, null, activeProperty?.id || null);
      setCharges(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load charges");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharges();
  }, [statusFilter, activeProperty]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError("");
    try {
      const result = await generateMonthlyCharges();
      setSuccess(result.message);
      await fetchCharges();
      setTimeout(() => setSuccess(""), 4000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate charges");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Billing & Charges</h2>
        <button
          className="btn btn-primary btn-sm"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Generating..." : "Generate Monthly Charges"}
        </button>
      </div>

      {success && <div className="success-banner">{success}</div>}
      {error && <div className="error-text">{error}</div>}

      {/* "pending" filter removed: it duplicated "overdue" in practice.
          Pending charges still appear under "All". */}
      <div className="flex gap-sm flex-wrap">
        {["", "partial", "paid", "overdue"].map((s) => (
          <button
            key={s}
            className={`btn btn-sm ${statusFilter === s ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setStatusFilter(s)}
          >
            {s || "All"}
          </button>
        ))}
      </div>

      {loading ? (
        <p>Loading charges...</p>
      ) : charges.length === 0 ? (
        <div className="empty-state">
          <p>No charges yet.</p>
          <p className="text-muted">Click "Generate Monthly Charges" to bill all active leases.</p>
        </div>
      ) : (
        <>
          <div className="properties-table-wrapper hidden-mobile">
            <table className="properties-table">
              <thead>
                <tr>
                  <th>Tenant</th>
                  <th>Unit</th>
                  <th>Property</th>
                  <th>Amount (KES)</th>
                  <th>Paid (KES)</th>
                  <th>Balance (KES)</th>
                  <th>Due Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {charges.map((c) => (
                  <tr key={c.id}>
                    <td className="prop-name">{c.tenant_name}</td>
                    <td>{c.unit_name}</td>
                    <td>{c.property_name}</td>
                    <td>{money(c.amount)}</td>
                    <td>{money(c.amount_paid)}</td>
                    <td className={balanceClass(c)}>{balanceText(c)}</td>
                    <td>{new Date(c.due_date).toLocaleDateString()}</td>
                    <td>
                      <span className={`status-pill ${pillClass(c.status)}`}>{c.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="hidden-desktop properties-cards">
            {charges.map((c) => (
              <div key={c.id} className="property-card card">
                <div className="property-card-header">
                  <strong>{c.tenant_name}</strong>
                  <span className={`status-pill ${pillClass(c.status)}`}>{c.status}</span>
                </div>
                <div className="text-sm">{c.unit_name} — {c.property_name}</div>
                <div className="text-sm">Amount: KES {money(c.amount)}</div>
                <div className="text-sm">Paid: KES {money(c.amount_paid)}</div>
                <div className={`text-sm ${balanceClass(c)}`}>
                  Balance: KES {balanceText(c)}
                </div>
                <div className="text-sm text-muted">Due: {new Date(c.due_date).toLocaleDateString()}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
