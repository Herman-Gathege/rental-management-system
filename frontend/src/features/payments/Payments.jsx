// frontend/src/features/payments/Payments.jsx
//
// Payment history with a date-range filter (requirement 6) plus the existing
// property filter, payment-type/method filters and page-local search.
//
// The date range is applied on `payment_date` — the date the money was
// received, which is what the list is sorted by and what the table shows. All
// filtering happens in the backend so pagination totals stay truthful, and the
// page resets to page 1 whenever a filter changes so no stale rows remain.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { queryPayments } from "../../api/payments";
import { useProperty } from "../../context/PropertyContext";
import { useAuth } from "../../context/AuthContext";
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

const PER_PAGE = 25;

export default function Payments() {
  const { activeProperty } = useProperty();
  const { user } = useAuth();

  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [paymentType, setPaymentType] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("");
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);

  // Re-page whenever a filter changes, so a stale page number can never show an
  // empty table while matching records sit on page 1.
  const pg = useServerPagination(
    PER_PAGE,
    `${activeProperty?.id || "all"}|${startDate}|${endDate}|${paymentType}|${paymentMethod}|${debouncedSearch}`,
  );
  const { page, setPage, total, setTotal, totalPages, limit, offset } = pg;

  const canRecord = user?.role === "LANDLORD";

  // Client-side guard so an invalid range is explained immediately; the
  // backend rejects it too (a direct API call can't bypass the rule).
  const rangeError =
    startDate && endDate && startDate > endDate
      ? "The start date must be on or before the end date."
      : "";

  const filtersActive = Boolean(
    startDate || endDate || paymentType || paymentMethod || debouncedSearch,
  );

  const clearFilters = () => {
    setStartDate("");
    setEndDate("");
    setPaymentType("");
    setPaymentMethod("");
    setSearch("");
  };

  const fetchPayments = async () => {
    if (rangeError) {
      setPayments([]);
      setTotal(0);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");
      const res = await queryPayments({
        propertyId: activeProperty?.id || null,
        startDate: startDate || null,
        endDate: endDate || null,
        paymentType: paymentType || null,
        paymentMethod: paymentMethod || null,
        search: debouncedSearch || null,
        limit,
        offset,
      });
      setPayments(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load payments");
      setPayments([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    activeProperty,
    page,
    startDate,
    endDate,
    paymentType,
    paymentMethod,
    debouncedSearch,
    rangeError,
  ]);

  const showingFrom = total === 0 ? 0 : offset + 1;
  const showingTo = Math.min(offset + limit, total);

  const renderBody = () => {
    if (loading) return <TableSkeleton rows={6} columns={5} />;

    if (error) {
      return (
        <ErrorState
          title="Couldn’t load payments"
          description={error}
          onRetry={fetchPayments}
        />
      );
    }

    if (total === 0 && filtersActive) {
      return (
        <NoResultsState
          term={debouncedSearch || (startDate || endDate ? `${startDate || "…"} – ${endDate || "…"}` : "")}
          onClear={clearFilters}
          description="No payments match the selected filters. Try widening the date range or clearing the filters."
        />
      );
    }

    if (total === 0) {
      return (
        <EmptyState
          title="No payments recorded yet"
          description="Payments appear here as soon as they are recorded or imported in a batch upload."
          action={
            canRecord ? (
              <Link to="/owner/payments/record" className="btn btn-primary">
                Record first payment
              </Link>
            ) : null
          }
        />
      );
    }

    return (
      <>
        <div className="text-sm text-muted mb-sm">
          Showing {showingFrom}–{showingTo} of {total}
        </div>

        <div className="properties-table-wrapper hidden-mobile">
          <table className="properties-table">
            <thead>
              <tr>
                <th>Tenant</th>
                <th>Amount (KES)</th>
                <th>Type</th>
                <th>Method</th>
                <th>Reference</th>
                <th>Payment date</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id}>
                  <td className="prop-name">{p.tenant_name}</td>
                  <td>{Number(p.amount).toLocaleString()}</td>
                  <td style={{ textTransform: "capitalize" }}>
                    {p.payment_type || "rent"}
                  </td>
                  <td>{(p.payment_method || "").toUpperCase()}</td>
                  <td>{p.reference || "—"}</td>
                  <td>{new Date(p.payment_date).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="hidden-desktop properties-cards">
          {payments.map((p) => (
            <div key={p.id} className="property-card card">
              <strong>{p.tenant_name}</strong>
              <div className="text-sm">KES {Number(p.amount).toLocaleString()}</div>
              <div className="text-sm" style={{ textTransform: "capitalize" }}>
                {p.payment_type || "rent"}
              </div>
              <div className="text-sm">
                {(p.payment_method || "").toUpperCase()}
                {p.reference ? ` — ${p.reference}` : ""}
              </div>
              <div className="text-sm text-muted">
                {new Date(p.payment_date).toLocaleDateString()}
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
    );
  };

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Payment History</h2>
        {canRecord && (
          <Link to="/owner/payments/record" className="btn btn-primary btn-sm">
            + Record Payment
          </Link>
        )}
      </div>

      <div className="card mb-md">
        <div
          className="grid gap-md"
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}
        >
          <div className="form-group">
            <label htmlFor="payment-from">From (payment date)</label>
            <input
              id="payment-from"
              type="date"
              className="input"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="payment-to">To (payment date)</label>
            <input
              id="payment-to"
              type="date"
              className="input"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="payment-type">Type</label>
            <select
              id="payment-type"
              className="input"
              value={paymentType}
              onChange={(e) => setPaymentType(e.target.value)}
            >
              <option value="">All</option>
              <option value="rent">Rent</option>
              <option value="deposit">Deposit</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="payment-method">Method</label>
            <select
              id="payment-method"
              className="input"
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
            >
              <option value="">All</option>
              <option value="mpesa">M-Pesa</option>
              <option value="bank">Bank</option>
              <option value="cash">Cash</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="payment-search">Search</label>
            <TableSearch
              id="payment-search"
              value={search}
              onChange={setSearch}
              placeholder="Tenant or reference…"
              label="Search payments by tenant or reference"
            />
          </div>
        </div>

        {rangeError && <p className="error-text mt-sm">{rangeError}</p>}

        {filtersActive && (
          <button
            type="button"
            className="btn btn-secondary btn-sm mt-sm"
            onClick={clearFilters}
          >
            Clear filters
          </button>
        )}
      </div>

      {renderBody()}
    </section>
  );
}
