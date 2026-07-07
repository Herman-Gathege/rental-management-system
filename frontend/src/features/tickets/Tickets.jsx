//frontend\src\features\tickets\Tickets.jsx
//
// Ticket list (Sprint 6). Shared by owner/finance/manager/tenant — the backend
// scopes what each role sees. Mirrors the Expenses/Leases list pattern:
// filter bar, desktop table, mobile cards, role-aware "+ Create" button.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTickets } from "../../api/tickets";
import { useAuth } from "../../context/AuthContext";
import { useProperty } from "../../context/PropertyContext";
import Pagination from "../../components/Pagination";
import useServerPagination from "../../hooks/useServerPagination";

const STATUSES = ["", "open", "assigned", "in_progress", "waiting", "resolved", "closed"];
const PRIORITIES = ["", "low", "medium", "high", "critical"];

const PER_PAGE = 25;

const statusClass = (s) => {
  switch (s) {
    case "closed":      return "status-paid";
    case "resolved":    return "status-ok";
    case "in_progress": return "status-ok";
    case "open":        return "status-owed";
    default:            return "status-owed";
  }
};

const priorityColor = (p) => {
  switch (p) {
    case "critical": return "#ef4444";
    case "high":     return "#f59e0b";
    case "medium":   return "#2563eb";
    default:         return "#6b7280";
  }
};

function dashboardBase(role) {
  switch (role) {
    case "property_manager": return "/manager";
    case "finance":          return "/finance";
    case "tenant":           return "/tenant";
    default:                 return "/owner";
  }
}

const fmtDate = (d) =>
  d ? new Date(d).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : "—";

export default function Tickets() {
  const { user } = useAuth();
  const { activeProperty } = useProperty();
  const role = user?.role?.toLowerCase();
  const base = dashboardBase(role);
  const canCreate = role !== "finance"; // Finance responds but doesn't create

  const [tickets, setTickets] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const pg = useServerPagination(PER_PAGE);
  const { page, setPage, total, setTotal, totalPages, limit, offset, reset } = pg;

  const fetchTickets = async () => {
    try {
      setLoading(true);
      setError("");
      const filters = { limit, offset };
      if (statusFilter) filters.status = statusFilter;
      if (priorityFilter) filters.priority = priorityFilter;
      if (activeProperty?.id) filters.property_id = activeProperty.id;
      const res = await getTickets(filters);
      setTickets(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load tickets");
    } finally {
      setLoading(false);
    }
  };

  // Reset to page 1 when any filter changes.
  useEffect(() => {
    reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, priorityFilter, activeProperty]);

  useEffect(() => {
    fetchTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, priorityFilter, activeProperty, page]);

  const showingFrom = total === 0 ? 0 : offset + 1;
  const showingTo = Math.min(offset + limit, total);

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Support Tickets</h2>
        {canCreate && (
          <Link to={`${base}/tickets/create`} className="btn btn-primary btn-sm">
            + New Ticket
          </Link>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-sm flex-wrap mb-md">
        {STATUSES.map((s) => (
          <button
            key={s || "all"}
            className={`btn btn-sm ${statusFilter === s ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setStatusFilter(s)}
          >
            {s ? s.replace("_", " ") : "All"}
          </button>
        ))}
      </div>

      <div className="flex gap-sm flex-wrap mb-md">
        {PRIORITIES.map((p) => (
          <button
            key={p || "any"}
            className={`btn btn-sm ${priorityFilter === p ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setPriorityFilter(p)}
          >
            {p || "Any priority"}
          </button>
        ))}
      </div>

      {loading ? (
        <p>Loading tickets...</p>
      ) : error ? (
        <p className="error-text">{error}</p>
      ) : total === 0 ? (
        <div className="empty-state">
          <p>No tickets found.</p>
          {canCreate && (
            <>
              <p className="text-muted">Report an issue to get started.</p>
              <Link to={`${base}/tickets/create`} className="btn btn-primary">
                Report an Issue
              </Link>
            </>
          )}
        </div>
      ) : (
        <>
          <div className="text-sm text-muted mb-sm">
            Showing {showingFrom}–{showingTo} of {total}
          </div>

          {/* Desktop table */}
          <div className="properties-table-wrapper hidden-mobile">
            <table className="properties-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Property</th>
                  <th>Status</th>
                  <th>Opened</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
                  <tr key={t.id}>
                    <td className="prop-name">{t.title}</td>
                    <td>{t.category?.replace(/_/g, " ") || "—"}</td>
                    <td>
                      <span style={{ color: priorityColor(t.priority), fontWeight: 600 }}>
                        {t.priority || "—"}
                      </span>
                    </td>
                    <td>{t.property_name || "—"}</td>
                    <td>
                      <span className={`status-pill ${statusClass(t.status)}`}>
                        {t.status?.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td>{fmtDate(t.opened_at || t.created_at)}</td>
                    <td>
                      <Link
                        to={`${base}/tickets/${t.id}`}
                        className="btn btn-secondary btn-sm"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="hidden-desktop properties-cards">
            {tickets.map((t) => (
              <div key={t.id} className="property-card card">
                <div className="property-card-header">
                  <strong>{t.title}</strong>
                  <span className={`status-pill ${statusClass(t.status)}`}>
                    {t.status?.replace(/_/g, " ")}
                  </span>
                </div>
                <div className="text-sm">
                  {t.category?.replace(/_/g, " ") || "—"}
                  {t.property_name ? ` · ${t.property_name}` : ""}
                </div>
                <div className="text-sm" style={{ color: priorityColor(t.priority) }}>
                  {t.priority} priority
                </div>
                <div className="text-sm text-muted">{fmtDate(t.opened_at || t.created_at)}</div>
                <Link
                  to={`${base}/tickets/${t.id}`}
                  className="btn btn-secondary btn-sm mt-sm"
                >
                  View
                </Link>
              </div>
            ))}
          </div>

          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </>
      )}
    </section>
  );
}
