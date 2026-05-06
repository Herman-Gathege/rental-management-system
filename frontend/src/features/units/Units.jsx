//frontend\src\features\units\Units.jsx 
import { useEffect, useState } from "react";
import { getUnits } from "../../api/units";
import { useProperty } from "../../context/PropertyContext";
import { Link } from "react-router-dom";

export default function Units() {
  const { activeProperty } = useProperty();
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
                {units.map((u) => (
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
                      <Link to={`/owner/units/${u.id}`} className="btn btn-secondary btn-sm">View</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="hidden-desktop properties-cards">
            {units.map((u) => (
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
                <Link to={`/owner/units/${u.id}`} className="btn btn-secondary btn-sm mt-sm">View</Link>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

