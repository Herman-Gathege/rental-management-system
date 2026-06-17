//frontend/src/features/dashboard/ManagerProperties.jsx
//
// Property Manager — Properties (read-only, Sprint 4.5).
// Lists the properties assigned to this manager via /dashboard/manager/properties.
// Responsive: table on desktop, MobileCardList stacked cards below 768px.

import { useEffect, useState } from "react";
import { getManagerProperties } from "../../api/dashboard";
import MobileCardList from "../../components/ui/MobileCardList";

export default function ManagerProperties() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getManagerProperties();
        if (!active) return;
        setProperties(data);
      } catch (err) {
        if (!active) return;
        setError(err?.response?.data?.detail || "Could not load your properties.");
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
        <div className="dash-panel">Loading your properties…</div>
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

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">Properties</div>

      <div className="dash-panel">
        <div className="dash-panel-title">Assigned Properties</div>
        {properties.length === 0 ? (
          <div className="text-muted">No properties assigned to you yet.</div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="staff-table-wrap hidden-mobile">
              <table className="staff-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>City</th>
                    <th>Address</th>
                  </tr>
                </thead>
                <tbody>
                  {properties.map((p) => (
                    <tr key={p.id}>
                      <td className="text-bold">{p.name}</td>
                      <td>{p.city || "—"}</td>
                      <td>{p.address || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <MobileCardList
              data={properties}
              renderCard={(p, i) => (
                <div className="staff-card" key={p.id || i}>
                  <div className="staff-card-title">{p.name}</div>
                  <div className="staff-card-row">
                    <span>City</span>
                    <span>{p.city || "—"}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Address</span>
                    <span>{p.address || "—"}</span>
                  </div>
                </div>
              )}
            />
          </>
        )}
      </div>
    </div>
  );
}
