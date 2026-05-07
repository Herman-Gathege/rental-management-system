//frontend\src\features\billing\Billing.jsx
import { useEffect, useState } from "react";
import { generateMonthlyCharges, getCharges } from "../../api/charges";
import { useProperty } from "../../context/PropertyContext";

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

      <div className="flex gap-sm flex-wrap">
        {["", "pending", "paid", "overdue"].map((s) => (
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
                    <td>{Number(c.amount).toLocaleString()}</td>
                    <td>{new Date(c.due_date).toLocaleDateString()}</td>
                    <td>
                      <span className={`status-pill ${c.status === "paid" ? "status-ok" : c.status === "overdue" ? "status-owed" : "status-paid"}`}>
                        {c.status}
                      </span>
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
                  <span className={`status-pill ${c.status === "paid" ? "status-ok" : c.status === "overdue" ? "status-owed" : "status-paid"}`}>
                    {c.status}
                  </span>
                </div>
                <div className="text-sm">{c.unit_name} — {c.property_name}</div>
                <div className="text-sm">KES {Number(c.amount).toLocaleString()}</div>
                <div className="text-sm text-muted">Due: {new Date(c.due_date).toLocaleDateString()}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
