//frontend/src/features/payments/BatchPayments.jsx
//
// Batch payment upload + review (Sprint 4.5 spinoff).
//
// Sprint 7 cleanup:
//   - "Save X for review" button (Batch 3) — push unresolved rows into the
//     reconciliation queue.
//   - "Download Template" button — matches the pattern from bulk uploads.
//   - Save response now surfaces WHY items were skipped ("already in
//     review queue", "already recorded as a payment", etc.) so
//     "Saved 0" doesn't look like a bug when it's really dedup working.
//   - "Clear" button next to the file picker — retract a picked file
//     before previewing, or wipe an in-progress preview to start over.
//     Clears the file, preview, selections, lease choices, and any
//     error / result / saveResult banners. Also resets the underlying
//     <input type="file"> so the visible filename disappears (setting
//     state alone doesn't do this — the DOM element holds its own copy).
//
// Sprint 6.2 (#7) — deposit awareness:
//   - New status `insufficient_first_payment`: row matched a lease with an
//     outstanding deposit, but the row amount is less than the deposit
//     balance. Backend rejects on commit; UI blocks the checkbox and shows
//     the shortfall inline. Row is still savable to review so the landlord
//     can follow up with the tenant.
//   - Matched rows on leases with an outstanding deposit show a small
//     "will be split" hint so the landlord knows the payment will be
//     recorded as deposit + rent.

import { useRef, useState } from "react";
import {
  previewBatch,
  commitBatch,
  downloadBatchTemplate,
  downloadBlob,
} from "../../api/paymentBatch";
import { saveReviewItems } from "../../api/paymentReconciliation";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });

const STATUS_LABEL = {
  matched: "Matched",
  multiple_leases: "Choose lease",
  no_active_lease: "No active lease",
  unmatched: "Unmatched",
  duplicate: "Already recorded",
  parse_error: "Couldn't read",
  insufficient_first_payment: "Deposit not covered",
};

const SAVABLE_STATUSES = new Set([
  "unmatched",
  "multiple_leases",
  "no_active_lease",
  "insufficient_first_payment",
]);

