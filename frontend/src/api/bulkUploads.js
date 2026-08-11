//frontend\src\api\bulkUploads.js
//
// Bulk upload API — properties, units, tenants. Landlord-only backend; the
// nav link should already be gated so this is called with the
// right role.

import API from "./client";

// ─── Template downloads ─────────────────────────────────────────────

export const downloadPropertiesTemplate = async () => {
  const response = await API.get("/bulk-uploads/properties/template", {
    responseType: "blob",
  });
  return response.data;
};

export const downloadUnitsTemplate = async () => {
  const response = await API.get("/bulk-uploads/units/template", {
    responseType: "blob",
  });
  return response.data;
};

export const downloadTenantsTemplate = async () => {
  const response = await API.get("/bulk-uploads/tenants/template", {
    responseType: "blob",
  });
  return response.data;
};

// ─── Uploads ────────────────────────────────────────────────────────

export const uploadPropertiesCSV = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await API.post("/bulk-uploads/properties", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const uploadUnitsCSV = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await API.post("/bulk-uploads/units", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const uploadTenantsCSV = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await API.post("/bulk-uploads/tenants", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

// ─── Browser download helper ────────────────────────────────────────

// Wraps a Blob in the standard "create link, click, revoke" download
// dance. Used by BulkUpload.jsx to save the template CSV to disk.
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
