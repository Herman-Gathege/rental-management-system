//frontend/src/features/dashboard/ManagerLeases.jsx
//
// Property Manager — Leases (read-only, Sprint 4.5).
// All leases (any status) in the manager's assigned properties via
// /dashboard/manager/leases.

import { useEffect, useState } from "react";
import { getManagerLeases } from "../../api/dashboard";

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

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">Leases</div>

      <div className="dash-panel">
        <div className="dash-panel-title">Leases in Your Properties</div>
        {leases.length === 0 ? (
          <div className="text-muted">No leases in your properties yet.</div>
        ) : (
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
              </tr>
            </thead>
            <tbody>
              {leases.map((l, i) => (
                <tr key={l.id || i}>
                  <td className="text-bold">{l.tenant_name || "—"}</td>
                  <td>{l.property_name}</td>
                  <td>{l.unit_name}</td>
                  <td>{l.status}</td>
                  <td>{fmtDate(l.start_date)}</td>
                  <td>{fmtDate(l.end_date)}</td>
                  <td>{money(l.rent_amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
