//frontend/src/features/dashboard/TenantDashboard.jsx
//
// Tenant self-service dashboard (Sprint 4.5, Chunk 4 + PP-2).
// Resolves the logged-in tenant via tenants.user_id and shows their unit,
// lease, balance, charges and payments. The Charges table now shows Paid /
// Balance per charge and flags a past-due balance in red.

import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import {
  getTenantDashboard,
  getTenantCharges,
  getTenantPayments,
} from "../../api/dashboard";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });

const fmtMonth = (d) =>
  d ? new Date(d).toLocaleDateString("en-GB", { month: "short", year: "numeric" }) : "—";

const fmtDate = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "—";

const startOfToday = () => {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
};
// A charge is "late" if it still owes a balance and its due date has passed.
const isLate = (c) => Number(c.balance) > 0 && c.due_date && new Date(c.due_date) < startOfToday();

export default function TenantDashboard() {
  const { user } = useAuth();

  const [data, setData] = useState(null);
  const [charges, setCharges] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const [d, c, p] = await Promise.all([
          getTenantDashboard(),
          getTenantCharges(),
          getTenantPayments(),
        ]);
        if (!active) return;
        setData(d);
        setCharges(c);
        setPayments(p);
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

  if (loading) {
    return (
      <div className="p-6">
        <div className="dash-panel">Loading your dashboard…</div>
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

  const tenant = data?.tenant || {};
  const unit = data?.unit;
  const lease = data?.lease;
  const balance = data?.balance ?? 0;

  const cards = [
    { label: "Unit", value: unit?.name || "—" },
    { label: "Lease Status", value: lease?.status || "—" },
    { label: "Monthly Rent", value: money(lease?.rent_amount), money: true },
    { label: "Balance", value: money(balance), money: true },
  ];

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Welcome,{" "}
        <span className="company-blue text-bold">
          {tenant.full_name || user?.email || "there"}
        </span>{" "}
        👋
      </div>

      <div className="dash-grid mb-md">
        {cards.map((c) => (
          <div className="dash-stat" key={c.label}>
            <div className={`dash-stat-value${c.money ? " dash-stat-money" : ""}`}>
              {c.value}
            </div>
            <div className="dash-stat-label">{c.label}</div>
          </div>
        ))}
      </div>

      {/* ===== Charges ===== */}
      <div className="dash-panel mb-md">
        <div className="dash-panel-title">Charges</div>
        {charges.length === 0 ? (
          <div className="text-muted">No charges yet.</div>
        ) : (
          <table className="staff-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>Amount</th>
                <th>Paid</th>
                <th>Balance</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {charges.map((c, i) => (
                <tr key={i}>
                  <td>{fmtMonth(c.month)}</td>
                  <td>{money(c.amount)}</td>
                  <td>{money(c.amount_paid)}</td>
                  <td className={isLate(c) ? "balance-late" : ""}>{money(c.balance)}</td>
                  <td>{c.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* ===== Payments ===== */}
      <div className="dash-panel">
        <div className="dash-panel-title">Payments</div>
        {payments.length === 0 ? (
          <div className="text-muted">No payments yet.</div>
        ) : (
          <table className="staff-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Reference</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p, i) => (
                <tr key={i}>
                  <td>{fmtDate(p.date)}</td>
                  <td>{p.reference || "—"}</td>
                  <td>{money(p.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
