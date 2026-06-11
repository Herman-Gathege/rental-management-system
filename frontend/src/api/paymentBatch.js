//frontend/src/api/paymentBatch.js
//
// API client for CSV batch payment upload (Sprint 4.5 spinoff).
// preview = dry-run match report (no writes); commit = record confirmed rows.

import API from "./client";

export const previewBatch = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  // Let axios set the multipart Content-Type (with boundary) itself.
  const res = await API.post("/payments/batch/preview", formData);
  return res.data;
};

export const commitBatch = async (payments, notify = false) => {
  const res = await API.post("/payments/batch/commit", { payments, notify });
  return res.data;
};
