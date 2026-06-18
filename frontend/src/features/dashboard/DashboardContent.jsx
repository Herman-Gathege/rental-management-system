// frontend/src/features/dashboard/DashboardContent.jsx
//
// Landlord (owner) dashboard body. Greeting + portfolio/money widgets +
// notifications + recent payments. Scopes to the property chosen in the navbar
// switcher (All = org-wide). Refetches when the selection changes.

import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useProperty } from "../../context/PropertyContext";
import { getOwnerSummary, getFinanceRecentPayments } from "../../api/dashboard";
import NotificationsCard from "../../components/ui/NotificationsCard";

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

export default function DashboardContent({ roleLabel }) {
  const { user } = useAuth();
  const { activeProperty } = useProperty();
  const activePropertyId = activeProperty?.id || null;

  const [summary, setSummary] = useState(null);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        setLoading(true);
        const [s, p] = await Promise.all([
          getOwnerSummary(activePropertyId),
          getFinanceRecentPayments(activePropertyId),
        ]);
        if (!active) return;
        setSummary(s);
        setPayments(p);
        setError("");
      } catch (err) {
        if (!active) return;
        setError(err?.response?.data?.detail || "Could not load your dashboard.");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [activePropertyId]);

  if (!user) return null;

  const greeting = user.email || user.full_name || "there";

  const cards = summary
    ? [
        { label: "Properties", value: summary.properties },
        { label: "Units", value: summary.units },
        { label: "Occupied", value: summary.occupied_units },
        { label: "Vacant", value: summary.vacant_units },
        { label: "Active Leases", value: summary.active_leases },
        { label: "Tenants", value: summary.tenants },
        { label: "Expected Rent", value: money(summary.expected_rent), money: true },
        { label: "Collected", value: money(summary.total_collected), money: true },
        { label: "Outstanding", value: money(summary.outstanding_balance), money: true },
      ]
    : [];

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Welcome, <span className="company-blue text-bold">{greeting}</span> 👋
      </div>

      <div className="text-muted mb-md">
        Viewing: {activeProperty ? activeProperty.name : "All Properties"}
      </div>

      {loading && <div className="dash-panel">Loading your dashboard…</div>}

      {!loading && error && (
        <div className="info-banner-warning">
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && summary && (
        <>
          <div className="dash-grid mb-md">
            {cards.map((c) => (
              <div className="dash-stat" key={c.label}>
                <div
                  className={`dash-stat-value${c.money ? " dash-stat-money" : ""}`}
                >
                  {c.value}
                </div>
                <div className="dash-stat-label">{c.label}</div>
              </div>
            ))}
          </div>

          <NotificationsCard />

          <div className="dash-panel">
            <div className="dash-panel-title">Recent Payments</div>
            {payments.length === 0 ? (
              <div className="text-muted">No payments recorded yet.</div>
            ) : (
              payments.map((p, i) => (
                <div className="dash-row" key={i}>
                  <div>
                    <div className="text-bold">{p.tenant_name}</div>
                    <div className="text-muted">
                      {fmtDate(p.payment_date)}
                      {p.method ? ` · ${p.method}` : ""}
                    </div>
                  </div>
                  <span className="text-bold">{money(p.amount)}</span>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
