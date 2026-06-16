// frontend/src/features/dashboard/DashboardContent.jsx
//
// Landlord (owner) dashboard body. Greeting + org-wide widgets + notifications
// + recent payments.
// Pulls /dashboard/owner/summary (portfolio counts + money, the money block
// reusing the finance summary so the figures match the finance dashboard) and
// /dashboard/finance/recent-payments (the landlord is permitted on it).
// Reuses the shared .dash-* card styles, same as the manager/finance pages.

import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getOwnerSummary, getFinanceRecentPayments } from "../../api/dashboard";

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

  const [summary, setSummary] = useState(null);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const [s, p] = await Promise.all([
          getOwnerSummary(),
          getFinanceRecentPayments(),
        ]);
        if (!active) return;
        setSummary(s);
        setPayments(p);
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
  }, []);

  if (!user) return null;

  // Show the email after the greeting (matches the Finance dashboard look).
  // For name + email instead, use: `${user.full_name} — ${user.email}`.
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

  // Notifications placeholder. The notifications module isn't built yet, so
  // this renders an honest empty state for now; once there's a notifications
  // feed/endpoint, swap this array for the fetched items and map over them.
  const notifications = [];

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Welcome, <span className="company-blue text-bold">{greeting}</span> 👋
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

          <div className="dash-panel mb-md">
            <div className="dash-panel-title">Notifications</div>
            {notifications.length === 0 ? (
              <div className="text-muted">
                You're all caught up — no new notifications.
              </div>
            ) : (
              notifications.map((n, i) => (
                <div className="dash-row" key={i}>
                  <div>
                    <div className="text-bold">{n.title}</div>
                    <div className="text-muted">{n.body}</div>
                  </div>
                  <span className="text-muted">{fmtDate(n.created_at)}</span>
                </div>
              ))
            )}
          </div>

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
