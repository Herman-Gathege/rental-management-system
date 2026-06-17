//frontend/src/features/dashboard/ManagerUnits.jsx
//
// Property Manager — Units (read-only, Sprint 4.5).
// Units across the manager's assigned properties, with occupancy + current
// tenant, via /dashboard/manager/units.
// Responsive: table on desktop, MobileCardList stacked cards below 768px.

import { useEffect, useState } from "react";
import { getManagerUnits } from "../../api/dashboard";
import MobileCardList from "../../components/ui/MobileCardList";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });

export default function ManagerUnits() {
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getManagerUnits();
        if (!active) return;
        setUnits(data);
      } catch (err) {
        if (!active) return;
        setError(err?.response?.data?.detail || "Could not load your units.");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <div className="dash-panel">Loading your units…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="info-banner-warning">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const occupied = units.filter((u) => u.status === "occupied").length;

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">Units</div>

      <div className="dash-panel">
        <div className="dash-panel-title">Units in Your Properties</div>
        {units.length === 0 ? (
          <div className="text-muted">No units in your properties yet.</div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="staff-table-wrap hidden-mobile">
              <table className="staff-table">
                <thead>
                  <tr>
                    <th>Property</th>
                    <th>Unit</th>
                    <th>Status</th>
                    <th>Tenant</th>
                    <th>Rent</th>
                  </tr>
                </thead>
                <tbody>
                  {units.map((u, i) => (
                    <tr key={u.id || i}>
                      <td>{u.property_name}</td>
                      <td className="text-bold">{u.name}</td>
                      <td>{u.status}</td>
                      <td>{u.tenant_name || "—"}</td>
                      <td>{money(u.rent_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <MobileCardList
              data={units}
              renderCard={(u, i) => (
                <div className="staff-card" key={u.id || i}>
                  <div className="staff-card-title">{u.name}</div>
                  <div className="staff-card-row">
                    <span>Property</span>
                    <span>{u.property_name}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Status</span>
                    <span>{u.status}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Tenant</span>
                    <span>{u.tenant_name || "—"}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Rent</span>
                    <span>{money(u.rent_amount)}</span>
                  </div>
                </div>
              )}
            />

            <div className="text-muted mt-md">
              {units.length} units · <span className="text-bold">{occupied}</span> occupied
            </div>
          </>
        )}
      </div>
    </div>
  );
}
