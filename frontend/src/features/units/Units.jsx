//frontend\src\features\units\Units.jsx
import { useEffect, useState } from "react";
import { getUnits } from "../../api/units";
import { useProperty } from "../../context/PropertyContext";
import { Link, useLocation } from "react-router-dom";

export default function Units() {
  const { activeProperty } = useProperty();
  const location = useLocation();

  // The "Vacant Units" menu points at /owner/units/vacant; that just preselects
  // the Vacant filter on this same page. "All Units" (/owner/units) defaults to
  // All. Either way the user can switch between All / Occupied / Vacant.
  const isVacantRoute = location.pathname.endsWith("/vacant");

  const [units, setUnits] = useState([]);
  const [statusFilter, setStatusFilter] = useState(isVacantRoute ? "vacant" : "");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Keep the filter in sync if the user navigates between the two menu items
  // without a full remount.
  useEffect(() => {
    setStatusFilter(isVacantRoute ? "vacant" : "");
  }, [isVacantRoute]);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await getUnits(activeProperty?.id || null);
        setUnits(data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load units");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [activeProperty]);

  if (loading) return <p>Loading units...</p>;
  if (error) return <p className="error-text">{error}</p>;

  const visible = statusFilter
    ? units.filter((u) => u.occupancy_status === statusFilter)
    : units;

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Units {activeProperty ? `— ${activeProperty.name}` : ""}</h2>
        <Link to="/owner/units/add" className="btn btn-primary btn-sm">
          + Add Unit
        </Link>
      </div>

      {units.length === 0 ? (
        <div className="empty-state">
          <p>No units yet.</p>
          <p className="text-muted">Add units to start tracking occupancy and leases.</p>
          <Link to="/owner/units/add" className="btn btn-primary">Add First Unit</Link>
        </div>
      ) : (
        <>
          {/* Status filter */}
          <div className="flex gap-sm flex-wrap">
            {[
              { key: "", label: "All" },
              { key: "occupied", label: "Occupied" },
              { key: "vacant", label: "Vacant" },
            ].map((f) => (
              <button
                key={f.key}
                className={`btn btn-sm ${statusFilter === f.key ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setStatusFilter(f.key)}
              >
                {f.label}
              </button>
            ))}
          </div>

          {visible.length === 0 ? (
            <p className="text-muted">
              No {statusFilter || ""} units{statusFilter ? "" : ""}.
            </p>
          ) : (
            <>
              {/* Desktop Table */}
              <div className="properties-table-wrapper hidden-mobile">
                <table className="properties-table">
                  <thead>
                    <tr>
                      <th>Unit</th>
                      <th>Property</th>
                      <th>Rent (KES)</th>
                      <th>Status</th>
                      <th>Tenant</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((u) => (
                      <tr key={u.id}>
                        <td className="prop-name">{u.name}</td>
                        <td>{u.property_name}</td>
                        <td>{Number(u.rent_amount).toLocaleString()}</td>
                        <td>
                          <span className={`status-pill ${u.occupancy_status === "occupied" ? "status-ok" : "status-owed"}`}>
                            {u.occupancy_status}
                          </span>
                        </td>
                        <td>{u.tenant_name || "—"}</td>
                        <td>
                          <Link
                            to={`/owner/units/${u.id}`}
                            state={{ unit: u }}
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

              {/* Mobile Cards */}
              <div className="hidden-desktop properties-cards">
                {visible.map((u) => (
                  <div key={u.id} className="property-card card">
                    <div className="property-card-header">
                      <strong>{u.name}</strong>
                      <span className={`status-pill ${u.occupancy_status === "occupied" ? "status-ok" : "status-owed"}`}>
                        {u.occupancy_status}
                      </span>
                    </div>
                    <div className="text-sm">{u.property_name}</div>
                    <div className="text-sm">KES {Number(u.rent_amount).toLocaleString()}</div>
                    {u.tenant_name && <div className="text-sm text-muted">Tenant: {u.tenant_name}</div>}
                    <Link
                      to={`/owner/units/${u.id}`}
                      state={{ unit: u }}
                      className="btn btn-secondary btn-sm mt-sm"
                    >
                      View
                    </Link>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </section>
  );
}

