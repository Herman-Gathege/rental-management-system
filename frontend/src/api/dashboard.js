//frontend/src/api/dashboard.js
//
// API client for the role-based dashboard endpoints (Sprint 4.5).
// Mirrors the other api/*.js modules: import the shared axios instance
// (which attaches the bearer token automatically) and expose one function
// per endpoint. Covers manager / finance / tenant so we don't touch this
// file again in the next two chunks.

import API from "./client";

/* ─── Property Manager ─── */

export const getManagerSummary = async () => {
  const res = await API.get("/dashboard/manager/summary");
  return res.data;
};

export const getManagerProperties = async () => {
  const res = await API.get("/dashboard/manager/properties");
  return res.data;
};

/* ─── Finance ─── */

export const getFinanceSummary = async () => {
  const res = await API.get("/dashboard/finance/summary");
  return res.data;
};

export const getFinanceRecentPayments = async () => {
  const res = await API.get("/dashboard/finance/recent-payments");
  return res.data;
};

/* ─── Tenant ─── */

export const getTenantDashboard = async () => {
  const res = await API.get("/dashboard/tenant/me");
  return res.data;
};

export const getTenantPayments = async () => {
  const res = await API.get("/dashboard/tenant/payments");
  return res.data;
};

export const getTenantCharges = async () => {
  const res = await API.get("/dashboard/tenant/charges");
  return res.data;
};