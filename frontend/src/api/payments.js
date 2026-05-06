//frontend\src\api\payments.js
import API from "./client";

export const recordPayment = async (payload) => {
  const { data } = await API.post("/payments/", payload);
  return data;
};

export const getPayments = async (tenantId = null, leaseId = null, propertyId = null) => {
  const params = {};
  if (tenantId) params.tenant_id = tenantId;
  if (leaseId) params.lease_id = leaseId;
  if (propertyId) params.property_id = propertyId;
  const { data } = await API.get("/payments/", { params });
  return data;
};

export const getPayment = async (paymentId) => {
  const { data } = await API.get(`/payments/${paymentId}`);
  return data;
};
