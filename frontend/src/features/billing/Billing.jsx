//frontend\src\features\billing\Billing.jsx
import { useEffect, useState } from "react";
import { generateMonthlyCharges, queryCharges } from "../../api/charges";
import { useProperty } from "../../context/PropertyContext";
import { useDebouncedValue } from "../../hooks/useDebouncedValue";
import Pagination from "../../components/Pagination";
import useServerPagination from "../../hooks/useServerPagination";
import {
  EmptyState,
  ErrorState,
  NoResultsState,
  TableSearch,
  TableSkeleton,
} from "../../components/ui/States";

const money = (n) => Number(n || 0).toLocaleString();

const PER_PAGE = 25;

// A charge is "late" for display purposes if it still owes a balance and its
// due date is strictly before today (a charge due *today* is not yet late).
const startOfToday = () => {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
};
const isLate = (c) => Number(c.balance) > 0 && new Date(c.due_date) < startOfToday();

// A tenant is "in credit" when they've overpaid against their total charges.
// That overpayment is lease-level (it isn't on any single charge), so the
// backend sends it as account_credit. When it exists, every (settled) charge
// row for that lease shows the credit instead of a 0 balance.
const hasCredit = (c) => Number(c.account_credit) > 0;

// Balance colour: green when in credit, red when past-due, plain otherwise.
const balanceClass = (c) =>
  hasCredit(c) ? "balance-credit" : isLate(c) ? "balance-late" : "";

// What to print in the Balance column: the credit (as a negative, e.g.
// "-27,500") when overpaid, otherwise the charge's own balance.
const balanceText = (c) =>
  hasCredit(c) ? `-${money(c.account_credit)}` : money(c.balance);

const pillClass = (status) =>
  status === "paid"
    ? "status-ok"
    : status === "overdue"
    ? "status-owed"
    : status === "partial"
    ? "status-partial"
    : "status-paid"; // pending

// Sprint 7 cleanup: charge-type badge. Rent vs deposit look identical in the
// table otherwise (same tenant name, same unit, sometimes even the same
// amount), so the type is called out explicitly with a coloured pill.
// Inline styles keep it self-contained — no dependency on CSS classes that
// might not exist yet.
const typeStyle = (t) => ({
  display: "inline-block",
  padding: "2px 8px",
  borderRadius: 4,
  fontSize: 12,
  fontWeight: 600,
  color: "#fff",
  textTransform: "capitalize",
  background: t === "deposit" ? "#8b5cf6" : "#2563eb", // purple / blue
});
const typeLabel = (c) => c.charge_type || "rent";

