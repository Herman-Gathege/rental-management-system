//frontend/src/features/dashboard/StaffDashboard.jsx
//
// Property Manager dashboard (Sprint 4.5).
// Stats scope to the property chosen in the navbar switcher (All = every
// assigned property); refetches on change. The "Your Properties" list always
// shows all assigned properties.
//
// Sprint 5: adds a best-effort "Expenses (YTD)" widget (paid / approved-pending
// / NOI + category breakdown) scoped to assigned properties (and the active
// property when one is selected). The expense reports are fetched separately so
// a hiccup there never blanks the core dashboard.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useProperty } from "../../context/PropertyContext";
import { getManagerSummary, getManagerProperties } from "../../api/dashboard";
import {
  getExpenseSummary,
  getNOI,
  getExpensesByCategory,
} from "../../api/expenses";
import NotificationsCard from "../../components/ui/NotificationsCard";

const money = (n) => `KES ${Number(n || 0).toLocaleString()}`;

const ytd = () => {
  const year = new Date().getFullYear();
  return { start_date: `${year}-01-01`, end_date: new Date().toISOString().slice(0, 10) };
};

const BAR_TRACK = {
  background: "#eef2f7",
  borderRadius: 4,
  height: 10,
  flex: 1,
  overflow: "hidden",
};

function Bar({ label, amount, max, color }) {
  const pct = max > 0 ? Math.max(2, Math.round((amount / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-sm mb-sm">
      <div className="text-sm" style={{ width: 130 }}>{label}</div>
      <div style={BAR_TRACK}>
        <div style={{ width: `${pct}%`, background: color, height: "100%" }} />
      </div>
      <div className="text-sm text-bold" style={{ width: 110, textAlign: "right" }}>
        {money(amount)}
      </div>
    </div>
  );
}

export default function StaffDashboard() {
  const { user } = useAuth();
  const { activeProperty } = useProperty();
  const activePropertyId = activeProperty?.id || null;

  const [summary, setSummary] = useState(null);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Expense widget (best-effort, doesn't block the core dashboard)
  const [expenseSummary, setExpenseSummary] = useState(null);
  const [noi, setNoi] = useState(null);
  const [byCategory, setByCategory] = useState([]);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setLoading(true);
        const [s, p] = await Promise.all([
          getManagerSummary(activePropertyId),
          getManagerProperties(),
        ]);
        if (!active) return;
        setSummary(s);
        setProperties(p);
        setError("");
      } catch (err) {
        if (!active) return;
        setError(
          err?.response?.data?.detail || "Could not load your dashboard."
        );
      } finally {
        if (active) setLoading(false);
      }

      // Expense reports — separate so a failure here leaves the rest intact.
      try {
        const params = ytd();
        if (activePropertyId) params.property_id = activePropertyId;
        const [exp, noiData, cats] = await Promise.all([
          getExpenseSummary(params),
          getNOI(params),
          getExpensesByCategory(params),
        ]);
        if (!active) return;
        setExpenseSummary(exp);
        setNoi(noiData);
        setByCategory(cats);
      } catch {
        if (!active) return;
        setExpenseSummary(null);
        setNoi(null);
        setByCategory([]);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, [activePropertyId]);

  const displayName = user?.full_name || user?.email || "there";

  const cards = summary
    ? [
        { label: "Properties", value: summary.properties },
        { label: "Units", value: summary.units },
        { label: "Occupied Units", value: summary.occupied_units },
        { label: "Vacant Units", value: summary.vacant_units },
        { label: "Active Leases", value: summary.active_leases },
        { label: "Tenants", value: summary.tenants },
      ]
    : [];

  const noiValue = noi?.noi ?? 0;
  const maxCategory = Math.max(0, ...byCategory.map((c) => c.total));

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Welcome, <span className="company-blue text-bold">{displayName}</span> 👋
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
          {summary.properties === 0 && (
            <div className="hint mb-md">
              No properties are assigned to you yet. Once a landlord assigns you
              to properties, your stats will appear here.
            </div>
          )}

          <div className="dash-grid mb-md">
            {cards.map((c) => (
              <div className="dash-stat" key={c.label}>
                <div className="dash-stat-value">{c.value}</div>
                <div className="dash-stat-label">{c.label}</div>
              </div>
            ))}
          </div>

          {/* ─── Expenses (YTD) — Sprint 5 ─── */}
          {expenseSummary && (
            <div className="dash-panel mb-md">
              <div className="flex items-center justify-between mb-sm">
                <div className="dash-panel-title">Expenses (YTD)</div>
                <Link to="/manager/expenses" className="btn btn-secondary btn-sm">
                  View all
                </Link>
              </div>

              <div className="dash-grid mb-md">
                <div className="dash-stat">
                  <div className="dash-stat-value">{money(expenseSummary.total_paid)}</div>
                  <div className="dash-stat-label">Paid</div>
                </div>
                <div className="dash-stat">
                  <div className="dash-stat-value">{money(expenseSummary.total_approved)}</div>
                  <div className="dash-stat-label">Approved · pending</div>
                </div>
                <div className="dash-stat">
                  <div
                    className="dash-stat-value"
                    style={{ color: noiValue >= 0 ? "#16a34a" : "#ef4444" }}
                  >
                    {money(noiValue)}
                  </div>
                  <div className="dash-stat-label">Net Operating Income</div>
                </div>
              </div>

              {byCategory.length === 0 ? (
                <p className="text-sm text-muted">No paid expenses yet this year.</p>
              ) : (
                byCategory.map((c) => (
                  <Bar
                    key={c.category_id}
                    label={c.category_name}
                    amount={c.total}
                    max={maxCategory}
                    color="#2563eb"
                  />
                ))
              )}
            </div>
          )}

          <NotificationsCard />

          <div className="dash-panel">
            <div className="dash-panel-title">Your Properties</div>
            {properties.length === 0 ? (
              <div className="text-muted">No properties assigned.</div>
            ) : (
              properties.map((p) => (
                <div className="dash-row" key={p.id}>
                  <span className="text-bold">{p.name}</span>
                  <span className="text-muted">{p.city}</span>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
