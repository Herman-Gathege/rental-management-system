//frontend\src\api\expenses.js

import API from "./client";

/* ─── Expenses CRUD ─── */

export const getExpenses = async (filters = {}) => {
  const params = {};
  if (filters.status) params.status = filters.status;
  if (filters.property_id) params.property_id = filters.property_id;
  if (filters.category_id) params.category_id = filters.category_id;
  if (filters.vendor_id) params.vendor_id = filters.vendor_id;
  const { data } = await API.get("/expenses/", { params });
  return data;
};

export const getExpense = async (id) => {
  const { data } = await API.get(`/expenses/${id}`);
  return data;
};

export const createExpense = async (payload) => {
  const { data } = await API.post("/expenses/", payload);
  return data;
};

export const updateExpense = async (id, payload) => {
  const { data } = await API.put(`/expenses/${id}`, payload);
  return data;
};

export const deleteExpense = async (id) => {
  const { data } = await API.delete(`/expenses/${id}`);
  return data;
};

/* ─── Workflow transitions ─── */

export const submitExpense = async (id) => {
  const { data } = await API.post(`/expenses/${id}/submit`);
  return data;
};

export const approveExpense = async (id) => {
  const { data } = await API.post(`/expenses/${id}/approve`);
  return data;
};

export const rejectExpense = async (id, reason = null) => {
  const { data } = await API.post(`/expenses/${id}/reject`, { reason });
  return data;
};

export const payExpense = async (id, payload = {}) => {
  const { data } = await API.post(`/expenses/${id}/pay`, payload);
  return data;
};

/* ─── Attachments (receipts) ─── */

export const uploadExpenseAttachment = async (expenseId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await API.post(
    `/expenses/${expenseId}/attachments`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
};

export const deleteExpenseAttachment = async (expenseId, attachmentId) => {
  const { data } = await API.delete(
    `/expenses/${expenseId}/attachments/${attachmentId}`
  );
  return data;
};

/* ─── Reports ─── */

export const getExpenseSummary = async (params = {}) => {
  const { data } = await API.get("/reports/expenses/summary", { params });
  return data;
};

export const getExpensesByCategory = async (params = {}) => {
  const { data } = await API.get("/reports/expenses/by-category", { params });
  return data;
};

export const getExpensesByVendor = async (params = {}) => {
  const { data } = await API.get("/reports/expenses/by-vendor", { params });
  return data;
};

export const getMonthlyExpenses = async (params = {}) => {
  const { data } = await API.get("/reports/expenses/monthly", { params });
  return data;
};

export const getProfitByProperty = async (params = {}) => {
  const { data } = await API.get("/reports/profit-by-property", { params });
  return data;
};

export const getNOI = async (params = {}) => {
  const { data } = await API.get("/reports/noi", { params });
  return data;
};
