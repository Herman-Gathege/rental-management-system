//frontend/src/api/paymentBatch.js
//
// Batch payment upload API. Landlord + Finance only (backend enforces).

import API from "./client";

// ─── Preview: upload CSV, get matched/flagged report (no writes) ───

export const previewBatch = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await API.post("/payments/batch/preview", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

// ─── Commit: record the rows the user confirmed ───

export const commitBatch = async (payments, notify = false) => {
  const { data } = await API.post("/payments/batch/commit", {
    payments,
    notify,
  });
  return data;
};

// ─── Template download (Sprint 7 cleanup) ───
//
// Returns a Blob; use downloadBlob() below to save it to disk.

export const downloadBatchTemplate = async () => {
  const response = await API.get("/payments/batch/template", {
    responseType: "blob",
  });
  return response.data;
};

// ─── Browser download helper ────────────────────────────────────────

export const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};
