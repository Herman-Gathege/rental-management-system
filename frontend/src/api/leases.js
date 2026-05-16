//frontend\src\api\leases.js

import API from "./client";

/* CREATE LEASE */
export const createLease = async (payload) => {
  const { data } = await API.post("/leases/", payload);
  return data;
};

/* LIST LEASES */
export const getLeases = async (filters = {}) => {
  const { data } = await API.get("/leases/", { params: filters });
  return data;
};

/* GET ONE LEASE */
export const getLease = async (leaseId) => {
  const { data } = await API.get(`/leases/${leaseId}`);
  return data;
};

/* UPDATE LEASE */
export const updateLease = async (leaseId, payload) => {
  const { data } = await API.put(`/leases/${leaseId}`, payload);
  return data;
};

/* TERMINATE LEASE */
export const terminateLease = async (leaseId) => {
  const { data } = await API.post(`/leases/${leaseId}/terminate`);
  return data;
};

/* UPLOAD SIGNED LEASE DOCUMENT */
export const uploadSignedLease = async (leaseId, file) => {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await API.post(
    `/leases/${leaseId}/signed-document`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
};
