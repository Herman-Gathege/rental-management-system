//frontend/src/features/payments/Reconciliation.jsx
//
// Payment reconciliation queue — Sprint 7 cleanup (Batch 3).
//
// Landlord + Finance. Lists candidate payments awaiting a decision (from
// batch CSV uploads or manual flags), lets the reviewer Apply (creates a
// real Payment), Reject (mark with reason, no payment created), or Delete
// (hard remove — backend blocks if already applied).
//
// Assumes getTenants() from api/tenants and getLeases() from api/leases.
// If your API signatures differ, adjust the two imports below.

import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import {
  listReviewItems,
  applyReviewItem,
  rejectReviewItem,
  deleteReviewItem,
} from "../../api/paymentReconciliation";
import { getTenants } from "../../api/tenants";
import { getLeases } from "../../api/leases";

const money = (n) => "KES " + Number(n || 0).toLocaleString();
const fmtDate = (d) => (d ? new Date(d).toLocaleDateString("en-GB") : "—");

const FLAG_LABEL = {
  unmatched: "Unmatched",
  multiple_leases: "Multiple leases",
  no_active_lease: "No active lease",
  duplicate: "Duplicate",
  parse_error: "Parse error",
  amount_mismatch: "Amount mismatch",
  manual_flag: "Manual flag",
};

const STATUS_TABS = [
  { key: "pending_review", label: "Pending" },
  { key: "applied", label: "Applied" },
  { key: "rejected", label: "Rejected" },
  { key: "all", label: "All" },
];

// Role → base path so back-link + nav feel right for both owner and finance.
function dashboardBase(role) {
  switch ((role || "").toLowerCase()) {
    case "finance": return "/finance";
    default:        return "/owner";
  }
}

