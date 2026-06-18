//frontend/src/features/dashboard/ManagerTenants.jsx
//
// Property Manager — Tenants (read-only, Sprint 4.5).
// Active tenancies in the manager's assigned properties via
// /dashboard/manager/tenants. Filters to the navbar switcher's property
// (All = every assigned property). Responsive table + MobileCardList.

import { useEffect, useState } from "react";
import { getManagerTenants } from "../../api/dashboard";
import { useProperty } from "../../context/PropertyContext";
import MobileCardList from "../../components/ui/MobileCardList";

export default function ManagerTenants() {
  const { activeProperty } = useProperty();
  const activePropertyId = activeProperty?.id || null;

  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getManagerTenants();
        if (!active) return;
        setTenants(data);
      } catch (err) {
        if (!active) return;
        setError(err?.response?.data?.detail || "Could not load your tenants.");
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
        <div className="dash-panel">Loading your tenants…</div>
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

  const visible = tenants.filter(
    (t) => !activePropertyId || t.property_id === activePropertyId
  );

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Tenants{activeProperty ? ` — ${activeProperty.name}` : ""}
      </div>

      <div className="dash-panel">
        <div className="dash-panel-title">Tenants in Your Properties</div>
        {visible.length === 0 ? (
          <div className="text-muted">No active tenants in this view yet.</div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="staff-table-wrap hidden-mobile">
              <table className="staff-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Property</th>
                    <th>Unit</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((t, i) => (
                    <tr key={(t.id || "") + i}>
                      <td className="text-bold">{t.full_name}</td>
                      <td>{t.phone || "—"}</td>
                      <td>{t.email || "—"}</td>
                      <td>{t.property_name}</td>
                      <td>{t.unit_name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <MobileCardList
              data={visible}
              renderCard={(t, i) => (
                <div className="staff-card" key={(t.id || "") + i}>
                  <div className="staff-card-title">{t.full_name}</div>
                  <div className="staff-card-row">
                    <span>Phone</span>
                    <span>{t.phone || "—"}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Email</span>
                    <span>{t.email || "—"}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Property</span>
                    <span>{t.property_name}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Unit</span>
                    <span>{t.unit_name}</span>
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
