//frontend/src/features/dashboard/ManagerLeases.jsx
//
// Property Manager — Leases (Sprint 4.5).
// All leases (any status) in the manager's assigned properties via
// /dashboard/manager/leases. Filters to the navbar switcher's property
// (All = every assigned property). Responsive table + MobileCardList.
// Each lease links to its detail page (/manager/leases/:id) where the PM can
// view the lease and conduct/view inspections.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getManagerLeases } from "../../api/dashboard";
import { useProperty } from "../../context/PropertyContext";
import MobileCardList from "../../components/ui/MobileCardList";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });

const fmtDate = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "—";

export default function ManagerLeases() {
  const { activeProperty } = useProperty();
  const activePropertyId = activeProperty?.id || null;

  const [leases, setLeases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getManagerLeases();
        if (!active) return;
        setLeases(data);
      } catch (err) {
        if (!active) return;
        setError(err?.response?.data?.detail || "Could not load your leases.");
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
        <div className="dash-panel">Loading your leases…</div>
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

  const visible = leases.filter(
    (l) => !activePropertyId || l.property_id === activePropertyId
  );

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Leases{activeProperty ? ` — ${activeProperty.name}` : ""}
      </div>

      <div className="dash-panel">
        <div className="dash-panel-title">Leases in Your Properties</div>
        {visible.length === 0 ? (
          <div className="text-muted">No leases in this view yet.</div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="staff-table-wrap hidden-mobile">
              <table className="staff-table">
                <thead>
                  <tr>
                    <th>Tenant</th>
                    <th>Property</th>
                    <th>Unit</th>
                    <th>Status</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>Rent</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((l, i) => (
                    <tr key={l.id || i}>
                      <td className="text-bold">{l.tenant_name || "—"}</td>
                      <td>{l.property_name}</td>
                      <td>{l.unit_name}</td>
                      <td>{l.status}</td>
                      <td>{fmtDate(l.start_date)}</td>
                      <td>{fmtDate(l.end_date)}</td>
                      <td>{money(l.rent_amount)}</td>
                      <td>
                        {l.id && (
                          <Link
                            to={`/manager/leases/${l.id}`}
                            className="btn btn-primary btn-sm"
                          >
                            View
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <MobileCardList
              data={visible}
              renderCard={(l, i) => (
                <div className="staff-card" key={l.id || i}>
                  <div className="staff-card-title">{l.tenant_name || "—"}</div>
                  <div className="staff-card-row">
                    <span>Property</span>
                    <span>{l.property_name}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Unit</span>
                    <span>{l.unit_name}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Status</span>
                    <span>{l.status}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Start</span>
                    <span>{fmtDate(l.start_date)}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>End</span>
                    <span>{fmtDate(l.end_date)}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Rent</span>
                    <span>{money(l.rent_amount)}</span>
                  </div>
                  {l.id && (
                    <Link
                      to={`/manager/leases/${l.id}`}
                      className="btn btn-primary btn-sm mt-sm"
                    >
                      View Lease
                    </Link>
                  )}
                </div>
              )}
            />
          </>
        )}
      </div>
    </div>
  );
}
