//frontend/src/features/dashboard/TenantLease.jsx
//
// Tenant "My Lease" page (Sprint 4.5 tenant portal, multi-lease + switcher).
// Renders one card per lease, filtered to the property chosen in the tenant
// property switcher (or all). The top section shows the account standing for
// whatever is in view (a single property, or everything).
// Responsive: per-lease details render as label/value rows (no wide table).

import { useEffect, useState } from "react";
import { getTenantDashboard } from "../../api/dashboard";
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

// Turn a signed balance into display text + a colour class.
const fmtBalance = (balance) => {
  if (balance < 0) return { text: money(-balance) + " credit", cls: "balance-credit" };
  if (balance > 0) return { text: money(balance) + " due", cls: "balance-late" };
  return { text: money(0), cls: "" };
};

export default function TenantLease() {
  const tp = useTenantProperty() || {};
  const activePropertyId = tp.activePropertyId || null;
  const activeProperty = tp.activeProperty || null;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const d = await getTenantDashboard();
        if (!active) return;
        setData(d);
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

  const allLeases = Array.isArray(data?.leases) ? data.leases : [];

  // Fallback to the single primary lease if `leases` isn't present.
  const sourceLeases =
    allLeases.length > 0
      ? allLeases
      : data?.lease
      ? [
          {
            ...data.lease,
            unit_name: data?.unit?.name || null,
            property_name: null,
            property_id: null,
            balance: data?.balance,
          },
        ]
      : [];

  // Filter to the chosen property (or all).
  const leases = sourceLeases.filter(
    (l) => !activePropertyId || l.property_id === activePropertyId
  );

  const balanceSum = leases.reduce((sum, l) => sum + Number(l.balance || 0), 0);
  const overall = fmtBalance(balanceSum);

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        {leases.length > 1 ? "My Leases" : "My Lease"}
        {activeProperty ? ` — ${activeProperty.name}` : ""}
      </div>

      {/* Account standing for whatever is in view */}
      <div className="dash-grid mb-md">
        <div className="dash-stat">
          <div className="dash-stat-value">{leases.length}</div>
          <div className="dash-stat-label">
            {leases.length === 1 ? "Lease" : "Leases"}
          </div>
        </div>
        <div className="dash-stat">
          <div
            className={
              "dash-stat-value dash-stat-money" +
              (overall.cls ? " " + overall.cls : "")
            }
          >
            {overall.text}
          </div>
          <div className="dash-stat-label">
            {activeProperty ? "Account Balance" : "Account Balance (all leases)"}
          </div>
        </div>
      </div>

      {leases.length === 0 ? (
        <div className="dash-panel">
          <div className="text-muted">No lease on file for this view.</div>
        </div>
      ) : (
        leases.map((l, i) => {
          const standing = fmtBalance(Number(l.balance || 0));
          const title =
            [l.property_name, l.unit_name].filter(Boolean).join(" · ") || "Lease";
          return (
            <div className="dash-panel mb-md" key={l.id || i}>
              <div className="dash-panel-title">{title}</div>
              <div className="staff-card-row">
                <span>Status</span>
                <span>{l.status || "—"}</span>
              </div>
              <div className="staff-card-row">
                <span>Monthly Rent</span>
                <span>{money(l.rent_amount)}</span>
              </div>
              <div className="staff-card-row">
                <span>Start Date</span>
                <span>{fmtDate(l.start_date)}</span>
              </div>
              <div className="staff-card-row">
                <span>End Date</span>
                <span>{fmtDate(l.end_date)}</span>
              </div>
              <div className="staff-card-row">
                <span>Balance</span>
                <span className={standing.cls}>{standing.text}</span>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
