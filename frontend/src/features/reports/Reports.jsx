//
// Landlord / Finance Financial Reports
// Sprint 6.2
//
// Reports:
// • Rent Roll
// • Collection
// • Vendor
// • Property Profitability
//

import { useEffect, useState } from "react";

import { useProperty } from "../../context/PropertyContext";

import {
  getRentRoll,
  getCollectionReport,
  getVendorReport,
  getProfitByProperty,
  downloadReportCsv,
} from "../../api/reports";

import ReportFilters from "./ReportFilters";
import RentRollTable from "./RentRollTable";
import CollectionTable from "./CollectionTable";
import VendorTable from "./VendorTable";
import ProfitTable from "./ProfitTable";

const REPORTS = [
  {
    key: "rent-roll",
    label: "Rent Roll",
    hasDates: false,
  },
  {
    key: "collection",
    label: "Collection",
    hasDates: true,
  },
  {
    key: "vendor",
    label: "Vendor",
    hasDates: true,
  },
  {
    key: "profit",
    label: "Profitability",
    hasDates: true,
  },
];

export default function Reports() {
  const { properties } = useProperty();

  const [active, setActive] = useState("rent-roll");

  const [propertyId, setPropertyId] = useState("");

  const [status, setStatus] = useState("");

  const [search, setSearch] = useState("");

  const [startDate, setStartDate] = useState("");

  const [endDate, setEndDate] = useState("");

  const [rows, setRows] = useState([]);

  const [loading, setLoading] = useState(false);

  const [downloading, setDownloading] = useState(false);

  const [error, setError] = useState("");

  const current = REPORTS.find(
    (r) => r.key === active
  );

  const opts = () => ({
    propertyId: propertyId || undefined,

    // Reserved for backend filtering.
    status: status || undefined,
    search: search || undefined,

    startDate:
      current.hasDates && startDate
        ? startDate
        : undefined,

    endDate:
      current.hasDates && endDate
        ? endDate
        : undefined,
  });

  const load = async () => {
    setLoading(true);
    setError("");

    try {
      let data;

      switch (active) {
        case "rent-roll":
          data = await getRentRoll(opts());
          break;

        case "collection":
          data = await getCollectionReport(opts());
          break;

        case "vendor":
          data = await getVendorReport(opts());
          break;

        case "profit":
          data = await getProfitByProperty(opts());
          break;

        default:
          data = [];
      }

      setRows(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Could not load this report."
      );

      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    active,
    propertyId,
    status,
    search,
    startDate,
    endDate,
  ]);

  const handleDownload = async () => {
    setDownloading(true);

    try {
      const path =
        active === "profit"
          ? "profit-by-property"
          : active;

      await downloadReportCsv(path, opts());
    } catch {
      setError(
        "Could not download the CSV."
      );
    } finally {
      setDownloading(false);
    }
  };

  return (
    <section className="properties-page">

      {/* Header */}

      <div className="properties-header">

        <h2>Financial Reports</h2>

        <button
          className="btn btn-primary"
          onClick={handleDownload}
          disabled={
            downloading ||
            loading ||
            rows.length === 0
          }
        >
          {downloading
            ? "Preparing..."
            : "Download CSV"}
        </button>

      </div>

      {/* Report Tabs */}

      <div className="flex gap-sm flex-wrap mb-md">

        {REPORTS.map((report) => (
          <button
            key={report.key}
            className={`btn btn-sm ${
              active === report.key
                ? "btn-primary"
                : "btn-secondary"
            }`}
            onClick={() =>
              setActive(report.key)
            }
          >
            {report.label}
          </button>
        ))}

      </div>

      {/* Filters */}

      <ReportFilters
        properties={properties}

        propertyId={propertyId}
        setPropertyId={setPropertyId}

        status={status}
        setStatus={setStatus}

        search={search}
        setSearch={setSearch}

        startDate={startDate}
        setStartDate={setStartDate}

        endDate={endDate}
        setEndDate={setEndDate}

        showDates={current.hasDates}
      />

      {error && (
        <div className="info-banner-warning mb-md">
          <p>{error}</p>
        </div>
      )}

      {/* Report Results */}

      <div className="dash-panel">

        <div
          className="dash-panel-title"
          style={{
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
          }}
        >
          <span>{current.label}</span>

          {!loading && (
            <span className="text-muted">
              {rows.length} record
              {rows.length !== 1
                ? "s"
                : ""}
            </span>
          )}
        </div>

                {loading ? (
          <div className="text-muted">
            Loading report...
          </div>
        ) : rows.length === 0 ? (
          <div className="text-muted">
            No data available for the selected filters.
          </div>
        ) : (
          <div className="staff-table-wrap">

            {active === "rent-roll" && (
              <RentRollTable rows={rows} />
            )}

            {active === "collection" && (
              <CollectionTable rows={rows} />
            )}

            {active === "vendor" && (
              <VendorTable rows={rows} />
            )}

            {active === "profit" && (
              <ProfitTable rows={rows} />
            )}

          </div>
        )}

      </div>

    </section>
  );
}