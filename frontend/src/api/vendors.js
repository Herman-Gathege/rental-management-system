//frontend\src\api\vendors.js

import API from "./client";

export const getVendors = async () => {
  const { data } = await API.get("/vendors/");
  return data;
};

export const createVendor = async (payload) => {
  const { data } = await API.post("/vendors/", payload);
  return data;
};

export const updateVendor = async (id, payload) => {
  const { data } = await API.put(`/vendors/${id}`, payload);
  return data;
};

export const deleteVendor = async (id) => {
  const { data } = await API.delete(`/vendors/${id}`);
  return data;
};
