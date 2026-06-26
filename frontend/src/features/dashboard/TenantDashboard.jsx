//frontend/src/features/dashboard/TenantDashboard.jsx
//
// Tenant self-service dashboard (Sprint 4.5, multi-lease + property switcher).
// Summary cards + charges/payments tables, all filtered to the property chosen
// in the tenant property switcher (or all).
// Responsive: tables on desktop, MobileCardList stacked cards below 768px.

import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useTenantProperty } from "../../context/TenantPropertyContext";
import {
  getTenantDashboard,
  getTenantCharges,
  getTenantPayments,
} from "../../api/dashboard";
import MobileCardList from "../../components/ui/MobileCardList";
import NotificationsCard from "../../components/ui/NotificationsCard";
import TicketsSummaryCard from "../../components/ui/TicketsSummaryCard";

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

const isLate = (c) =>
  Number(c.balance) > 0 && c.due_date && new Date(c.due_date) < startOfToday();

const fmtBalance = (balance) => {
  if (balance < 0) return { text: money(-balance) + " credit", cls: "balance-credit" };
  if (balance > 0) return { text: money(balance) + " due", cls: "balance-late" };
  return { text: money(0), cls: "" };
};

export default function TenantDashboard() {
  const { user } = useAuth();
  const tp = useTenantProperty() || {};
  const activePropertyId = tp.activePropertyId || null;
  const activeProperty = tp.activeProperty || null;

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
        setError(err?.response?.data?.detail || "Could not load your dashboard.");
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
  const allLeases = Array.isArray(data?.leases) ? data.leases : [];

  const matches = (row) => !activePropertyId || row.property_id === activePropertyId;

  const focusLeases = allLeases.filter(matches);
  const visibleCharges = charges.filter(matches);
  const visiblePayments = payments.filter(matches);

  const monthlyRent = focusLeases.reduce((s, l) => s + Number(l.rent_amount || 0), 0);
  const balanceSum = focusLeases.reduce((s, l) => s + Number(l.balance || 0), 0);
  const standing = fmtBalance(balanceSum);

  const distinctChargeProps = new Set(visibleCharges.map((c) => c.property_id).filter(Boolean));
  const showChargeProp = !activeProperty && distinctChargeProps.size > 1;
  const distinctPayProps = new Set(visiblePayments.map((p) => p.property_id).filter(Boolean));
  const showPayProp = !activeProperty && distinctPayProps.size > 1;

  const cards = [
    { label: "Property", value: activeProperty ? activeProperty.name : "All Properties" },
    { label: focusLeases.length === 1 ? "Lease" : "Leases", value: focusLeases.length },
    { label: "Monthly Rent", value: money(monthlyRent), money: true },
    { label: "Account Balance", value: standing.text, money: true, cls: standing.cls },
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

      <NotificationsCard />

      <TicketsSummaryCard />

      {/* ===== Charges ===== */}
      <div className="dash-panel mb-md">
        <div className="dash-panel-title">Charges</div>
        {visibleCharges.length === 0 ? (
          <div className="text-muted">No charges yet.</div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="staff-table-wrap hidden-mobile">
              <table className="staff-table">
                <thead>
                  <tr>
                    {showChargeProp && <th>Property</th>}
                    <th>Month</th>
                    <th>Amount</th>
                    <th>Paid</th>
                    <th>Balance</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleCharges.map((c, i) => (
                    <tr key={i}>
                      {showChargeProp && <td>{c.property_name || "—"}</td>}
                      <td>{fmtMonth(c.month)}</td>
                      <td>{money(c.amount)}</td>
                      <td>{money(c.amount_paid)}</td>
                      <td className={isLate(c) ? "balance-late" : ""}>{money(c.balance)}</td>
                      <td>{c.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <MobileCardList
              data={visibleCharges}
              renderCard={(c, i) => (
                <div className="staff-card" key={i}>
                  <div className="staff-card-title">{fmtMonth(c.month)}</div>
                  {showChargeProp && (
                    <div className="staff-card-row">
                      <span>Property</span>
                      <span>{c.property_name || "—"}</span>
                    </div>
                  )}
                  <div className="staff-card-row">
                    <span>Amount</span>
                    <span>{money(c.amount)}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Paid</span>
                    <span>{money(c.amount_paid)}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Balance</span>
                    <span className={isLate(c) ? "balance-late" : ""}>{money(c.balance)}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Status</span>
                    <span>{c.status}</span>
                  </div>
                </div>
              )}
            />
          </>
        )}
      </div>

      {/* ===== Payments ===== */}
      <div className="dash-panel">
        <div className="dash-panel-title">Payments</div>
        {visiblePayments.length === 0 ? (
          <div className="text-muted">No payments yet.</div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="staff-table-wrap hidden-mobile">
              <table className="staff-table">
                <thead>
                  <tr>
                    {showPayProp && <th>Property</th>}
                    <th>Date</th>
                    <th>Reference</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {visiblePayments.map((p, i) => (
                    <tr key={i}>
                      {showPayProp && <td>{p.property_name || "—"}</td>}
                      <td>{fmtDate(p.date)}</td>
                      <td>{p.reference || "—"}</td>
                      <td>{money(p.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <MobileCardList
              data={visiblePayments}
              renderCard={(p, i) => (
                <div className="staff-card" key={i}>
                  <div className="staff-card-title">{fmtDate(p.date)}</div>
                  {showPayProp && (
                    <div className="staff-card-row">
                      <span>Property</span>
                      <span>{p.property_name || "—"}</span>
                    </div>
                  )}
                  <div className="staff-card-row">
                    <span>Reference</span>
                    <span>{p.reference || "—"}</span>
                  </div>
                  <div className="staff-card-row">
                    <span>Amount</span>
                    <span>{money(p.amount)}</span>
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
