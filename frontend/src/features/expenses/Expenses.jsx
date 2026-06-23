//frontend\src\features\expenses\Expenses.jsx
//
// Expense list (Sprint 5). Shared by owner/finance/manager — the backend scopes
// what each role sees (Landlord/Finance org-wide, PM their assigned properties).
// Mirrors the Leases list: status filter + active-property filter, desktop table
// + mobile cards. Links/create are role-aware via the user's dashboard prefix.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getExpenses } from "../../api/expenses";
import { useAuth } from "../../context/AuthContext";
import { useProperty } from "../../context/PropertyContext";

const STATUS_FILTERS = ["", "draft", "submitted", "approved", "paid"];

const money = (n) => "KES " + Number(n || 0).toLocaleString();

const fmtDate = (d) => (d ? new Date(d).toLocaleDateString() : "—");

// Map an expense status to one of the existing status-pill modifier classes.
const statusClass = (status) => {
  switch (status) {
    case "paid":
      return "status-paid";
    case "approved":
      return "status-ok";
    case "draft":
    case "submitted":
    default:
      return "status-owed";
  }
};

function dashboardBase(role) {
  switch (role) {
    case "property_manager":
      return "/manager";
    case "finance":
      return "/finance";
    default:
      return "/owner";
  }
}

export default function Expenses() {
  const { user } = useAuth();
  const { activeProperty } = useProperty();

  const role = user?.role?.toLowerCase();
  const base = dashboardBase(role);

  const [expenses, setExpenses] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchExpenses = async () => {
    try {
      setLoading(true);
      setError("");
      const filters = {};
      if (statusFilter) filters.status = statusFilter;
      if (activeProperty?.id) filters.property_id = activeProperty.id;
      const data = await getExpenses(filters);
      setExpenses(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load expenses");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExpenses();
  }, [statusFilter, activeProperty]);

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Expenses</h2>
        <Link to={`${base}/expenses/create`} className="btn btn-primary btn-sm">
          + Add Expense
        </Link>
      </div>

      {/* Status filter */}
      <div className="flex gap-sm flex-wrap mb-md">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s || "all"}
            className={`btn btn-sm ${statusFilter === s ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setStatusFilter(s)}
          >
            {s || "All"}
          </button>
        ))}
      </div>

      {loading ? (
        <p>Loading expenses...</p>
      ) : error ? (
        <p className="error-text">{error}</p>
      ) : expenses.length === 0 ? (
        <div className="empty-state">
          <p>No expenses found.</p>
          <p className="text-muted">
            Record an expense to start tracking money going out.
          </p>
          <Link to={`${base}/expenses/create`} className="btn btn-primary">
            Add First Expense
          </Link>
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="properties-table-wrapper hidden-mobile">
            <table className="properties-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Title</th>
                  <th>Property</th>
                  <th>Category</th>
                  <th>Vendor</th>
                  <th>Amount (KES)</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((e) => (
                  <tr key={e.id}>
                    <td>{fmtDate(e.expense_date)}</td>
                    <td className="prop-name">{e.title}</td>
                    <td>{e.property_name}</td>
                    <td>{e.category_name || "—"}</td>
                    <td>{e.vendor_name || "—"}</td>
                    <td>{Number(e.amount).toLocaleString()}</td>
                    <td>
                      <span className={`status-pill ${statusClass(e.status)}`}>
                        {e.status}
                      </span>
                    </td>
                    <td>
                      <Link
                        to={`${base}/expenses/${e.id}`}
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
            {expenses.map((e) => (
              <div key={e.id} className="property-card card">
                <div className="property-card-header">
                  <strong>{e.title}</strong>
                  <span className={`status-pill ${statusClass(e.status)}`}>
                    {e.status}
                  </span>
                </div>
                <div className="text-sm">{e.property_name}</div>
                <div className="text-sm text-muted">
                  {e.category_name || "—"}
                  {e.vendor_name ? ` · ${e.vendor_name}` : ""}
                </div>
                <div className="text-sm">{money(e.amount)}</div>
                <div className="text-sm text-muted">{fmtDate(e.expense_date)}</div>
                <Link
                  to={`${base}/expenses/${e.id}`}
                  className="btn btn-secondary btn-sm mt-sm"
                >
                  View
                </Link>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
