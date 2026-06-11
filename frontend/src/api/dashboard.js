//frontend/src/api/dashboard.js
//
// API client for the role-based dashboard endpoints (Sprint 4.5).
// Mirrors the other api/*.js modules: import the shared axios instance
// (which attaches the bearer token automatically) and expose one function
// per endpoint. Covers manager / owner / finance / tenant.

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

export const getManagerUnits = async () => {
  const res = await API.get("/dashboard/manager/units");
  return res.data;
};

export const getManagerTenants = async () => {
  const res = await API.get("/dashboard/manager/tenants");
  return res.data;
};

export const getManagerLeases = async () => {
  const res = await API.get("/dashboard/manager/leases");
  return res.data;
};

/* ─── Owner / Landlord ─── */

export const getOwnerSummary = async () => {
  const res = await API.get("/dashboard/owner/summary");
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

export const getTenantInspections = async () => {
  const res = await API.get("/dashboard/tenant/inspections");
  return res.data;
};
