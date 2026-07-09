//frontend/src/features/dashboard/TenantPayments.jsx
//
// Tenant "My Payments" page (Sprint 4.5 tenant portal, multi-lease + switcher).
// Payments come back tagged with property_id; this page filters them to the
// property chosen in the tenant property switcher (or shows all). A "Property"
// column appears only in All mode when more than one property is present.
// Responsive: table on desktop, MobileCardList stacked cards below 768px.
//
// Sprint 7 polish: added a "Type" column so the tenant can see at a glance
// which payments settled rent vs the security deposit. The backend already
// returns payment_type on every row (see dashboard_service.get_tenant_payments).

import { useEffect, useState } from "react";
import { getTenantPayments } from "../../api/dashboard";
import { useTenantProperty } from "../../context/TenantPropertyContext";
import MobileCardList from "../../components/ui/MobileCardList";

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

// "rent" -> "Rent", "deposit" -> "Deposit". Fallback dash if the row is old
// data with no payment_type set.
const typeLabel = (t) =>
  t ? t.charAt(0).toUpperCase() + t.slice(1) : "—";

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
            {/* Desktop table */}
            <div className="staff-table-wrap hidden-mobile">
              <table className="staff-table">
                <thead>
                  <tr>
                    {showProperty && <th>Property</th>}
                    <th>Date</th>
                    <th>Type</th>
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
                      <td>{typeLabel(p.payment_type)}</td>
                      <td>{p.reference || "—"}</td>
                      <td>{p.method ? p.method.toUpperCase() : "—"}</td>
                      <td>{money(p.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <MobileCardList
              data={visible}
              renderCard={(p, i) => (
                <div className="staff-card" key={i}>
                  <div className="staff-card-title">{fmtDate(p.date)}</div>
                  {showProperty && (
                    <div className="staff-card-row">
                      <span>Property</span>
                      <span>{p.property_name || "—"}</span>
                    </div>
                  )}
                  <div className="staff-card-row">
                    <span>Type</span>
                    <span>{typeLabel(p.payment_type)}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Reference</span>
                    <span>{p.reference || "—"}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Method</span>
                    <span>{p.method ? p.method.toUpperCase() : "—"}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Amount</span>
                    <span>{money(p.amount)}</span>
                  </div>
                </div>
              )}
            />

            <div className="text-muted mt-md">
              Total paid: <span className="text-bold">{money(totalPaid)}</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
