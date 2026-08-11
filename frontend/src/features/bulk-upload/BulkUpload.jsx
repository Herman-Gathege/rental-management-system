//frontend\src\features\bulk-upload\BulkUpload.jsx
//
// Bulk Upload page (Sprint 7 cleanup, Batch 2).
//
// A single page with two panels — Properties and Units — each with:
//   - a "Download Template" button that saves a CSV with the correct
//     headers and a couple of example rows
//   - a file picker + Upload button
//   - a results block showing imported / skipped counts with a
//     collapsible list of exactly which rows failed and why
//
// Skipped rows come back with a `reason` field the backend sets during
// per-row validation (missing required column, duplicate, bad number,
// unknown property, etc.). We surface every reason verbatim so the user
// can fix the CSV and re-upload rather than guess.

import { useState } from "react";
import { Link } from "react-router-dom";
import {
  downloadPropertiesTemplate,
  downloadUnitsTemplate,
  downloadTenantsTemplate,
  uploadPropertiesCSV,
  uploadUnitsCSV,
  uploadTenantsCSV,
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
            Import properties, units, and tenants from CSV files. Download a
            template, fill it in, then upload. Invalid rows are skipped and
            reported — valid rows still get imported.
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
          templateFn={downloadPropertiesTemplate}
          templateFilename="properties-template.csv"
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
          templateFn={downloadUnitsTemplate}
          templateFilename="units-template.csv"
          uploadFn={uploadUnitsCSV}
        />
      </div>

      <div className="card detail-card mt-md">
        <BulkUploadPanel
          title="Tenants"
          description={
            "Import multiple tenants at once. Each tenant needs a full name " +
            "and phone number. Phone numbers and emails must be unique within " +
            "your organization. Landlord phone numbers cannot be used."
          }
          templateFn={downloadTenantsTemplate}
          templateFilename="tenants-template.csv"
          uploadFn={uploadTenantsCSV}
        />
      </div>
    </section>
  );
}


/* ─── One upload panel ────────────────────────────────────────────── */

function BulkUploadPanel({ title, description, templateFn, templateFilename, uploadFn }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [templateLoading, setTemplateLoading] = useState(false);

  const handleDownloadTemplate = async () => {
    setTemplateLoading(true);
    try {
      const blob = await templateFn();
      downloadBlob(blob, templateFilename);
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to download template");
    } finally {
      setTemplateLoading(false);
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
          onClick={handleDownloadTemplate}
          disabled={templateLoading}
        >
          {templateLoading ? "Preparing…" : "Download Template"}
        </button>

        <input
          type="file"
          accept=".csv,text/csv"
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
