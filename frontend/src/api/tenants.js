//frontend\src\api\tenants.js

import API from "./client";

/* CREATE TENANT */
export const createTenant = async (payload) => {
  const { data } = await API.post("/tenants/", payload);
  return data;
};

/* LIST TENANTS */
export const getTenants = async (search = null) => {
  const params = search ? { search } : {};
  const { data } = await API.get("/tenants/", { params });
  return data;
};

/* GET ONE TENANT */
export const getTenant = async (tenantId) => {
  const { data } = await API.get(`/tenants/${tenantId}`);
  return data;
};

/* UPDATE TENANT */
export const updateTenant = async (tenantId, payload) => {
  const { data } = await API.put(`/tenants/${tenantId}`, payload);
  return data;
};

/* DELETE TENANT */
export const deleteTenant = async (tenantId) => {
  const { data } = await API.delete(`/tenants/${tenantId}`);
  return data;
};

/* ─── DOCUMENTS ─── */

/* UPLOAD DOCUMENT (multipart form) */
export const uploadTenantDocument = async (tenantId, documentType, file) => {
  const formData = new FormData();
  formData.append("document_type", documentType);
  formData.append("file", file);

  const { data } = await API.post(
    `/tenants/${tenantId}/documents`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
};

/* LIST DOCUMENTS */
export const getTenantDocuments = async (tenantId) => {
  const { data } = await API.get(`/tenants/${tenantId}/documents`);
  return data;
};

/* DELETE DOCUMENT */
export const deleteTenantDocument = async (tenantId, documentId) => {
  const { data } = await API.delete(`/tenants/${tenantId}/documents/${documentId}`);
  return data;
};

