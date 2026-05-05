//frontend\src\api\leases.js

import API from "./client";

export const createLease = async (payload) => {
  const { data } = await API.post("/leases/", payload);
  return data;
};

export const getLeases = async (status = null, propertyId = null) => {
  const params = {};
  if (status) params.status = status;
  if (propertyId) params.property_id = propertyId;
  const { data } = await API.get("/leases/", { params });
  return data;
};

export const getLease = async (leaseId) => {
  const { data } = await API.get(`/leases/${leaseId}`);
  return data;
};

export const updateLease = async (leaseId, payload) => {
  const { data } = await API.put(`/leases/${leaseId}`, payload);
  return data;
};

export const terminateLease = async (leaseId) => {
  const { data } = await API.post(`/leases/${leaseId}/terminate`);
  return data;
};
