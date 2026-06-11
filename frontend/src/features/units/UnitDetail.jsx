//frontend\src\features\units\UnitDetail.jsx
//
// Read-only unit detail (Option A fix for the blank "View" page).
// Reached from the Units list "View" button, which passes the row's data via
// router state for an instant, rich render. On a direct URL hit (no state) it
// falls back to getUnit(id) for the unit's core fields; occupancy/tenant come
// from the list row, so those show "—" on a cold direct load.

import { useEffect, useState } from "react";
import { useParams, useLocation, Link } from "react-router-dom";
import { getUnit } from "../../api/units";

export default function UnitDetail() {
  const { unitId } = useParams();
  const location = useLocation();
  const passed = location.state?.unit || null;

  const [unit, setUnit] = useState(passed);
  const [loading, setLoading] = useState(!passed);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getUnit(unitId);
        if (!active) return;
        // Keep the enriched fields the list passed (occupancy_status,
        // tenant_name, property_name) and layer the canonical unit fields
        // from the API on top.
        setUnit((prev) => ({ ...(prev || {}), ...data }));
      } catch (err) {
        if (!active) return;
        if (!passed) setError(err.response?.data?.detail || "Failed to load unit");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [unitId]);

  if (loading) return <p>Loading unit...</p>;
  if (error) return <p className="error-text">{error}</p>;
  if (!unit) return <p className="text-muted">Unit not found.</p>;

  const rent =
    unit.rent_amount != null ? Number(unit.rent_amount).toLocaleString() : "—";
  const statusPill =
    unit.occupancy_status === "occupied" ? "status-ok" : "status-owed";

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>
          Unit {unit.name}
          {unit.property_name ? ` — ${unit.property_name}` : ""}
        </h2>
        <div className="flex gap-sm">
          <Link to="/owner/units" className="btn btn-secondary btn-sm">
            Back to Units
          </Link>
          <Link to={`/owner/units/${unitId}/edit`} className="btn btn-primary btn-sm">
            Edit
          </Link>
        </div>
      </div>

      <div className="card">
        <div className="property-info-grid">
          <div className="info-item">
            <label>Property</label>
            <span>{unit.property_name || "—"}</span>
          </div>
          <div className="info-item">
            <label>Rent (KES)</label>
            <span>{rent}</span>
          </div>
          <div className="info-item">
            <label>Status</label>
            <span>
              {unit.occupancy_status ? (
                <span className={`status-pill ${statusPill}`}>
                  {unit.occupancy_status}
                </span>
              ) : (
                "—"
              )}
            </span>
          </div>
          <div className="info-item">
            <label>Current Tenant</label>
            <span>{unit.tenant_name || "—"}</span>
          </div>
        </div>
      </div>
    </section>
  );
}
