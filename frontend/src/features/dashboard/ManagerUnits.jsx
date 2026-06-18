//frontend/src/features/dashboard/ManagerUnits.jsx
//
// Property Manager — Units (read-only, Sprint 4.5).
// Units across the manager's assigned properties, with occupancy + current
// tenant, via /dashboard/manager/units.
// Filters to the property chosen in the navbar switcher (All = every assigned
// property). Responsive: table on desktop, MobileCardList cards below 768px.

import { useEffect, useState } from "react";
import { getManagerUnits } from "../../api/dashboard";
import { useProperty } from "../../context/PropertyContext";
import MobileCardList from "../../components/ui/MobileCardList";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });

export default function ManagerUnits() {
  const { activeProperty } = useProperty();
  const activePropertyId = activeProperty?.id || null;

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

  const visible = units.filter(
    (u) => !activePropertyId || u.property_id === activePropertyId
  );
  const occupied = visible.filter((u) => u.status === "occupied").length;

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Units{activeProperty ? ` — ${activeProperty.name}` : ""}
      </div>

      <div className="dash-panel">
        <div className="dash-panel-title">Units in Your Properties</div>
        {visible.length === 0 ? (
          <div className="text-muted">No units in this view yet.</div>
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
                  {visible.map((u, i) => (
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
              data={visible}
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
              {visible.length} units · <span className="text-bold">{occupied}</span> occupied
            </div>
          </>
        )}
      </div>
    </div>
  );
}
