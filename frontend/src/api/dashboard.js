//frontend/src/api/dashboard.js
//
// API client for the role-based dashboard endpoints (Sprint 4.5).
// Mirrors the other api/*.js modules: import the shared axios instance
// (which attaches the bearer token automatically) and expose one function
// per endpoint. Covers manager / owner / finance / tenant.
//
// Summary + recent-payments calls accept an optional propertyId to scope the
// figures to a single property (omit / null = all, per the property switcher).

import API from "./client";

// Build axios params only when a property is selected (null/undefined = all).
const propParams = (propertyId) =>
  propertyId ? { params: { property_id: propertyId } } : undefined;

/* ─── Property Manager ─── */

export const getManagerSummary = async (propertyId) => {
  const res = await API.get("/dashboard/manager/summary", propParams(propertyId));
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

export const getOwnerSummary = async (propertyId) => {
  const res = await API.get("/dashboard/owner/summary", propParams(propertyId));
  return res.data;
};

/* ─── Finance ─── */

export const getFinanceSummary = async (propertyId) => {
  const res = await API.get("/dashboard/finance/summary", propParams(propertyId));
  return res.data;
};

export const getFinanceRecentPayments = async (propertyId) => {
  const res = await API.get(
    "/dashboard/finance/recent-payments",
    propParams(propertyId)
  );
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
