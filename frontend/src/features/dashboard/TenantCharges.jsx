//frontend/src/features/dashboard/TenantCharges.jsx
//
// Tenant "My Charges" page (Sprint 4.5 tenant portal, multi-lease + switcher).
// Charges come back tagged with property_id; this page filters them to the
// property chosen in the tenant property switcher (or shows all). A "Property"
// column appears only in All mode when more than one property is present, so
// mixed rows stay readable without cluttering single-property views.

import { useEffect, useState } from "react";
import { getTenantCharges } from "../../api/dashboard";
import { useTenantProperty } from "../../context/TenantPropertyContext";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });

const fmtMonth = (d) =>
  d ? new Date(d).toLocaleDateString("en-GB", { month: "short", year: "numeric" }) : "—";

const fmtDate = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "—";

const startOfToday = () => {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
};

const isLate = (c) =>
  Number(c.balance) > 0 && c.due_date && new Date(c.due_date) < startOfToday();

export default function TenantCharges() {
  const tp = useTenantProperty() || {};
  const activePropertyId = tp.activePropertyId || null;
  const activeProperty = tp.activeProperty || null;

  const [charges, setCharges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const c = await getTenantCharges();
        if (!active) return;
        setCharges(c);
      } catch (err) {
        if (!active) return;
        setError(err?.response?.data?.detail || "Could not load your charges.");
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
        <div className="dash-panel">Loading your charges…</div>
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

  const visible = charges.filter(
    (c) => !activePropertyId || c.property_id === activePropertyId
  );
  const totalOutstanding = visible.reduce((sum, c) => sum + Number(c.balance || 0), 0);

  const distinctProps = new Set(visible.map((c) => c.property_id).filter(Boolean));
  const showProperty = !activeProperty && distinctProps.size > 1;

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        My Charges{activeProperty ? ` — ${activeProperty.name}` : ""}
      </div>

      <div className="dash-panel">
        <div className="dash-panel-title">Rent Charges</div>

        {visible.length === 0 ? (
          <div className="text-muted">No charges yet.</div>
        ) : (
          <>
            <table className="staff-table">
              <thead>
                <tr>
                  {showProperty && <th>Property</th>}
                  <th>Month</th>
                  <th>Due</th>
                  <th>Amount</th>
                  <th>Paid</th>
                  <th>Balance</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((c, i) => (
                  <tr key={i}>
                    {showProperty && <td>{c.property_name || "—"}</td>}
                    <td>{fmtMonth(c.month)}</td>
                    <td>{fmtDate(c.due_date)}</td>
                    <td>{money(c.amount)}</td>
                    <td>{money(c.amount_paid)}</td>
                    <td className={isLate(c) ? "balance-late" : ""}>
                      {money(c.balance)}
                    </td>
                    <td>{c.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="text-muted mt-md">
              Total outstanding:{" "}
              <span className="text-bold">{money(totalOutstanding)}</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
