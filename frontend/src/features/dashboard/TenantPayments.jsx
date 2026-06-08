//frontend/src/features/dashboard/TenantPayments.jsx
//
// Tenant "My Payments" page (Sprint 4.5 tenant portal, multi-lease + switcher).
// Payments come back tagged with property_id; this page filters them to the
// property chosen in the tenant property switcher (or shows all). A "Property"
// column appears only in All mode when more than one property is present.

import { useEffect, useState } from "react";
import { getTenantPayments } from "../../api/dashboard";
import { useTenantProperty } from "../../context/TenantPropertyContext";

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
  const tp = useTenantProperty() || {};
  const activePropertyId = tp.activePropertyId || null;
  const activeProperty = tp.activeProperty || null;

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

  const visible = payments.filter(
    (p) => !activePropertyId || p.property_id === activePropertyId
  );
  const totalPaid = visible.reduce((sum, p) => sum + Number(p.amount || 0), 0);

  const distinctProps = new Set(visible.map((p) => p.property_id).filter(Boolean));
  const showProperty = !activeProperty && distinctProps.size > 1;

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        My Payments{activeProperty ? ` — ${activeProperty.name}` : ""}
      </div>

      <div className="dash-panel">
        <div className="dash-panel-title">Payment History</div>

        {visible.length === 0 ? (
          <div className="text-muted">No payments yet.</div>
        ) : (
          <>
            <table className="staff-table">
              <thead>
                <tr>
                  {showProperty && <th>Property</th>}
                  <th>Date</th>
                  <th>Reference</th>
                  <th>Method</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((p, i) => (
                  <tr key={i}>
                    {showProperty && <td>{p.property_name || "—"}</td>}
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
