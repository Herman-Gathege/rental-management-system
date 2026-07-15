// frontend/src/features/dashboard/DashboardContent.jsx
//
// Landlord (owner) dashboard body. Greeting + portfolio/money widgets +
// notifications + recent payments. Scopes to the property chosen in the navbar
// switcher (All = org-wide). Refetches when the selection changes.
//
// Sprint 6: adds a portfolio-wide Ticket Overview section (open vs closed,
// critical issues, avg resolution time, by-category, top properties) fed by
// GET /tickets/metrics/summary. CSS bars (no chart lib in this stack).
//
// Sprint 6.2 (#7): adds a "Deposits Held" money card — deposits are tracked
// separately from rent so they never inflate collected/expected.
//
// Sprint 7 cleanup:
//   - Recent Payments trimmed to a 4-row preview with a "View all" link
//     matching the NotificationsCard pattern so the dashboard stays compact.
//   - Removed the "Tickets by Status" bar chart from the Ticket Overview
//     panel. The four headline stats (Open, Closed, Critical/High, Avg
//     resolution) already summarise state well; the redundant bar chart
//     was crowding the page.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

import { useProperty } from "../../context/PropertyContext";
import { getOwnerSummary, getFinanceRecentPayments } from "../../api/dashboard";
import { getTicketMetrics } from "../../api/ticketMetrics";
import NotificationsCard from "../../components/ui/NotificationsCard";
import TicketsSummaryCard from "../../components/ui/TicketsSummaryCard";

// Cap on dashboard-preview rows for Recent Payments. Full history is still
// reachable via the "View all" link — this keeps the card compact.
const RECENT_PAYMENTS_LIMIT = 4;

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

// Present avg resolution hours as a human string.
const fmtResolution = (hours) => {
  if (hours == null) return "—";
  if (hours < 1) return `${Math.round(hours * 60)} min`;
  if (hours < 48) return `${hours.toFixed(1)} hrs`;
  return `${(hours / 24).toFixed(1)} days`;
};

const BAR_TRACK = {
  background: "#eef2f7",
  borderRadius: 4,
  height: 10,
  flex: 1,
  overflow: "hidden",
};

function Bar({ label, value, max, color }) {
  const pct = max > 0 ? Math.max(2, Math.round((value / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-sm mb-sm">
      <div
        className="text-sm"
        style={{ width: 150, textTransform: "capitalize" }}
      >
        {label}
      </div>
      <div style={BAR_TRACK}>
        <div style={{ width: `${pct}%`, background: color, height: "100%" }} />
      </div>
      <div
        className="text-sm text-bold"
        style={{ width: 44, textAlign: "right" }}
      >
        {value}
      </div>
    </div>
  );
}

// Where to send "View all" from the Recent Payments preview. The full-history
// route is different per role even though this component is currently only
// used from the landlord dashboard — future-proofed the same way
// NotificationsCard is.
function paymentsHistoryPath(role) {
  switch ((role || "").toLowerCase()) {
    case "property_manager":
      return "/manager/payments/history";
    case "finance":
      return "/finance/payments";
    case "tenant":
      return "/tenant/payments";
    default:
      return "/owner/payments/history";
  }
}

// Color per status for the by-status bars.
// const statusColor = (s) => {
//   switch (s) {
//     case "open":
//       return "#f59e0b";
//     case "assigned":
//       return "#2563eb";
//     case "in_progress":
//       return "#0ea5e9";
//     case "waiting":
//       return "#a855f7";
//     case "resolved":
//       return "#22c55e";
//     case "closed":
//       return "#6b7280";
//     default:
//       return "#94a3b8";
//   }
// };

export default function DashboardContent({ roleLabel }) {
  const { user } = useAuth();
  const { activeProperty } = useProperty();
  const activePropertyId = activeProperty?.id || null;

  const [summary, setSummary] = useState(null);
  const [payments, setPayments] = useState([]);
  const [metrics, setMetrics] = useState(null);
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
        setError(
          err?.response?.data?.detail || "Could not load your dashboard.",
        );
      } finally {
        if (active) setLoading(false);
      }

      // Ticket metrics — best-effort, portfolio-wide (not property-filtered).
      try {
        const m = await getTicketMetrics();
        if (!active) return;
        setMetrics(m);
      } catch {
        if (!active) return;
        setMetrics(null);
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
        {
          label: "Expected Rent",
          value: money(summary.expected_rent),
          money: true,
        },
        {
          label: "Collected",
          value: money(summary.total_collected),
          money: true,
        },
        {
          label: "Outstanding",
          value: money(summary.outstanding_balance),
          money: true,
        },
        {
          label: "Deposits Held",
          value: money(summary.deposits_held),
          money: true,
        },
      ]
    : [];

  const maxCategory = metrics
    ? Math.max(0, ...Object.values(metrics.by_category || {}))
    : 0;
  const maxProp = metrics
    ? Math.max(0, ...(metrics.top_properties || []).map((p) => p.count))
    : 0;

  // Sprint 7 cleanup: preview only the newest RECENT_PAYMENTS_LIMIT rows.
  // The API can return more; we slice client-side so this widget stays
  // compact on the dashboard while the full list remains one click away.
  const paymentsPreview = payments.slice(0, RECENT_PAYMENTS_LIMIT);
  const paymentsPath = paymentsHistoryPath(user?.role);

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
          {/* ─── Portfolio-wide Ticket Overview (Sprint 6) ─── */}
          {/* Compact recent/urgent tickets card */}
          {/* Compact recent/urgent tickets card */}
          <TicketsSummaryCard />
          <div className="dashboard-bottom-grid">
            <NotificationsCard />

            <div className="dash-panel">
              <div className="flex justify-between items-center mb-md">
                <div className="dash-panel-title">Recent Payments</div>
                <div
                  style={{
                    // marginTop: "1rem",
                    display: "flex",
                    justifyContent: "flex-end",
                  }}
                >
                  <Link
                    to="/owner/payments/history"
                    className="btn btn-secondary btn-sm"
                  >
                    View All Payments
                  </Link>
                </div>
              </div>


              {payments.length === 0 ? (
                <div className="text-muted">No payments recorded yet.</div>
              ) : (
                <>
                  {/* <span className="text-muted">
                    Showing latest {Math.min(payments.length, 5)}
                  </span> */}
                  {payments.slice(0, 5).map((p, i) => (
                    <div className="dash-row" key={i}>
                      <div>
                        <div className="text-bold">{p.tenant_name}</div>

                        <div className="text-muted">
                          {fmtDate(p.payment_date)}
                          {p.method ? ` · ${p.method}` : ""}
                          {p.payment_type === "deposit" ? " · Deposit" : ""}
                        </div>
                      </div>

                      <span className="text-bold">{money(p.amount)}</span>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
