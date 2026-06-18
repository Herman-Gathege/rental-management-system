//frontend/src/features/dashboard/TenantInspections.jsx
//
// Tenant "Lease Checklist" page (Sprint 4.5 tenant portal).
// Read-only view of the tenant's move-in and move-out inspections across all
// their leases, filtered by the active property switcher like the other tenant
// pages. Shows item conditions, comments, photos, and — for move-out — any
// deposit deductions. No internal notes or inspector identity.
// Responsive: each inspection's item table -> MobileCardList cards below 768px.
//
// Each inspection links to the shared ConductInspection page:
//   - a DRAFT move-in  -> "Conduct" (the tenant may fill and sign it)
//   - anything else     -> "View"    (read-only; move-out is owner/PM-only)

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTenantInspections } from "../../api/dashboard";
import { useTenantProperty } from "../../context/TenantPropertyContext";
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

const TYPE_LABEL = { move_in: "Move-In", move_out: "Move-Out" };

// "needs_repair" -> "Needs Repair", "working" -> "Working"
const condLabel = (c) =>
  c ? c.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase()) : "—";

// Photo thumbnails (shared by table cell + mobile card).
const Photos = ({ urls }) =>
  !urls || urls.length === 0 ? (
    "—"
  ) : (
    <div className="inspection-photos-grid">
      {urls.map((url) => (
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
  );

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

          // A tenant may fill a draft move-in; everything else is view-only.
          const canConduct =
            insp.status === "draft" && insp.inspection_type === "move_in";

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
                <div className="flex items-center gap-sm">
                  <span className={`role-badge inspection-status-${insp.status}`}>
                    {insp.status}
                  </span>
                  <Link
                    to={`/tenant/leases/${insp.lease_id}/inspections/${insp.id}`}
                    className="btn btn-primary btn-sm"
                  >
                    {canConduct ? "Conduct" : "View"}
                  </Link>
                </div>
              </div>

              {/* Desktop table */}
              <div className="staff-table-wrap hidden-mobile">
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
                          <Photos urls={it.photo_urls} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile cards */}
              <MobileCardList
                data={insp.items}
                renderCard={(it) => (
                  <div className="staff-card" key={it.id}>
                    <div className="staff-card-title">{it.item_name}</div>
                    <div className="staff-card-row">
                      <span>Condition</span>
                      <span
                        className={`condition-badge condition-${
                          it.condition || ""
                        }`}
                      >
                        {condLabel(it.condition)}
                      </span>
                    </div>
                    <div className="staff-card-row">
                      <span>Comments</span>
                      <span>{it.comments || "—"}</span>
                    </div>
                    {isMoveOut && (
                      <div className="staff-card-row">
                        <span>Deduction</span>
                        <span>
                          {it.deduction_amount
                            ? money(it.deduction_amount)
                            : "—"}
                        </span>
                      </div>
                    )}
                    {it.photo_urls && it.photo_urls.length > 0 && (
                      <div className="mt-sm">
                        <div className="text-sm text-muted mb-sm">Photos</div>
                        <Photos urls={it.photo_urls} />
                      </div>
                    )}
                  </div>
                )}
              />

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