export default function Billing() {
  const { activeProperty } = useProperty();
  const [charges, setCharges] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  // Charge type filter (rent / deposit / all). The backend already stores
  // charge_type on every row; this exposes it as a real query filter so the
  // totals below reflect exactly the rows on screen.
  const [typeFilter, setTypeFilter] = useState("");
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [generating, setGenerating] = useState(false);

  // Re-page whenever the filters or the selected property change.
  const pg = useServerPagination(
    PER_PAGE,
    `${statusFilter}|${typeFilter}|${debouncedSearch}|${activeProperty?.id || "all"}`,
  );
  const { page, setPage, total, setTotal, totalPages, limit, offset, reset } = pg;

  const fetchCharges = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await queryCharges({
        status: statusFilter || null,
        chargeType: typeFilter || null,
        propertyId: activeProperty?.id || null,
        search: debouncedSearch || null,
        limit,
        offset,
      });
      setCharges(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load charges");
      setCharges([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const filtersActive = Boolean(statusFilter || typeFilter || debouncedSearch);

  const clearFilters = () => {
    setStatusFilter("");
    setTypeFilter("");
    setSearch("");
  };

  useEffect(() => {
    fetchCharges();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, typeFilter, debouncedSearch, activeProperty, page]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError("");
    try {
      const result = await generateMonthlyCharges();
      setSuccess(result.message);
      reset();
      await fetchCharges();
      setTimeout(() => setSuccess(""), 4000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate charges");
    } finally {
      setGenerating(false);
    }
  };

  const showingFrom = total === 0 ? 0 : offset + 1;
  const showingTo = Math.min(offset + limit, total);

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Billing & Charges</h2>
        <button
          className="btn btn-primary btn-sm"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Generating..." : "Generate Monthly Charges"}
        </button>
      </div>

      {success && <div className="success-banner">{success}</div>}
      {error && <div className="error-text">{error}</div>}

      <div className="card mb-md">
        {/* Type filter: rent vs deposit. Deposits are a separate obligation —
            showing them mixed with rent makes month-to-month rent figures read
            wrong, so this is the primary split. */}
        <div className="flex gap-sm flex-wrap items-center">
          <span className="text-sm text-muted">Charge type:</span>
          {[
            { value: "", label: "All charges" },
            { value: "rent", label: "Rent" },
            { value: "deposit", label: "Deposits" },
          ].map((option) => (
            <button
              key={option.value || "all"}
              className={`btn btn-sm ${typeFilter === option.value ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setTypeFilter(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* "pending" = unpaid and not yet past its due date; past-due balances
            live under "overdue", so the two filters don't overlap. */}
        <div className="flex gap-sm flex-wrap items-center mt-sm">
          <span className="text-sm text-muted">Status:</span>
          {["", "pending", "partial", "paid", "overdue"].map((s) => (
            <button
              key={s}
              className={`btn btn-sm ${statusFilter === s ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setStatusFilter(s)}
            >
              {s || "All"}
            </button>
          ))}
        </div>

        <div className="flex gap-sm flex-wrap items-end mt-sm">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="charge-search">Search tenant</label>
            <TableSearch
              id="charge-search"
              value={search}
              onChange={setSearch}
              placeholder="Tenant name…"
              label="Search charges by tenant name"
            />
          </div>

          {filtersActive && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={clearFilters}
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <TableSkeleton rows={6} columns={8} />
      ) : error ? (
        <ErrorState
          title="Couldn’t load charges"
          description={error}
          onRetry={fetchCharges}
        />
      ) : total === 0 && filtersActive ? (
        <NoResultsState
          term={debouncedSearch || (typeFilter === "deposit" ? "Deposits" : typeFilter === "rent" ? "Rent" : "")}
          onClear={clearFilters}
          description="No charges match the selected filters. Clear them to see all charges again."
        />
      ) : total === 0 ? (
        <EmptyState
          title="No charges yet"
          description="Monthly rent charges will appear here automatically once invoicing runs, or you can generate them now."
          action={
            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              disabled={generating}
            >
              {generating ? "Generating…" : "Generate monthly charges"}
            </button>
          }
        />
      ) : (
        <>
          <div className="text-sm text-muted mb-sm mt-sm">
            Showing {showingFrom}–{showingTo} of {total}
            {typeFilter && ` ${typeFilter} charges`}
          </div>

          <div className="properties-table-wrapper hidden-mobile">
            <table className="properties-table">
              <thead>
                <tr>
                  <th>Tenant</th>
                  <th>Unit</th>
                  <th>Property</th>
                  <th>Amount (KES)</th>
                  <th>Paid (KES)</th>
                  <th>Balance (KES)</th>
                  <th>Due Date</th>
                  <th>Status</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {charges.map((c) => (
                  <tr key={c.id}>
                    <td className="prop-name">{c.tenant_name}</td>
                    <td>{c.unit_name}</td>
                    <td>{c.property_name}</td>
                    <td>{money(c.amount)}</td>
                    <td>{money(c.amount_paid)}</td>
                    <td className={balanceClass(c)}>{balanceText(c)}</td>
                    <td>{new Date(c.due_date).toLocaleDateString()}</td>
                    <td>
                      <span className={`status-pill ${pillClass(c.status)}`}>{c.status}</span>
                    </td>
                    <td>
                      <span style={typeStyle(typeLabel(c))}>{typeLabel(c)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="hidden-desktop properties-cards">
            {charges.map((c) => (
              <div key={c.id} className="property-card card">
                <div className="property-card-header">
                  <strong>{c.tenant_name}</strong>
                  <span className={`status-pill ${pillClass(c.status)}`}>{c.status}</span>
                </div>
                <div className="text-sm">{c.unit_name} — {c.property_name}</div>
                <div className="text-sm">Amount: KES {money(c.amount)}</div>
                <div className="text-sm">Paid: KES {money(c.amount_paid)}</div>
                <div className={`text-sm ${balanceClass(c)}`}>
                  Balance: KES {balanceText(c)}
                </div>
                <div className="text-sm text-muted">Due: {new Date(c.due_date).toLocaleDateString()}</div>
                <div className="mt-sm">
                  <span style={typeStyle(typeLabel(c))}>{typeLabel(c)}</span>
                </div>
              </div>
            ))}
          </div>

          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </>
      )}
    </section>
  );
}