export default function Reconciliation() {
  const { user } = useAuth();
  const base = dashboardBase(user?.role);

  const [statusFilter, setStatusFilter] = useState("pending_review");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [applyingItem, setApplyingItem] = useState(null); // opens modal when set

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await listReviewItems(statusFilter);
      setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load review queue");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const handleReject = async (item) => {
    const reason = prompt(
      `Reject this ${money(item.amount)} payment?\n\nOptional reason:`,
      ""
    );
    if (reason === null) return;
    try {
      await rejectReviewItem(item.id, reason || null);
      await load();
    } catch (err) {
      alert(err?.response?.data?.detail || "Reject failed");
    }
  };

  const handleDelete = async (item) => {
    if (!confirm(`Delete this ${money(item.amount)} review item permanently?`)) return;
    try {
      await deleteReviewItem(item.id);
      await load();
    } catch (err) {
      alert(err?.response?.data?.detail || "Delete failed");
    }
  };

  return (
    <section className="properties-page">
      <div className="flex items-center gap-sm mb-sm">
        <Link to={`${base}/dashboard`} className="text-sm checklist-back-link">
          ← Dashboard
        </Link>
      </div>

      <div className="properties-header">
        <div>
          <h2>Payment Review</h2>
          <p className="text-muted text-sm">
            Candidate payments that couldn't be auto-matched. Fix and apply,
            reject, or delete.
          </p>
        </div>
      </div>

      {/* Status tabs */}
      <div className="flex gap-sm mt-md flex-wrap">
        {STATUS_TABS.map((t) => (
          <button
            key={t.key}
            className={`btn btn-sm ${statusFilter === t.key ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setStatusFilter(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && <div className="error-text mt-md">{error}</div>}

      {loading ? (
        <p className="mt-md">Loading…</p>
      ) : items.length === 0 ? (
        <div className="empty-state mt-md">
          <p>No items in this view.</p>
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="properties-table-wrapper hidden-mobile mt-md">
            <table className="properties-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Reference</th>
                  <th>Payer</th>
                  <th>Tenant</th>
                  <th>Flag</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((it) => (
                  <ReviewRow
                    key={it.id}
                    item={it}
                    onApply={() => setApplyingItem(it)}
                    onReject={() => handleReject(it)}
                    onDelete={() => handleDelete(it)}
                  />
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="hidden-desktop properties-cards mt-md">
            {items.map((it) => (
              <ReviewCard
                key={it.id}
                item={it}
                onApply={() => setApplyingItem(it)}
                onReject={() => handleReject(it)}
                onDelete={() => handleDelete(it)}
              />
            ))}
          </div>
        </>
      )}

      {applyingItem && (
        <ApplyModal
          item={applyingItem}
          onClose={() => setApplyingItem(null)}
          onApplied={async () => {
            setApplyingItem(null);
            await load();
          }}
        />
      )}
    </section>
  );
}


/* ─── Row / Card ────────────────────────────────────────────────────── */

function ReviewRow({ item, onApply, onReject, onDelete }) {
  const isPending = item.status === "pending_review";
  return (
    <tr>
      <td>{fmtDate(item.payment_date)}</td>
      <td>{money(item.amount)}</td>
      <td>{item.reference || "—"}</td>
      <td>{item.payer_phone || item.payer_name || "—"}</td>
      <td>{item.tenant_name || "—"}</td>
      <td>
        <span className="role-badge">
          {FLAG_LABEL[item.flag_reason] || item.flag_reason}
        </span>
      </td>
      <td>
        <span className={`status-pill ${statusPillClass(item.status)}`}>
          {statusLabel(item)}
        </span>
      </td>
      <td>
        {isPending ? (
          <div className="flex gap-sm flex-wrap">
            <button className="btn btn-primary btn-sm" onClick={onApply}>Fix & Apply</button>
            <button className="btn btn-secondary btn-sm" onClick={onReject}>Reject</button>
            <button className="btn btn-danger btn-sm" onClick={onDelete}>Delete</button>
          </div>
        ) : (
          <div className="flex gap-sm">
            {item.status !== "applied" && (
              <button className="btn btn-danger btn-sm" onClick={onDelete}>Delete</button>
            )}
          </div>
        )}
      </td>
    </tr>
  );
}

function ReviewCard({ item, onApply, onReject, onDelete }) {
  const isPending = item.status === "pending_review";
  return (
    <div className="property-card card">
      <div className="flex items-center justify-between">
        <strong>{money(item.amount)}</strong>
        <span className={`status-pill ${statusPillClass(item.status)}`}>
          {statusLabel(item)}
        </span>
      </div>
      <div className="text-sm">
        <div><span className="text-muted">Date: </span>{fmtDate(item.payment_date)}</div>
        <div><span className="text-muted">Reference: </span>{item.reference || "—"}</div>
        <div><span className="text-muted">Payer: </span>{item.payer_phone || item.payer_name || "—"}</div>
        <div><span className="text-muted">Tenant: </span>{item.tenant_name || "—"}</div>
        <div>
          <span className="text-muted">Flag: </span>
          <span className="role-badge">{FLAG_LABEL[item.flag_reason] || item.flag_reason}</span>
        </div>
      </div>
      {isPending && (
        <div className="flex gap-sm flex-wrap mt-sm">
          <button className="btn btn-primary btn-sm" onClick={onApply}>Fix & Apply</button>
          <button className="btn btn-secondary btn-sm" onClick={onReject}>Reject</button>
          <button className="btn btn-danger btn-sm" onClick={onDelete}>Delete</button>
        </div>
      )}
      {!isPending && item.status !== "applied" && (
        <div className="flex gap-sm mt-sm">
          <button className="btn btn-danger btn-sm" onClick={onDelete}>Delete</button>
        </div>
      )}
      {item.status === "rejected" && item.rejection_reason && (
        <div className="text-sm text-muted mt-sm">
          <strong>Reason:</strong> {item.rejection_reason}
        </div>
      )}
    </div>
  );
}

function statusLabel(item) {
  if (item.status === "pending_review") return "pending";
  return item.status;
}

function statusPillClass(status) {
  switch (status) {
    case "applied":  return "status-paid";
    case "rejected": return "status-owed";
    default:         return "status-ok";
  }
}


/* ─── Apply Modal ───────────────────────────────────────────────────── */

function ApplyModal({ item, onClose, onApplied }) {
  const [tenants, setTenants] = useState([]);
  const [allLeases, setAllLeases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    tenant_id: item.tenant_id || "",
    lease_id: item.lease_id || "",
    amount: String(item.amount || ""),
    payment_date: item.payment_date || new Date().toISOString().slice(0, 10),
    reference: item.reference || "",
    payment_method: "mpesa",
    payment_type: "rent",
    notes: item.notes || "",
    notify: false,
  });

  useEffect(() => {
    const load = async () => {
      try {
        const [t, l] = await Promise.all([getTenants(), getLeases()]);
        setTenants(Array.isArray(t) ? t : (t?.items || []));
        setAllLeases(Array.isArray(l) ? l : (l?.items || []));
      } catch (err) {
        setError("Failed to load tenants or leases");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Leases for the selected tenant, active only.
  const tenantLeases = useMemo(() => {
    if (!form.tenant_id) return [];
    return allLeases.filter(
      (l) => l.tenant_id === form.tenant_id && (l.status === "active" || !l.status)
    );
  }, [form.tenant_id, allLeases]);

  // Clear lease when tenant changes to a tenant that doesn't have the current lease.
  useEffect(() => {
    if (form.lease_id && !tenantLeases.some((l) => l.id === form.lease_id)) {
      setForm((f) => ({ ...f, lease_id: "" }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.tenant_id, tenantLeases.length]);

  const handleSubmit = async () => {
    setError("");
    if (!form.tenant_id) return setError("Pick a tenant");
    if (!form.lease_id) return setError("Pick a lease");
    const amt = parseFloat(form.amount);
    if (!amt || amt <= 0) return setError("Amount must be positive");
    if (!form.payment_date) return setError("Payment date is required");

    setApplying(true);
    try {
      await applyReviewItem(item.id, {
        tenant_id: form.tenant_id,
        lease_id: form.lease_id,
        amount: amt,
        payment_date: form.payment_date,
        reference: form.reference || null,
        payment_method: form.payment_method,
        payment_type: form.payment_type,
        notes: form.notes || null,
        notify: form.notify,
      });
      onApplied();
    } catch (err) {
      setError(err?.response?.data?.detail || "Apply failed");
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal card"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 640, margin: "40px auto", padding: 24 }}
      >
        <div className="flex items-center justify-between mb-md">
          <h3 style={{ margin: 0 }}>Fix & Apply</h3>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>Close</button>
        </div>

        {item.raw_transaction && (
          <div className="text-sm text-muted mb-sm" style={{ background: "#f9fafb", padding: 8, borderRadius: 4 }}>
            <strong>Source: </strong>{item.raw_transaction}
          </div>
        )}

        {loading ? (
          <p>Loading tenants and leases…</p>
        ) : (
          <>
            <div className="form-group">
              <label>Tenant</label>
              <select
                className="input"
                value={form.tenant_id}
                onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
              >
                <option value="">Select tenant…</option>
                {tenants.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.full_name}{t.phone ? ` (${t.phone})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Lease</label>
              <select
                className="input"
                value={form.lease_id}
                onChange={(e) => setForm({ ...form, lease_id: e.target.value })}
                disabled={!form.tenant_id}
              >
                <option value="">
                  {form.tenant_id ? "Select lease…" : "Pick a tenant first"}
                </option>
                {tenantLeases.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.unit_name || l.unit_id}
                    {l.property_name ? ` — ${l.property_name}` : ""}
                    {l.rent_amount != null ? ` (${money(l.rent_amount)}/mo)` : ""}
                  </option>
                ))}
              </select>
              {form.tenant_id && tenantLeases.length === 0 && (
                <p className="text-sm text-muted">This tenant has no active leases.</p>
              )}
            </div>

            <div className="two-col">
              <div className="form-group">
                <label>Amount (KES)</label>
                <input
                  className="input"
                  type="number"
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Payment date</label>
                <input
                  className="input"
                  type="date"
                  value={form.payment_date}
                  onChange={(e) => setForm({ ...form, payment_date: e.target.value })}
                />
              </div>
            </div>

            <div className="two-col">
              <div className="form-group">
                <label>Method</label>
                <select
                  className="input"
                  value={form.payment_method}
                  onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
                >
                  <option value="mpesa">M-Pesa</option>
                  <option value="cash">Cash</option>
                  <option value="bank">Bank</option>
                </select>
              </div>
              <div className="form-group">
                <label>Type</label>
                <select
                  className="input"
                  value={form.payment_type}
                  onChange={(e) => setForm({ ...form, payment_type: e.target.value })}
                >
                  <option value="rent">Rent</option>
                  <option value="deposit">Deposit</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Reference</label>
              <input
                className="input"
                type="text"
                value={form.reference}
                onChange={(e) => setForm({ ...form, reference: e.target.value })}
                placeholder="M-Pesa code or leave blank"
              />
            </div>

            <div className="form-group">
              <label>Notes (optional)</label>
              <textarea
                className="input"
                rows={2}
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="Anything the next reviewer should know"
              />
            </div>

            <label className="flex items-center gap-sm text-sm">
              <input
                type="checkbox"
                checked={form.notify}
                onChange={(e) => setForm({ ...form, notify: e.target.checked })}
              />
              Send WhatsApp receipt to tenant
            </label>

            {error && <div className="error-text mt-sm">{error}</div>}

            <div className="flex gap-sm mt-md justify-end">
              <button className="btn btn-secondary" onClick={onClose} disabled={applying}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={applying}
              >
                {applying ? "Applying…" : "Apply Payment"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}