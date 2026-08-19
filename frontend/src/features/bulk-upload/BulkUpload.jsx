//frontend\src\features\bulk-upload\BulkUpload.jsx
//
// Bulk Upload page (Sprint 7 cleanup, Batch 2).
//
// A single page with three panels — Properties, Units, Tenants — each with:
//   - "Download CSV Template" and "Download Excel Template" buttons
//   - a file picker + Upload button (accepts .csv and .xlsx)
//   - a results block showing imported / skipped counts with a
//     collapsible list of exactly which rows failed and why
//
// Skipped rows come back with a `reason` field the backend sets during
// per-row validation (missing required column, duplicate, bad number,
// unknown property, etc.). We surface every reason verbatim so the user
// can fix the file and re-upload rather than guess.

import { useState } from "react";
import { Link } from "react-router-dom";
import {
  downloadPropertiesTemplate,
  downloadPropertiesTemplateXlsx,
  downloadUnitsTemplate,
  downloadUnitsTemplateXlsx,
  downloadTenantsTemplate,
  downloadTenantsTemplateXlsx,
  uploadPropertiesCSV,
  uploadUnitsCSV,
  uploadTenantsCSV,
  previewTenantsCSV,
  downloadBlob,
} from "../../api/bulkUploads";

export default function BulkUpload() {
  return (
    <section className="properties-page">
      <div className="flex items-center gap-sm mb-sm">
        <Link to="/owner/dashboard" className="text-sm checklist-back-link">
          ← Dashboard
        </Link>
      </div>

      <div className="properties-header">
        <div>
          <h2>Bulk Upload</h2>
          <p className="text-muted text-sm">
            Import properties, units, and tenants from CSV or Excel files.
            Download a template, fill it in, then upload. Invalid rows are
            skipped and reported — valid rows still get imported.
          </p>
        </div>
      </div>

      <div className="card detail-card mt-md">
        <BulkUploadPanel
          title="Properties"
          description={
            "Import multiple properties at once. Each property needs a name, " +
            "address, city, and country. Property names must be unique within " +
            "your organization."
          }
          templateCsvFn={downloadPropertiesTemplate}
          templateCsvFilename="properties-template.csv"
          templateXlsxFn={downloadPropertiesTemplateXlsx}
          templateXlsxFilename="properties-template.xlsx"
          uploadFn={uploadPropertiesCSV}
        />
      </div>

      <div className="card detail-card mt-md">
        <BulkUploadPanel
          title="Units"
          description={
            "Import multiple units at once. Each unit references its property " +
            "by name (property_name column), so make sure the property already " +
            "exists — upload properties first if you're starting fresh. " +
            "Required columns: property_name, name, rent_amount."
          }
          templateCsvFn={downloadUnitsTemplate}
          templateCsvFilename="units-template.csv"
          templateXlsxFn={downloadUnitsTemplateXlsx}
          templateXlsxFilename="units-template.xlsx"
          uploadFn={uploadUnitsCSV}
        />
      </div>

      <div className="card detail-card mt-md">
        <TenantBulkUploadPanel
          title="Tenants"
          description={
            "Import multiple tenants at once. You can now include lease information " +
            "so tenants are onboarded with their units in one step. Each tenant needs " +
            "a full name and phone number. Phone numbers and emails must be unique " +
            "within your organization. Landlord phone numbers cannot be used. " +
            "When using Excel, set phone column cells to Text format before " +
            "entering numbers so leading zeros are preserved."
          }
          templateCsvFn={downloadTenantsTemplate}
          templateCsvFilename="tenants-template.csv"
          templateXlsxFn={downloadTenantsTemplateXlsx}
          templateXlsxFilename="tenants-template.xlsx"
        />
      </div>
    </section>
  );
}


/* ─── One upload panel ────────────────────────────────────────────── */

