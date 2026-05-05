//frontend\src\api\tenants.js

import API from "./client";

export const createTenant = async (payload) => {
  const { data } = await API.post("/tenants/", payload);
  return data;
};

export const getTenants = async (search = null) => {
  const params = search ? { search } : {};
  const { data } = await API.get("/tenants/", { params });
  return data;
};

export const getTenant = async (tenantId) => {
  const { data } = await API.get(`/tenants/${tenantId}`);
  return data;
};

export const updateTenant = async (tenantId, payload) => {
  const { data } = await API.put(`/tenants/${tenantId}`, payload);
  return data;
};

export const deleteTenant = async (tenantId) => {
  const { data } = await API.delete(`/tenants/${tenantId}`);
  return data;
};
