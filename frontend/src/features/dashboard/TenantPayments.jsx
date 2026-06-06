//frontend/src/features/dashboard/TenantPayments.jsx
//
// Tenant "My Payments" page (Sprint 4.5 tenant portal).
// Reuses the already-scoped /dashboard/tenant/payments endpoint via
// getTenantPayments() — the backend resolves the tenant from tenants.user_id,
// so this only ever returns the logged-in tenant's own payments. Styling
// reuses the existing dashboard classes; no new CSS.

import { useEffect, useState } from "react";
import { getTenantPayments } from "../../api/dashboard";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });

const fmtDate = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "—";

export default function TenantPayments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const p = await getTenantPayments();
        if (!active) return;
        setPayments(p);
      } catch (err) {
        if (!active) return;
        setError(err?.response?.data?.detail || "Could not load your payments.");
      } finally {
        if (active) setLoading(false);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <div className="dash-panel">Loading your payments…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="info-banner-warning">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const totalPaid = payments.reduce((sum, p) => sum + Number(p.amount || 0), 0);

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">My Payments</div>

      <div className="dash-panel">
        <div className="dash-panel-title">Payment History</div>

        {payments.length === 0 ? (
          <div className="text-muted">No payments yet.</div>
        ) : (
          <>
            <table className="staff-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Reference</th>
                  <th>Method</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p, i) => (
                  <tr key={i}>
                    <td>{fmtDate(p.date)}</td>
                    <td>{p.reference || "—"}</td>
                    <td>{p.method ? p.method.toUpperCase() : "—"}</td>
                    <td>{money(p.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="text-muted mt-md">
              Total paid: <span className="text-bold">{money(totalPaid)}</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
