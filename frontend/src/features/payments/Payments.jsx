//frontend\src\features\payments\Payments.jsx
import { useEffect, useState } from "react";
import { getPayments } from "../../api/payments";
import { useProperty } from "../../context/PropertyContext";
import { useAuth } from "../../context/AuthContext";
import { Link } from "react-router-dom";

export default function Payments() {
  const { activeProperty } = useProperty();
  const { user } = useAuth();
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Only the landlord records payments. Finance has a read-only view of this
  // page (and no /finance/payments/record route exists), so the button is
  // hidden for them. The record link is owner-scoped, so gating on LANDLORD
  // also keeps it from showing anywhere it wouldn't work.
  const canRecord = user?.role === "LANDLORD";

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await getPayments(null, null, activeProperty?.id || null);
        setPayments(data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load payments");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [activeProperty]);

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Payments</h2>
        {canRecord && (
          <Link to="/owner/payments/record" className="btn btn-primary btn-sm">
            + Record Payment
          </Link>
        )}
      </div>

      {error && <div className="error-text">{error}</div>}

      {loading ? (
        <p>Loading payments...</p>
      ) : payments.length === 0 ? (
        <div className="empty-state">
          <p>No payments recorded yet.</p>
          {canRecord && (
            <Link to="/owner/payments/record" className="btn btn-primary">
              Record First Payment
            </Link>
          )}
        </div>
      ) : (
        <>
          <div className="properties-table-wrapper hidden-mobile">
            <table className="properties-table">
              <thead>
                <tr>
                  <th>Tenant</th>
                  <th>Amount (KES)</th>
                  <th>Method</th>
                  <th>Reference</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p) => (
                  <tr key={p.id}>
                    <td className="prop-name">{p.tenant_name}</td>
                    <td>{Number(p.amount).toLocaleString()}</td>
                    <td>{p.payment_method.toUpperCase()}</td>
                    <td>{p.reference || "—"}</td>
                    <td>{new Date(p.payment_date).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="hidden-desktop properties-cards">
            {payments.map((p) => (
              <div key={p.id} className="property-card card">
                <strong>{p.tenant_name}</strong>
                <div className="text-sm">KES {Number(p.amount).toLocaleString()}</div>
                <div className="text-sm">{p.payment_method.toUpperCase()} {p.reference ? `— ${p.reference}` : ""}</div>
                <div className="text-sm text-muted">{new Date(p.payment_date).toLocaleDateString()}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
