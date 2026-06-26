//frontend\src\components\ui\TicketsSummaryCard.jsx
//
// Dashboard ticket summary widget (Sprint 6, Chunk 6d). Drop into any role's
// dashboard with a single import + <TicketsSummaryCard />. Self-contained:
// fetches tickets scoped to the caller (the backend already scopes by role),
// then shows headline counts + a short list of the most urgent open tickets.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTickets } from "../../api/tickets";
import { useAuth } from "../../context/AuthContext";

const OPEN_STATUSES = ["open", "assigned", "in_progress", "waiting"];

function dashboardBase(role) {
  switch ((role || "").toLowerCase()) {
    case "property_manager": return "/manager";
    case "finance":          return "/finance";
    case "tenant":           return "/tenant";
    default:                 return "/owner";
  }
}

const priorityColor = (p) => {
  switch (p) {
    case "critical": return "#ef4444";
    case "high":     return "#f59e0b";
    case "medium":   return "#2563eb";
    default:         return "#6b7280";
  }
};

const fmtShort = (d) =>
  d ? new Date(d).toLocaleDateString("en-GB", { day: "2-digit", month: "short" }) : "";

export default function TicketsSummaryCard() {
  const { user } = useAuth();
  const role = user?.role?.toLowerCase();
  const isTenant = role === "tenant";
  const base = dashboardBase(role);

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTickets()
      .then((data) => setTickets(Array.isArray(data) ? data : []))
      .catch(() => setTickets([]))
      .finally(() => setLoading(false));
  }, []);

  const openTickets = tickets.filter((t) => OPEN_STATUSES.includes(t.status));
  const urgent = openTickets.filter((t) => ["high", "critical"].includes(t.priority));
  const mine = openTickets.filter((t) => t.assigned_to && t.assigned_to === user?.id);

  const priorityRank = { critical: 0, high: 1, medium: 2, low: 3 };
  const topOpen = [...openTickets]
    .sort((a, b) => {
      const pr = (priorityRank[a.priority] ?? 9) - (priorityRank[b.priority] ?? 9);
      if (pr !== 0) return pr;
      return new Date(b.created_at) - new Date(a.created_at);
    })
    .slice(0, 4);

  return (
    <div className="dash-panel mb-md">
      <div className="flex items-center justify-between mb-sm">
        <div className="dash-panel-title">
          {isTenant ? "My Tickets" : "Support Tickets"}
        </div>
        <Link to={`${base}/tickets`} className="btn btn-secondary btn-sm">
          View all
        </Link>
      </div>

      {loading ? (
        <div className="text-muted text-sm">Loading…</div>
      ) : (
        <>
          {/* Headline counts */}
          <div className="dash-grid mb-md">
            <div className="dash-stat">
              <div className="dash-stat-value">{openTickets.length}</div>
              <div className="dash-stat-label">Open</div>
            </div>
            <div className="dash-stat">
              <div className="dash-stat-value" style={{ color: urgent.length ? "#ef4444" : undefined }}>
                {urgent.length}
              </div>
              <div className="dash-stat-label">High / Critical</div>
            </div>
            {!isTenant && (
              <div className="dash-stat">
                <div className="dash-stat-value" style={{ color: mine.length ? "#2563eb" : undefined }}>
                  {mine.length}
                </div>
                <div className="dash-stat-label">Assigned to me</div>
              </div>
            )}
          </div>

          {/* Top open tickets */}
          {topOpen.length === 0 ? (
            <div className="text-muted text-sm">
              {isTenant ? "You have no open tickets." : "No open tickets — all clear."}
            </div>
          ) : (
            topOpen.map((t) => (
              <Link
                key={t.id}
                to={`${base}/tickets/${t.id}`}
                className="dash-row"
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div>
                  <div className="text-bold text-sm">{t.title}</div>
                  <div className="text-xs text-muted">
                    {t.status?.replace(/_/g, " ")}
                    {t.category ? ` · ${t.category.replace(/_/g, " ")}` : ""}
                  </div>
                </div>
                <span
                  className="text-xs"
                  style={{ color: priorityColor(t.priority), fontWeight: 600, whiteSpace: "nowrap" }}
                >
                  {t.priority}
                  {t.created_at ? ` · ${fmtShort(t.created_at)}` : ""}
                </span>
              </Link>
            ))
          )}
        </>
      )}
    </div>
  );
}
