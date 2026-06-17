//frontend/src/features/dashboard/StaffDashboard.jsx
//
// Property Manager dashboard (Sprint 4.5).
// Pulls /dashboard/manager/summary + /dashboard/manager/properties and shows
// occupancy/lease/tenant stats for the properties assigned to this manager.
// A manager with no assignments yet sees zeros + a hint (a valid state, not
// an error).

import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getManagerSummary, getManagerProperties } from "../../api/dashboard";
import NotificationsCard from "../../components/ui/NotificationsCard";

export default function StaffDashboard() {
  const { user } = useAuth();

  const [summary, setSummary] = useState(null);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const [s, p] = await Promise.all([
          getManagerSummary(),
          getManagerProperties(),
        ]);
        if (!active) return;
        setSummary(s);
        setProperties(p);
      } catch (err) {
        if (!active) return;
        setError(
          err?.response?.data?.detail || "Could not load your dashboard."
        );
      } finally {
        if (active) setLoading(false);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, []);

  const displayName = user?.full_name || user?.email || "there";

  const cards = summary
    ? [
        { label: "Properties", value: summary.properties },
        { label: "Units", value: summary.units },
        { label: "Occupied Units", value: summary.occupied_units },
        { label: "Vacant Units", value: summary.vacant_units },
        { label: "Active Leases", value: summary.active_leases },
        { label: "Tenants", value: summary.tenants },
      ]
    : [];

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Welcome, <span className="company-blue text-bold">{displayName}</span> 👋
      </div>

      {loading && <div className="dash-panel">Loading your dashboard…</div>}

      {!loading && error && (
        <div className="info-banner-warning">
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && summary && (
        <>
          {summary.properties === 0 && (
            <div className="hint mb-md">
              No properties are assigned to you yet. Once a landlord assigns you
              to properties, your stats will appear here.
            </div>
          )}

          <div className="dash-grid mb-md">
            {cards.map((c) => (
              <div className="dash-stat" key={c.label}>
                <div className="dash-stat-value">{c.value}</div>
                <div className="dash-stat-label">{c.label}</div>
              </div>
            ))}
          </div>

          <NotificationsCard />

          <div className="dash-panel">
            <div className="dash-panel-title">Your Properties</div>
            {properties.length === 0 ? (
              <div className="text-muted">No properties assigned.</div>
            ) : (
              properties.map((p) => (
                <div className="dash-row" key={p.id}>
                  <span className="text-bold">{p.name}</span>
                  <span className="text-muted">{p.city}</span>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
