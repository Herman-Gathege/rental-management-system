//frontend/src/features/dashboard/FinanceDashboard.jsx
//
// Finance dashboard (Sprint 4.5).
// Pulls /dashboard/finance/summary + /dashboard/finance/recent-payments and
// shows org-wide money: expected rent, collected, outstanding, overdue count,
// plus the latest payments. Reuses the shared .dash-* card styles.

import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import {
  getFinanceSummary,
  getFinanceRecentPayments,
} from "../../api/dashboard";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });

export default function FinanceDashboard() {
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
          getFinanceSummary(),
          getFinanceRecentPayments(),
        ]);
        if (!active) return;
        setSummary(s);
        setPayments(p);
      } catch (err) {
        if (!active) return;
        setError(
          err?.response?.data?.detail || "Could not load the finance dashboard."
        );
      } finally {
        if (active) setLoading(false);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, []);

  const displayName = user?.full_name || user?.email || "there";

  const cards = summary
    ? [
        { label: "Expected Rent", value: money(summary.expected_rent), money: true },
        { label: "Collected", value: money(summary.total_collected), money: true },
        { label: "Outstanding", value: money(summary.outstanding_balance), money: true },
        { label: "Overdue Charges", value: summary.overdue_charges, money: false },
      ]
    : [];

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Welcome, <span className="company-blue text-bold">{displayName}</span> 👋
      </div>

      {loading && <div className="dash-panel">Loading the finance dashboard…</div>}

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
                      {p.payment_date}
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
