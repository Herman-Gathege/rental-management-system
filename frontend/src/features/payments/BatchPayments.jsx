//frontend/src/features/payments/BatchPayments.jsx
//
// Batch payment upload + review (Sprint 4.5 spinoff).
// Upload a bank/M-Pesa statement CSV -> preview (matched/flagged, no writes) ->
// pick leases for multi-lease rows, tick which to record -> commit. Re-previews
// after commit so newly-recorded rows show as duplicates.

import { useState } from "react";
import { previewBatch, commitBatch } from "../../api/paymentBatch";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 0 });

const STATUS_LABEL = {
  matched: "Matched",
  multiple_leases: "Choose lease",
  no_active_lease: "No active lease",
  unmatched: "Unmatched",
  duplicate: "Already recorded",
  parse_error: "Couldn't read",
};

export default function BatchPayments() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [selected, setSelected] = useState({});
  const [leaseChoice, setLeaseChoice] = useState({});
  const [notify, setNotify] = useState(false);
  const [loading, setLoading] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

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
    setError("");
  };

  const runPreview = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
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
      // Re-preview so just-recorded rows now read as duplicates.
      const data = await previewBatch(file);
      applyPreview(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not record payments.");
    } finally {
      setCommitting(false);
    }
  };

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">Batch Payment Upload</div>

      <div className="dash-panel mb-md">
        <div className="dash-panel-title">Upload statement (CSV)</div>
        <p className="text-sm text-muted">
          Upload a bank / M-Pesa statement export. Each deposit is matched to a
          tenant by phone number. Nothing is recorded until you review and
          confirm below.
        </p>
        <div className="flex items-center gap-sm mt-sm">
          <input type="file" accept=".csv" onChange={handleFile} />
          <button
            className="btn btn-primary"
            onClick={runPreview}
            disabled={!file || loading}
          >
            {loading ? "Reading…" : "Preview"}
          </button>
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
                    <td>
                      <input
                        type="checkbox"
                        disabled={!canCommit}
                        checked={!!selected[r.row] && canCommit}
                        onChange={(e) =>
                          setSelected((prev) => ({
                            ...prev,
                            [r.row]: e.target.checked,
                          }))
                        }
                      />
                    </td>
                    <td>
                      <span className="role-badge">
                        {STATUS_LABEL[r.status] || r.status}
                      </span>
                    </td>
                    <td>{r.date || "—"}</td>
                    <td>{r.amount != null ? money(r.amount) : "—"}</td>
                    <td>{r.phone || "—"}</td>
                    <td>{r.reference || "—"}</td>
                    <td>{r.tenant_name || "—"}</td>
                    <td>
                      {r.status === "matched" && "✓"}
                      {r.status === "multiple_leases" && (
                        <select
                          className="input"
                          value={leaseChoice[r.row] || ""}
                          onChange={(e) =>
                            setLeaseChoice((prev) => ({
                              ...prev,
                              [r.row]: e.target.value,
                            }))
                          }
                        >
                          <option value="">Select lease…</option>
                          {r.lease_options.map((o) => (
                            <option key={o.lease_id} value={o.lease_id}>
                              {money(o.rent_amount)} / mo
                            </option>
                          ))}
                        </select>
                      )}
                      {!["matched", "multiple_leases"].includes(r.status) && "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="flex items-center gap-sm mt-md">
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
          </div>
        </div>
      )}
    </div>
  );
}