export default function BatchPayments() {
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [selected, setSelected] = useState({});
  const [leaseChoice, setLeaseChoice] = useState({});
  const [notify, setNotify] = useState(false);
  const [loading, setLoading] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [savingForReview, setSavingForReview] = useState(false);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [saveResult, setSaveResult] = useState(null);

  const applyPreview = (data) => {
    setPreview(data);
    const sel = {};
    data.rows.forEach((r) => {
      if (r.status === "matched") sel[r.row] = true;
    });
    setSelected(sel);
    setLeaseChoice({});
  };

  const handleFile = (e) => {
    setFile(e.target.files[0] || null);
    setPreview(null);
    setResult(null);
    setSaveResult(null);
    setError("");
  };

  // Wipe file + preview + selections + banners. Also reset the file input
  // DOM node so its visible filename disappears — React state doesn't
  // control that; the <input type="file"> keeps its own value.
  const handleClear = () => {
    setFile(null);
    setPreview(null);
    setSelected({});
    setLeaseChoice({});
    setResult(null);
    setSaveResult(null);
    setError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDownloadTemplate = async () => {
    setTemplateLoading(true);
    try {
      const blob = await downloadBatchTemplate();
      downloadBlob(blob, "batch-payments-template.csv");
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to download template");
    } finally {
      setTemplateLoading(false);
    }
  };

  const runPreview = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    setSaveResult(null);
    try {
      const data = await previewBatch(file);
      applyPreview(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not read that file.");
    } finally {
      setLoading(false);
    }
  };

  const committable = (r) =>
    r.status === "matched" ||
    (r.status === "multiple_leases" && !!leaseChoice[r.row]);

  const toRecord = preview
    ? preview.rows.filter((r) => selected[r.row] && committable(r))
    : [];

  const savableRows = preview
    ? preview.rows.filter((r) => SAVABLE_STATUSES.has(r.status))
    : [];

  const runCommit = async () => {
    if (toRecord.length === 0) return;
    setCommitting(true);
    setError("");
    try {
      const payments = toRecord.map((r) => ({
        tenant_id: r.tenant_id,
        lease_id: r.status === "matched" ? r.lease_id : leaseChoice[r.row],
        amount: r.amount,
        reference: r.reference,
        payment_date: r.date,
      }));
      const res = await commitBatch(payments, notify);
      setResult(res);
      const data = await previewBatch(file);
      applyPreview(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not record payments.");
    } finally {
      setCommitting(false);
    }
  };

  const runSaveForReview = async () => {
    if (savableRows.length === 0) return;
    setSavingForReview(true);
    setError("");
    try {
      const items = savableRows.map((r) => ({
        amount: r.amount,
        payment_date: r.date,
        reference: r.reference,
        payer_phone: r.phone,
        payer_name: null,
        raw_transaction: r.raw,
        tenant_id: r.tenant_id,
        lease_id: null,
        flag_reason: r.status,
        notes: null,
      }));
      const res = await saveReviewItems(items);
      setSaveResult(res);
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not save for review.");
    } finally {
      setSavingForReview(false);
    }
  };

  const renderCheckbox = (r, canCommit) => (
    <input
      type="checkbox"
      disabled={!canCommit}
      checked={!!selected[r.row] && canCommit}
      onChange={(e) =>
        setSelected((prev) => ({ ...prev, [r.row]: e.target.checked }))
      }
    />
  );

  const renderLeaseControl = (r) => {
    if (r.status === "matched") return "✓";
    if (r.status === "multiple_leases") {
      return (
        <select
          className="input"
          value={leaseChoice[r.row] || ""}
          onChange={(e) =>
            setLeaseChoice((prev) => ({ ...prev, [r.row]: e.target.value }))
          }
        >
          <option value="">Select lease…</option>
          {r.lease_options.map((o) => (
            <option key={o.lease_id} value={o.lease_id}>
              {money(o.rent_amount)} / mo
              {o.deposit_outstanding
                ? ` — deposit unpaid: ${money(o.deposit_outstanding)}`
                : ""}
            </option>
          ))}
        </select>
      );
    }
    return "—";
  };

  // Short inline hint under the status badge — explains split-on-commit
  // for matched rows and the shortfall for insufficient rows.
  const renderStatusHint = (r) => {
    if (
      r.status === "matched" &&
      r.deposit_outstanding &&
      Number(r.amount) > Number(r.deposit_outstanding)
    ) {
      const rentPortion =
        Number(r.amount) - Number(r.deposit_outstanding);
      return (
        <div className="text-xs text-muted mt-xs">
          Will split: {money(r.deposit_outstanding)} deposit +{" "}
          {money(rentPortion)} rent
        </div>
      );
    }
    if (r.status === "matched" && r.deposit_outstanding) {
      return (
        <div className="text-xs text-muted mt-xs">
          Will apply to deposit
        </div>
      );
    }
    if (r.status === "insufficient_first_payment") {
      return (
        <div className="text-xs text-warning mt-xs">
          Deposit balance is {money(r.deposit_outstanding)}. First payment
          must cover it in full.
        </div>
      );
    }
    return null;
  };

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">Batch Payment Upload</div>

      <div className="dash-panel mb-md">
        <div className="dash-panel-title">Upload statement (CSV)</div>
        <p className="text-sm text-muted">
          Upload a bank / M-Pesa statement export. Each deposit is matched to a
          tenant by phone number. Nothing is recorded until you review and
          confirm below. Not sure of the format? Download the template first.
        </p>
        <div className="flex items-center gap-sm mt-sm flex-wrap">
          <button
            className="btn btn-secondary"
            onClick={handleDownloadTemplate}
            disabled={templateLoading}
          >
            {templateLoading ? "Preparing…" : "Download Template"}
          </button>
          <input
            type="file"
            accept=".csv"
            onChange={handleFile}
            ref={fileInputRef}
          />
          <button
            className="btn btn-primary"
            onClick={runPreview}
            disabled={!file || loading}
          >
            {loading ? "Reading…" : "Preview"}
          </button>
          {(file || preview) && (
            <button
              className="btn btn-secondary"
              onClick={handleClear}
              disabled={loading || committing || savingForReview}
              title="Clear the picked file and any preview"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="info-banner-warning mb-md">
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="dash-panel mb-md">
          <div className="text-bold">
            Recorded {result.created_count} payment(s)
            {result.skipped_count
              ? `, skipped ${result.skipped_count}`
              : ""}
            .
          </div>
          {result.skipped_count > 0 && (
            <ul className="text-sm text-muted mt-sm">
              {result.skipped.map((s, i) => (
                <li key={i}>
                  {s.reference || "—"}: {s.reason}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {saveResult && (
        <div className="dash-panel mb-md">
          <div className="text-bold">
            Saved {saveResult.saved_count} to review queue
            {saveResult.skipped_count
              ? `, skipped ${saveResult.skipped_count}`
              : ""}
            .
          </div>

          {saveResult.saved_count > 0 && (
            <p className="text-sm text-muted mt-sm">
              Head to <strong>Payment Review</strong> in the sidebar to resolve
              them — pick tenant/lease, apply, or reject.
            </p>
          )}

          {saveResult.skipped_count > 0 && (
            <>
              <p className="text-sm text-muted mt-sm">
                Skipped rows (already handled or not saveable):
              </p>
              <ul className="text-sm text-muted">
                {saveResult.skipped.map((s, i) => (
                  <li key={i}>
                    <strong>{s.reference || "—"}</strong>: {s.reason}
                  </li>
                ))}
              </ul>
              {saveResult.saved_count === 0 && (
                <p className="text-sm text-muted mt-sm">
                  If the rows are already in the queue, open{" "}
                  <strong>Payment Review</strong> to resolve them there.
                </p>
              )}
            </>
          )}
        </div>
      )}

      {preview && (
        <div className="dash-panel">
          <div className="dash-panel-title">
            Review — {preview.total_rows} row(s)
          </div>

          <div className="text-sm text-muted mb-sm">
            {Object.entries(preview.summary).map(([k, v]) => (
              <span key={k} className="mr-md">
                {STATUS_LABEL[k] || k}:{" "}
                <span className="text-bold">{v}</span>
              </span>
            ))}
          </div>

          <div className="batch-table-wrap hidden-mobile">
            <table className="staff-table">
              <thead>
                <tr>
                  <th></th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Phone</th>
                  <th>Reference</th>
                  <th>Tenant</th>
                  <th>Lease</th>
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((r) => {
                  const canCommit = committable(r);
                  return (
                    <tr key={r.row}>
                      <td>{renderCheckbox(r, canCommit)}</td>
                      <td>
                        <span className="role-badge">
                          {STATUS_LABEL[r.status] || r.status}
                        </span>
                        {renderStatusHint(r)}
                      </td>
                      <td>{r.date || "—"}</td>
                      <td>{r.amount != null ? money(r.amount) : "—"}</td>
                      <td>{r.phone || "—"}</td>
                      <td>{r.reference || "—"}</td>
                      <td>{r.tenant_name || "—"}</td>
                      <td>{renderLeaseControl(r)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="hidden-desktop batch-cards">
            {preview.rows.map((r) => {
              const canCommit = committable(r);
              return (
                <div key={r.row} className="card batch-card">
                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-sm">
                      {renderCheckbox(r, canCommit)}
                      <span className="role-badge">
                        {STATUS_LABEL[r.status] || r.status}
                      </span>
                    </label>
                    <span className="text-bold">
                      {r.amount != null ? money(r.amount) : "—"}
                    </span>
                  </div>

                  {renderStatusHint(r)}

                  <div className="text-sm">
                    <div>
                      <span className="text-muted">Tenant: </span>
                      {r.tenant_name || "—"}
                    </div>
                    <div>
                      <span className="text-muted">Date: </span>
                      {r.date || "—"}
                    </div>
                    <div>
                      <span className="text-muted">Phone: </span>
                      {r.phone || "—"}
                    </div>
                    <div>
                      <span className="text-muted">Reference: </span>
                      {r.reference || "—"}
                    </div>
                  </div>

                  {r.status === "matched" && (
                    <div className="text-sm text-muted">Lease matched ✓</div>
                  )}
                  {r.status === "multiple_leases" && (
                    <div>{renderLeaseControl(r)}</div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex items-center gap-sm mt-md flex-wrap">
            <label className="text-sm">
              <input
                type="checkbox"
                checked={notify}
                onChange={(e) => setNotify(e.target.checked)}
              />{" "}
              Send WhatsApp receipts
            </label>
            <button
              className="btn btn-primary"
              onClick={runCommit}
              disabled={committing || toRecord.length === 0}
            >
              {committing
                ? "Recording…"
                : `Record ${toRecord.length} selected`}
            </button>

            {savableRows.length > 0 && (
              <button
                className="btn btn-secondary"
                onClick={runSaveForReview}
                disabled={savingForReview}
                title="Move unresolved rows into the reconciliation queue for later"
              >
                {savingForReview
                  ? "Saving…"
                  : `Save ${savableRows.length} for review`}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
