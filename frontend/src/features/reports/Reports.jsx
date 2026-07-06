//frontend\src\features\reports\Reports.jsx
//
// Landlord / finance financial reports (Sprint 6.2 #1).
// Four reports: Rent Roll, Collection, Vendor, Property Profitability.
// Filters: property (from the navbar PropertyContext) + date range (where the
// report supports it). Each report has a "Download CSV" button hitting the
// matching server-side CSV endpoint.
//
// Rent Roll has no date range (it's a point-in-time snapshot of leases); the
// others accept an optional start/end. The property filter uses the same
// property list the switcher does, via PropertyContext.

import { useEffect, useState } from "react";
import { useProperty } from "../../context/PropertyContext";
import {
  getRentRoll,
  getCollectionReport,
  getVendorReport,
  getProfitByProperty,
  downloadReportCsv,
} from "../../api/reports";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });

const REPORTS = [
  { key: "rent-roll",   label: "Rent Roll",        hasDates: false },
  { key: "collection",  label: "Collection",       hasDates: true },
  { key: "vendor",      label: "Vendor",           hasDates: true },
  { key: "profit",      label: "Profitability",    hasDates: true },
];

export default function Reports() {
  const { properties } = useProperty();

  const [active, setActive] = useState("rent-roll");
  const [propertyId, setPropertyId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);

  const current = REPORTS.find((r) => r.key === active);

  const opts = () => ({
    propertyId: propertyId || undefined,
    startDate: current.hasDates && startDate ? startDate : undefined,
    endDate: current.hasDates && endDate ? endDate : undefined,
  });

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      let data;
      if (active === "rent-roll") data = await getRentRoll(opts());
      else if (active === "collection") data = await getCollectionReport(opts());
      else if (active === "vendor") data = await getVendorReport(opts());
      else data = await getProfitByProperty(opts());
      setRows(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not load this report.");
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  // Reload whenever the report type or filters change.
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, propertyId, startDate, endDate]);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      // Profitability's CSV path is profit-by-property; others match their key.
      const path = active === "profit" ? "profit-by-property" : active;
      await downloadReportCsv(path, opts());
    } catch {
      setError("Could not download the CSV.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Financial Reports</h2>
        <button
          className="btn btn-primary"
          onClick={handleDownload}
          disabled={downloading || loading || rows.length === 0}
        >
          {downloading ? "Preparing…" : "Download CSV"}
        </button>
      </div>

      {/* Report type tabs */}
      <div className="flex gap-sm flex-wrap mb-md">
        {REPORTS.map((r) => (
          <button
            key={r.key}
            className={`btn btn-sm ${active === r.key ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setActive(r.key)}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="card mb-md">
        <div className="two-col">
          <div className="form-group">
            <label htmlFor="property">Property</label>
            <select
              id="property"
              className="input"
              value={propertyId}
              onChange={(e) => setPropertyId(e.target.value)}
            >
              <option value="">All properties</option>
              {(properties || []).map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          {current.hasDates && (
            <div className="two-col">
              <div className="form-group">
                <label htmlFor="start">From</label>
                <input
                  id="start"
                  type="date"
                  className="input"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="end">To</label>
                <input
                  id="end"
                  type="date"
                  className="input"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {error && <div className="info-banner-warning mb-md"><p>{error}</p></div>}

      {/* Results */}
      <div className="dash-panel">
        <div className="dash-panel-title">{current.label}</div>
        {loading ? (
          <div className="text-muted">Loading…</div>
        ) : rows.length === 0 ? (
          <div className="text-muted">No data for this report.</div>
        ) : (
          <div className="staff-table-wrap">
            {active === "rent-roll" && <RentRollTable rows={rows} />}
            {active === "collection" && <CollectionTable rows={rows} />}
            {active === "vendor" && <VendorTable rows={rows} />}
            {active === "profit" && <ProfitTable rows={rows} />}
          </div>
        )}
      </div>
    </section>
  );
}

function RentRollTable({ rows }) {
  return (
    <table className="staff-table">
      <thead>
        <tr>
          <th>Tenant</th><th>Property</th><th>Unit</th>
          <th>Monthly Rent</th><th>Deposit Held</th><th>Balance</th><th>Status</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.lease_id}>
            <td>{r.tenant_name || "—"}</td>
            <td>{r.property_name}</td>
            <td>{r.unit_name}</td>
            <td>{money(r.monthly_rent)}</td>
            <td>{money(r.deposit_held)}</td>
            <td className={r.balance > 0 ? "balance-late" : ""}>{money(r.balance)}</td>
            <td>{r.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function CollectionTable({ rows }) {
  return (
    <table className="staff-table">
      <thead>
        <tr>
          <th>Property</th><th>Expected Rent</th><th>Collected</th>
          <th>Outstanding</th><th>Collection Rate</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.property_id}>
            <td>{r.property_name}</td>
            <td>{money(r.expected_rent)}</td>
            <td>{money(r.collected)}</td>
            <td className={r.outstanding > 0 ? "balance-late" : ""}>{money(r.outstanding)}</td>
            <td>{r.collection_rate}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function VendorTable({ rows }) {
  return (
    <table className="staff-table">
      <thead>
        <tr>
          <th>Vendor</th><th>Invoices</th><th>Total Billed</th>
          <th>Total Paid</th><th>Outstanding</th><th>Avg Cost</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.vendor_id}>
            <td>{r.vendor_name}</td>
            <td>{r.invoices}</td>
            <td>{money(r.total_billed)}</td>
            <td>{money(r.total_paid)}</td>
            <td className={r.outstanding > 0 ? "balance-late" : ""}>{money(r.outstanding)}</td>
            <td>{money(r.average_cost)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ProfitTable({ rows }) {
  return (
    <table className="staff-table">
      <thead>
        <tr>
          <th>Property</th><th>Income</th><th>Expenses</th><th>Profit (NOI)</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.property_id}>
            <td>{r.property_name}</td>
            <td>{money(r.income)}</td>
            <td>{money(r.expenses)}</td>
            <td className="text-bold" style={{ color: r.profit >= 0 ? "#16a34a" : "#ef4444" }}>
              {money(r.profit)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
