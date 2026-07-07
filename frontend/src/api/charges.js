//frontend\src\api\charges.js
import API from "./client";

export const generateMonthlyCharges = async (billingDate = null) => {
  const params = billingDate ? { billing_date: billingDate } : {};
  const { data } = await API.post("/charges/generate-monthly", null, { params });
  return data;
};

// getCharges supports optional pagination. When `limit` is passed, the backend
// returns { items, total, limit, offset }; otherwise a bare array (backward
// compatible). Callers that pass a limit should read `.items`/`.total`.
export const getCharges = async (
  status = null,
  leaseId = null,
  propertyId = null,
  limit = null,
  offset = null
) => {
  const params = {};
  if (status) params.status = status;
  if (leaseId) params.lease_id = leaseId;
  if (propertyId) params.property_id = propertyId;
  if (limit != null) params.limit = limit;
  if (offset != null) params.offset = offset;
  const { data } = await API.get("/charges/", { params });
  return data;
};

export const getCharge = async (chargeId) => {
  const { data } = await API.get(`/charges/${chargeId}`);
  return data;
};