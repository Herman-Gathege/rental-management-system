//frontend/src/features/dashboard/TenantLease.jsx
//
// Tenant "My Lease" page (Sprint 4.5 tenant portal).
// Reuses the already-scoped /dashboard/tenant/me endpoint via
// getTenantDashboard() — same call the dashboard uses — and shows the
// tenant's unit, lease terms, and account standing.
//
// Account standing: the backend returns a signed `balance`
// (positive = owes, negative = overpaid). We derive owed/credit from it here,
// so an overpaid tenant sees "KES X credit" in green rather than a bare
// negative number. (If the backend later exposes amount_owed/credit directly
// we read those instead — the fallbacks below keep this page working either
// way.) Styling reuses existing dashboard classes; only .balance-credit is new.

import { useEffect, useState } from "react";
import { getTenantDashboard } from "../../api/dashboard";

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

export default function TenantLease() {
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
        setError(err?.response?.data?.detail || "Could not load your lease.");
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
        <div className="dash-panel">Loading your lease…</div>
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

  const unit = data?.unit;
  const lease = data?.lease;

  // Derive owed / credit from the signed balance the backend already returns.
  const balance = Number(data?.balance ?? 0);
  const credit =
    data?.credit != null ? Number(data.credit) : balance < 0 ? -balance : 0;
  const owed =
    data?.amount_owed != null ? Number(data.amount_owed) : balance > 0 ? balance : 0;

  let balanceText = money(0);
  let balanceClass = "";
  if (credit > 0) {
    balanceText = money(credit) + " credit";
    balanceClass = "balance-credit";
  } else if (owed > 0) {
    balanceText = money(owed) + " due";
    balanceClass = "balance-late";
  }

  if (!lease) {
    return (
      <div className="p-6">
        <div className="text-lg font-bold mb-md">My Lease</div>
        <div className="dash-panel">
          <div className="text-muted">No lease on file yet.</div>
        </div>
      </div>
    );
  }

  const cards = [
    { label: "Unit", value: unit?.name || "—" },
    { label: "Lease Status", value: lease.status || "—" },
    { label: "Monthly Rent", value: money(lease.rent_amount), money: true },
    { label: "Account Balance", value: balanceText, money: true, cls: balanceClass },
  ];

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">My Lease</div>

      <div className="dash-grid mb-md">
        {cards.map((c) => (
          <div className="dash-stat" key={c.label}>
            <div
              className={
                "dash-stat-value" +
                (c.money ? " dash-stat-money" : "") +
                (c.cls ? " " + c.cls : "")
              }
            >
              {c.value}
            </div>
            <div className="dash-stat-label">{c.label}</div>
          </div>
        ))}
      </div>

      <div className="dash-panel">
        <div className="dash-panel-title">Lease Details</div>
        <table className="staff-table">
          <tbody>
            <tr>
              <td className="text-muted">Unit</td>
              <td>{unit?.name || "—"}</td>
            </tr>
            <tr>
              <td className="text-muted">Monthly Rent</td>
              <td>{money(lease.rent_amount)}</td>
            </tr>
            <tr>
              <td className="text-muted">Status</td>
              <td>{lease.status || "—"}</td>
            </tr>
            <tr>
              <td className="text-muted">Start Date</td>
              <td>{fmtDate(lease.start_date)}</td>
            </tr>
            <tr>
              <td className="text-muted">End Date</td>
              <td>{fmtDate(lease.end_date)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
