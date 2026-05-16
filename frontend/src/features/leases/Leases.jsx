// frontend/src/features/leases/Leases.jsx
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { getLeases } from "../../api/leases";
import { useProperty } from "../../context/PropertyContext";

export default function Leases() {
  const { activeProperty } = useProperty();
  const location = useLocation();

  // Detect if the user came in via /owner/leases/expired
  const isExpiredView = location.pathname.endsWith("/expired");

  const [leases, setLeases] = useState([]);
  const [statusFilter, setStatusFilter] = useState(isExpiredView ? "ended" : "active");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchLeases = async () => {
    try {
      setLoading(true);
      setError("");

      // Build the filters object for getLeases({...})
      const filters = {};
      if (statusFilter) filters.status = statusFilter;
      if (activeProperty?.id) filters.property_id = activeProperty.id;

      const data = await getLeases(filters);
      setLeases(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load leases");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeases();
  }, [statusFilter, activeProperty]);

  // The filter buttons differ depending on the view
  const filterOptions = isExpiredView
    ? ["ended", "terminated"]
    : ["active", "ended", "terminated", ""];

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>{isExpiredView ? "Expired & Terminated Leases" : "Leases"}</h2>
        {!isExpiredView && (
          <Link to="/owner/leases/create" className="btn btn-primary btn-sm">
            + Create Lease
          </Link>
        )}
      </div>

      {/* Status Filter */}
      <div className="flex gap-sm flex-wrap mb-md">
        {filterOptions.map((s) => (
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
        <p>Loading leases...</p>
      ) : error ? (
        <p className="error-text">{error}</p>
      ) : leases.length === 0 ? (
        <div className="empty-state">
          <p>No leases found.</p>
          {!isExpiredView && (
            <>
              <p className="text-muted">Create a lease to assign a tenant to a unit.</p>
              <Link to="/owner/leases/create" className="btn btn-primary">
                Create First Lease
              </Link>
            </>
          )}
        </div>
      ) : (
        <>
          {/* Desktop Table */}
          <div className="properties-table-wrapper hidden-mobile">
            <table className="properties-table">
              <thead>
                <tr>
                  <th>Tenant</th>
                  <th>Unit</th>
                  <th>Property</th>
                  <th>Rent (KES)</th>
                  <th>Start</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {leases.map((l) => (
                  <tr key={l.id}>
                    <td className="prop-name">{l.tenant_name}</td>
                    <td>{l.unit_name}</td>
                    <td>{l.property_name}</td>
                    <td>{Number(l.rent_amount).toLocaleString()}</td>
                    <td>{new Date(l.start_date).toLocaleDateString()}</td>
                    <td>
                      <span
                        className={`status-pill ${
                          l.status === "active"
                            ? "status-ok"
                            : l.status === "terminated"
                            ? "status-owed"
                            : "status-paid"
                        }`}
                      >
                        {l.status}
                      </span>
                    </td>
                    <td>
                      <Link to={`/owner/leases/${l.id}`} className="btn btn-secondary btn-sm">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="hidden-desktop properties-cards">
            {leases.map((l) => (
              <div key={l.id} className="property-card card">
                <div className="property-card-header">
                  <strong>{l.tenant_name}</strong>
                  <span
                    className={`status-pill ${
                      l.status === "active" ? "status-ok" : "status-owed"
                    }`}
                  >
                    {l.status}
                  </span>
                </div>
                <div className="text-sm">
                  {l.unit_name} — {l.property_name}
                </div>
                <div className="text-sm">
                  KES {Number(l.rent_amount).toLocaleString()}/mo
                </div>
                <Link
                  to={`/owner/leases/${l.id}`}
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