function BulkUploadPanel({
  title,
  description,
  templateCsvFn,
  templateCsvFilename,
  templateXlsxFn,
  templateXlsxFilename,
  uploadFn,
}) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [csvLoading, setCsvLoading] = useState(false);
  const [xlsxLoading, setXlsxLoading] = useState(false);

  const handleDownloadTemplate = async (fn, filename, setLoading) => {
    setLoading(true);
    try {
      const blob = await fn();
      downloadBlob(blob, filename);
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to download template");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0] || null);
    setResult(null);
    setError("");
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      const data = await uploadFn(file);
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h3>{title}</h3>
      <p className="text-sm text-muted">{description}</p>

      <div className="flex gap-sm items-center flex-wrap mt-md">
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => handleDownloadTemplate(templateCsvFn, templateCsvFilename, setCsvLoading)}
          disabled={csvLoading || xlsxLoading}
        >
          {csvLoading ? "Preparing…" : "CSV Template"}
        </button>

        <button
          className="btn btn-secondary btn-sm"
          onClick={() => handleDownloadTemplate(templateXlsxFn, templateXlsxFilename, setXlsxLoading)}
          disabled={csvLoading || xlsxLoading}
        >
          {xlsxLoading ? "Preparing…" : "Excel Template"}
        </button>

        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={handleFileChange}
          disabled={uploading}
        />

        <button
          className="btn btn-primary btn-sm"
          onClick={handleUpload}
          disabled={!file || uploading}
        >
          {uploading ? "Uploading…" : "Upload"}
        </button>
      </div>

      {error && (
        <div className="error-text mt-sm">{error}</div>
      )}

      {result && (
        <div className="mt-md">
          <div className="text-sm">
            <strong style={{ color: "#16a34a" }}>{result.imported_count}</strong>{" "}
            imported ·{" "}
            <strong style={{ color: result.skipped_count > 0 ? "#dc2626" : "#6b7280" }}>
              {result.skipped_count}
            </strong>{" "}
            skipped · {result.total_rows} data row{result.total_rows === 1 ? "" : "s"} in file
          </div>

          {result.imported.length > 0 && (
            <details className="mt-sm">
              <summary
                className="text-sm"
                style={{ cursor: "pointer", color: "#16a34a" }}
              >
                ✓ Imported ({result.imported.length})
              </summary>
              <ul style={{ paddingLeft: "1.5rem", fontSize: "0.875rem", marginTop: 4 }}>
                {result.imported.map((r) => (
                  <li key={`imp-${r.row_number}`}>
                    Row {r.row_number}: {r.identifier}
                  </li>
                ))}
              </ul>
            </details>
          )}

          {result.skipped.length > 0 && (
            <details open className="mt-sm">
              <summary
                className="text-sm"
                style={{ cursor: "pointer", color: "#dc2626" }}
              >
                ✗ Skipped ({result.skipped.length})
              </summary>
              <ul style={{ paddingLeft: "1.5rem", fontSize: "0.875rem", marginTop: 4 }}>
                {result.skipped.map((r) => (
                  <li key={`skp-${r.row_number}`}>
                    Row {r.row_number}: <strong>{r.identifier}</strong> — {r.reason}
                  </li>
                ))}
              </ul>
            </details>
          )}

          {result.imported_count > 0 && (
            <p className="text-sm text-muted mt-sm">
              Refresh the {title.toLowerCase()} list page to see the imported rows.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Tenant upload panel with preview ────────────────────────────── */

function TenantBulkUploadPanel({
  title,
  description,
  templateCsvFn,
  templateCsvFilename,
  templateXlsxFn,
  templateXlsxFilename,
}) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [csvLoading, setCsvLoading] = useState(false);
  const [xlsxLoading, setXlsxLoading] = useState(false);
  const [preview, setPreview] = useState(null);

  const handleDownloadTemplate = async (fn, filename, setLoading) => {
    setLoading(true);
    try {
      const blob = await fn();
      downloadBlob(blob, filename);
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to download template");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0] || null);
    setResult(null);
    setError("");
    setPreview(null);
  };

  const handlePreview = async () => {
    if (!file) return;
    setPreviewing(true);
    setError("");
    setPreview(null);
    try {
      const data = await previewTenantsCSV(file);
      setPreview(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Preview failed");
    } finally {
      setPreviewing(false);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      const data = await uploadTenantsCSV(file);
      setResult(data);
      setPreview(null);
    } catch (err) {
      setError(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const formatCurrency = (value) => {
    if (!value && value !== 0) return "";
    const num = parseFloat(value);
    if (isNaN(num)) return value;
    return `KES ${num.toLocaleString("en-KE")}`;
  };

  const formatDate = (value) => {
    if (!value) return "";
    const d = new Date(value + "T00:00:00");
    if (isNaN(d.getTime())) return value;
    return d.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <div>
      <h3>{title}</h3>
      <p className="text-sm text-muted">{description}</p>

      <div className="flex gap-sm items-center flex-wrap mt-md">
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => handleDownloadTemplate(templateCsvFn, templateCsvFilename, setCsvLoading)}
          disabled={csvLoading || xlsxLoading}
        >
          {csvLoading ? "Preparing…" : "CSV Template"}
        </button>

        <button
          className="btn btn-secondary btn-sm"
          onClick={() => handleDownloadTemplate(templateXlsxFn, templateXlsxFilename, setXlsxLoading)}
          disabled={csvLoading || xlsxLoading}
        >
          {xlsxLoading ? "Preparing…" : "Excel Template"}
        </button>

        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={handleFileChange}
          disabled={uploading || previewing}
        />

        <button
          className="btn btn-secondary btn-sm"
          onClick={handlePreview}
          disabled={!file || previewing || uploading}
        >
          {previewing ? "Previewing…" : "Preview"}
        </button>

        <button
          className="btn btn-primary btn-sm"
          onClick={handleUpload}
          disabled={!file || uploading || previewing}
        >
          {uploading ? "Uploading…" : "Confirm & Upload"}
        </button>
      </div>

      {error && (
        <div className="error-text mt-sm">{error}</div>
      )}

      {preview && (
        <div className="mt-md">
          <div className="text-sm mb-sm">
            <strong style={{ color: "#16a34a" }}>{preview.ready_count}</strong>{" "}
            ready ·{" "}
            <strong style={{ color: preview.error_count > 0 ? "#dc2626" : "#6b7280" }}>
              {preview.error_count}
            </strong>{" "}
            errors · {preview.total_rows} data row{preview.total_rows === 1 ? "" : "s"} in file
          </div>

          {preview.rows.length > 0 && (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #e5e7eb", textAlign: "left" }}>
                    <th style={{ padding: "0.5rem" }}>Row</th>
                    <th style={{ padding: "0.5rem" }}>Tenant</th>
                    <th style={{ padding: "0.5rem" }}>Unit</th>
                    <th style={{ padding: "0.5rem" }}>Rent</th>
                    <th style={{ padding: "0.5rem" }}>Deposit</th>
                    <th style={{ padding: "0.5rem" }}>Start Date</th>
                    <th style={{ padding: "0.5rem" }}>End Date</th>
                    <th style={{ padding: "0.5rem" }}>Billing Day</th>
                    <th style={{ padding: "0.5rem" }}>Status</th>
                    <th style={{ padding: "0.5rem" }}>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.map((r) => (
                    <tr key={r.row_number} style={{ borderBottom: "1px solid #f3f4f6" }}>
                      <td style={{ padding: "0.5rem" }}>{r.row_number}</td>
                      <td style={{ padding: "0.5rem" }}>{r.identifier}</td>
                      <td style={{ padding: "0.5rem" }}>{r.unit_name || "—"}</td>
                      <td style={{ padding: "0.5rem" }}>{formatCurrency(r.rent_amount)}</td>
                      <td style={{ padding: "0.5rem" }}>{formatCurrency(r.deposit_amount)}</td>
                      <td style={{ padding: "0.5rem" }}>{formatDate(r.start_date)}</td>
                      <td style={{ padding: "0.5rem" }}>{formatDate(r.end_date)}</td>
                      <td style={{ padding: "0.5rem" }}>{r.billing_day || "—"}</td>
                      <td style={{ padding: "0.5rem" }}>{r.lease_status || "—"}</td>
                      <td style={{ padding: "0.5rem" }}>
                        {r.status === "ready" ? (
                          <span style={{ color: "#16a34a", fontWeight: 500 }}>READY</span>
                        ) : (
                          <span style={{ color: "#dc2626", fontWeight: 500 }}>ERROR: {r.reason}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {result && (
        <div className="mt-md">
          <div className="text-sm">
            <strong style={{ color: "#16a34a" }}>{result.imported_count}</strong>{" "}
            imported ·{" "}
            <strong style={{ color: result.skipped_count > 0 ? "#dc2626" : "#6b7280" }}>
              {result.skipped_count}
            </strong>{" "}
            skipped · {result.total_rows} data row{result.total_rows === 1 ? "" : "s"} in file
          </div>

          {result.imported.length > 0 && (
            <details className="mt-sm">
              <summary
                className="text-sm"
                style={{ cursor: "pointer", color: "#16a34a" }}
              >
                ✓ Imported ({result.imported.length})
              </summary>
              <ul style={{ paddingLeft: "1.5rem", fontSize: "0.875rem", marginTop: 4 }}>
                {result.imported.map((r) => (
                  <li key={`imp-${r.row_number}`}>
                    Row {r.row_number}: {r.identifier}
                    {r.unit_name && ` → ${r.unit_name}`}
                    {r.rent_amount && ` (Rent: ${formatCurrency(r.rent_amount)})`}
                  </li>
                ))}
              </ul>
            </details>
          )}

          {result.skipped.length > 0 && (
            <details open className="mt-sm">
              <summary
                className="text-sm"
                style={{ cursor: "pointer", color: "#dc2626" }}
              >
                ✗ Skipped ({result.skipped.length})
              </summary>
              <ul style={{ paddingLeft: "1.5rem", fontSize: "0.875rem", marginTop: 4 }}>
                {result.skipped.map((r) => (
                  <li key={`skp-${r.row_number}`}>
                    Row {r.row_number}: <strong>{r.identifier}</strong> — {r.reason}
                  </li>
                ))}
              </ul>
            </details>
          )}

          {result.imported_count > 0 && (
            <p className="text-sm text-muted mt-sm">
              Refresh the {title.toLowerCase()} list page to see the imported rows.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
