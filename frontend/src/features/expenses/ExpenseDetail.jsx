//frontend\src\features\expenses\ExpenseDetail.jsx
//
// Expense detail (Sprint 5). Shows the full record, the workflow action buttons
// (submit / approve / reject / pay) shown per role + status, and the receipts
// UI (upload / view / remove). Reachable by owner/manager/finance; the backend
// enforces the real permissions, this just hides actions the caller can't take.

import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  getExpense,
  submitExpense,
  approveExpense,
  rejectExpense,
  payExpense,
  deleteExpense,
  uploadExpenseAttachment,
  deleteExpenseAttachment,
} from "../../api/expenses";
import { useAuth } from "../../context/AuthContext";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { minimumFractionDigits: 2 });

const fmtDate = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "—";

const statusClass = (status) => {
  switch (status) {
    case "paid":
      return "status-paid";
    case "approved":
      return "status-ok";
    default:
      return "status-owed";
  }
};

function dashboardBase(role) {
  switch (role) {
    case "property_manager":
      return "/manager";
    case "finance":
      return "/finance";
    default:
      return "/owner";
  }
}

export default function ExpenseDetail() {
  const { expenseId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const role = user?.role?.toLowerCase();
  const base = dashboardBase(role);
  const isApprover = role === "landlord" || role === "finance";

  const [expense, setExpense] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);

  const load = async () => {
    try {
      setExpense(await getExpense(expenseId));
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load expense");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [expenseId]);

  const runAction = async (fn) => {
    setBusy(true);
    try {
      const updated = await fn();
      setExpense(updated);
    } catch (err) {
      alert(err.response?.data?.detail || "Action failed");
    } finally {
      setBusy(false);
    }
  };

  const handleSubmit = () => {
    if (!confirm("Submit this expense for approval?")) return;
    runAction(() => submitExpense(expenseId));
  };

  const handleApprove = () => {
    if (!confirm("Approve this expense?")) return;
    runAction(() => approveExpense(expenseId));
  };

  const handleReject = () => {
    const reason = prompt("Reason for rejection (optional):");
    if (reason === null) return; // cancelled
    runAction(() => rejectExpense(expenseId, reason || null));
  };

  const handlePay = () => {
    if (!confirm("Mark this expense as paid?")) return;
    runAction(() => payExpense(expenseId));
  };

  const handleDelete = async () => {
    if (!confirm("Delete this expense? This cannot be undone.")) return;
    setBusy(true);
    try {
      await deleteExpense(expenseId);
      navigate(`${base}/expenses`);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete expense");
      setBusy(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      const updated = await uploadExpenseAttachment(expenseId, file);
      setExpense(updated);
    } catch (err) {
      alert(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleRemoveAttachment = async (attachmentId) => {
    if (!confirm("Remove this receipt?")) return;
    try {
      const updated = await deleteExpenseAttachment(expenseId, attachmentId);
      setExpense(updated);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to remove receipt");
    }
  };

  if (loading) return <p>Loading...</p>;
  if (error) return <div className="error-text">{error}</div>;
  if (!expense) return <p>Expense not found</p>;

  const status = expense.status;
  const canEdit = status === "draft" || status === "submitted";
  const attachments = expense.attachments || [];

  return (
    <section className="properties-page">
      {/* Back link */}
      <div className="flex items-center gap-sm mb-sm">
        <Link to={`${base}/expenses`} className="text-sm checklist-back-link">
          ← All Expenses
        </Link>
      </div>

      <div className="properties-header">
        <div>
          <h2>{expense.title}</h2>
          <p className="text-muted">
            {expense.property_name}
            {expense.unit_name ? ` · ${expense.unit_name}` : ""}
          </p>
        </div>
        <span className={`status-pill ${statusClass(status)}`}>{status}</span>
      </div>

      {/* ─── Details ─── */}
      <div className="card detail-card">
        <h3>Details</h3>

        <div className="two-col">
          <div>
            <div className="text-sm text-muted">Amount</div>
            <div className="text-bold">{money(expense.amount)}</div>
          </div>
          <div>
            <div className="text-sm text-muted">Expense Date</div>
            <div className="text-bold">{fmtDate(expense.expense_date)}</div>
          </div>
        </div>

        <div className="two-col mt-md">
          <div>
            <div className="text-sm text-muted">Category</div>
            <div className="text-bold">{expense.category_name || "—"}</div>
          </div>
          <div>
            <div className="text-sm text-muted">Vendor</div>
            <div className="text-bold">{expense.vendor_name || "—"}</div>
          </div>
        </div>

        <div className="two-col mt-md">
          <div>
            <div className="text-sm text-muted">Payment Method</div>
            <div className="text-bold">{expense.payment_method || "—"}</div>
          </div>
          <div>
            <div className="text-sm text-muted">Reference No.</div>
            <div className="text-bold">{expense.reference_number || "—"}</div>
          </div>
        </div>

        <div className="two-col mt-md">
          <div>
            <div className="text-sm text-muted">Receipt No.</div>
            <div className="text-bold">{expense.receipt_number || "—"}</div>
          </div>
          <div>
            <div className="text-sm text-muted">Recorded By</div>
            <div className="text-bold">{expense.created_by_email || "—"}</div>
          </div>
        </div>

        {expense.approved_by_email && (
          <div className="mt-md">
            <div className="text-sm text-muted">Approved By</div>
            <div className="text-bold">{expense.approved_by_email}</div>
          </div>
        )}

        {expense.description && (
          <div className="mt-md">
            <div className="text-sm text-muted">Description</div>
            <div>{expense.description}</div>
          </div>
        )}

        {expense.notes && (
          <div className="mt-md">
            <div className="text-sm text-muted">Notes</div>
            <div>{expense.notes}</div>
          </div>
        )}
      </div>

      {/* ─── Workflow actions ─── */}
      <div className="card detail-card">
        <h3>Actions</h3>

        <div className="flex gap-sm flex-wrap">
          {status === "draft" && (
            <button className="btn btn-primary" onClick={handleSubmit} disabled={busy}>
              Submit for Approval
            </button>
          )}

          {status === "submitted" && isApprover && (
            <>
              <button className="btn btn-primary" onClick={handleApprove} disabled={busy}>
                Approve
              </button>
              <button className="btn btn-danger" onClick={handleReject} disabled={busy}>
                Reject
              </button>
            </>
          )}

          {status === "approved" && isApprover && (
            <button className="btn btn-primary" onClick={handlePay} disabled={busy}>
              Mark as Paid
            </button>
          )}

          {canEdit && (
            <Link to={`${base}/expenses/${expenseId}/edit`} className="btn btn-secondary">
              Edit
            </Link>
          )}

          {canEdit && (
            <button className="btn btn-danger" onClick={handleDelete} disabled={busy}>
              Delete
            </button>
          )}
        </div>

        {status === "submitted" && !isApprover && (
          <p className="text-sm text-muted mt-sm">
            Waiting for a landlord or finance user to approve this expense.
          </p>
        )}
        {status === "paid" && (
          <p className="text-sm text-muted mt-sm">
            This expense is paid and locked. It counts toward reports and NOI.
          </p>
        )}
      </div>

      {/* ─── Receipts ─── */}
      <div className="card detail-card">
        <div className="flex items-center justify-between mb-sm">
          <h3>Receipts</h3>
          <label className="btn btn-secondary btn-sm doc-upload-label">
            {uploading ? "Uploading..." : "Add Receipt"}
            <input
              type="file"
              accept="application/pdf,image/*"
              onChange={handleUpload}
              disabled={uploading}
              className="doc-upload-hidden-input"
            />
          </label>
        </div>

        {attachments.length === 0 ? (
          <div className="empty-state-sm">
            <p className="text-sm">No receipts attached yet.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-sm">
            {attachments.map((a) => (
              <div key={a.id} className="doc-upload-row">
                <div className="doc-upload-row-info">
                  <div className="text-sm text-bold file-name-ellipsis">
                    {a.filename || "Receipt"}
                  </div>
                  <div className="text-xs text-muted">{fmtDate(a.uploaded_at)}</div>
                </div>
                <div className="flex gap-sm">
                  <a
                    href={a.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-secondary btn-sm"
                  >
                    View
                  </a>
                  <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    onClick={() => handleRemoveAttachment(a.id)}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
