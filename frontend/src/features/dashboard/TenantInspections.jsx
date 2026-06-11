//frontend/src/features/dashboard/TenantInspections.jsx
//
// Tenant "Lease Checklist" page (Sprint 4.5 tenant portal).
// Read-only view of the tenant's move-in and move-out inspections across all
// their leases, filtered by the active property switcher like the other tenant
// pages. Shows item conditions, comments, photos, and — for move-out — any
// deposit deductions. No internal notes or inspector identity (handled in the
// backend serializer).

import { useEffect, useState } from "react";
import { getTenantInspections } from "../../api/dashboard";
import { useTenantProperty } from "../../context/TenantPropertyContext";

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

const TYPE_LABEL = { move_in: "Move-In", move_out: "Move-Out" };

// "needs_repair" -> "Needs Repair", "working" -> "Working"
const condLabel = (c) =>
  c ? c.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase()) : "—";

export default function TenantInspections() {
  const tp = useTenantProperty() || {};
  const activePropertyId = tp.activePropertyId || null;
  const activeProperty = tp.activeProperty || null;

  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getTenantInspections();
        if (!active) return;
        setInspections(data);
      } catch (err) {
        if (!active) return;
        setError(
          err?.response?.data?.detail || "Could not load your inspections."
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

  if (loading) {
    return (
      <div className="p-6">
        <div className="dash-panel">Loading your checklist…</div>
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

  const visible = inspections.filter(
    (i) => !activePropertyId || i.property_id === activePropertyId
  );

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Lease Checklist{activeProperty ? ` — ${activeProperty.name}` : ""}
      </div>

      {visible.length === 0 ? (
        <div className="dash-panel">
          <div className="text-muted">No inspections on record yet.</div>
        </div>
      ) : (
        visible.map((insp) => {
          const isMoveOut = insp.inspection_type === "move_out";
          const where =
            [insp.property_name, insp.unit_name].filter(Boolean).join(" · ") ||
            "Lease";

          return (
            <div className="dash-panel mb-md" key={insp.id}>
              <div className="flex items-center justify-between mb-sm">
                <div>
                  <div className="dash-panel-title">
                    {TYPE_LABEL[insp.inspection_type] || insp.inspection_type}{" "}
                    Inspection — {where}
                  </div>
                  <div className="text-sm text-muted">
                    {insp.inspection_date
                      ? fmtDate(insp.inspection_date)
                      : "Not yet dated"}
                  </div>
                </div>
                <span className={`role-badge inspection-status-${insp.status}`}>
                  {insp.status}
                </span>
              </div>

              <table className="staff-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Condition</th>
                    <th>Comments</th>
                    {isMoveOut && <th>Deduction</th>}
                    <th>Photos</th>
                  </tr>
                </thead>
                <tbody>
                  {insp.items.map((it) => (
                    <tr key={it.id}>
                      <td className="text-bold">{it.item_name}</td>
                      <td>
                        <span
                          className={`condition-badge condition-${
                            it.condition || ""
                          }`}
                        >
                          {condLabel(it.condition)}
                        </span>
                      </td>
                      <td>{it.comments || "—"}</td>
                      {isMoveOut && (
                        <td>
                          {it.deduction_amount
                            ? money(it.deduction_amount)
                            : "—"}
                        </td>
                      )}
                      <td>
                        {it.photo_urls.length === 0 ? (
                          "—"
                        ) : (
                          <div className="inspection-photos-grid">
                            {it.photo_urls.map((url) => (
                              <a
                                key={url}
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inspection-photo-thumb"
                              >
                                <img src={url} alt="Inspection" />
                              </a>
                            ))}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {isMoveOut && (
                <div className="text-muted mt-md">
                  Total deductions:{" "}
                  <span className="text-bold">
                    {money(insp.total_deduction_amount)}
                  </span>
                </div>
              )}

              {insp.status === "signed" && insp.tenant_signed_name && (
                <div className="text-sm text-muted mt-sm">
                  Signed by {insp.tenant_signed_name}
                  {insp.tenant_signed_at
                    ? ` on ${fmtDate(insp.tenant_signed_at)}`
                    : ""}
                  .
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}
