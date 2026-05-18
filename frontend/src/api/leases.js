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

/* INITIATE MOVE-OUT
   Creates a draft move-out inspection. Lease stays 'active' until
   the move-out inspection is signed. */
export const initiateMoveOut = async (leaseId) => {
  const { data } = await API.post(`/leases/${leaseId}/initiate-move-out`);
  return data;
};

/* TERMINATE LEASE — direct termination, requires signed move-out inspection */
export const terminateLease = async (leaseId) => {
  const { data } = await API.post(`/leases/${leaseId}/terminate`);
  return data;
};

/* UPLOAD SIGNED LEASE DOCUMENT */
// export const uploadSignedLease = async (leaseId, file) => {
//   const formData = new FormData();
//   formData.append("file", file);

//   const { data } = await API.post(
//     `/leases/${leaseId}/signed-document`,
//     formData,
//     { headers: { "Content-Type": "multipart/form-data" } }
//   );
//   return data;
// };

/* UPLOAD SIGNED LEASE DOCUMENTS */
export const uploadSignedLease = async (leaseId, files) => {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  const { data } = await API.post(
    `/leases/${leaseId}/signed-document`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return data;
};
