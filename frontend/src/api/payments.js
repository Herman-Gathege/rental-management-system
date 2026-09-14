//frontend\src\api\payments.js
import API from "./client";

export const recordPayment = async (payload) => {
  const { data } = await API.post("/payments/", payload);
  return data;
};

// getPayments supports optional pagination. When `limit` is passed, the backend
// returns { items, total, limit, offset }; otherwise it returns a bare array
// (backward compatible). Callers that pass a limit should read `.items`/`.total`.
export const getPayments = async (
  tenantId = null,
  leaseId = null,
  propertyId = null,
  limit = null,
  offset = null
) => {
  const params = {};
  if (tenantId) params.tenant_id = tenantId;
  if (leaseId) params.lease_id = leaseId;
  if (propertyId) params.property_id = propertyId;
  if (limit != null) params.limit = limit;
  if (offset != null) params.offset = offset;
  const { data } = await API.get("/payments/", { params });
  return data;
};

export const getPayment = async (paymentId) => {
  const { data } = await API.get(`/payments/${paymentId}`);
  return data;
};

// Filter-object variant used by the payment history page. Kept separate from
// getPayments() so the existing positional callers (dashboards, tenant portal)
// are untouched.
export const queryPayments = async ({
  tenantId = null,
  leaseId = null,
  propertyId = null,
  paymentType = null,
  paymentMethod = null,
  startDate = null,
  endDate = null,
  limit = null,
  offset = null,
} = {}) => {
  const params = {};
  if (tenantId) params.tenant_id = tenantId;
  if (leaseId) params.lease_id = leaseId;
  if (propertyId) params.property_id = propertyId;
  if (paymentType) params.payment_type = paymentType;
  if (paymentMethod) params.payment_method = paymentMethod;
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  if (limit != null) params.limit = limit;
  if (offset != null) params.offset = offset;
  const { data } = await API.get("/payments/", { params });
  return data;
};
