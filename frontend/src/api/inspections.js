//frontend\src\api\inspections.js
import API from "./client";

/* GET INSPECTION */
export const getInspection = async (inspectionId) => {
  const { data } = await API.get(`/inspections/${inspectionId}`);
  return data;
};

/* UPDATE ITEM (condition, comments, deduction) */
export const updateInspectionItem = async (inspectionId, itemId, payload) => {
  const { data } = await API.put(
    `/inspections/${inspectionId}/items/${itemId}`,
    payload
  );
  return data;
};

/* UPLOAD PHOTO */
export const uploadInspectionPhoto = async (inspectionId, itemId, file) => {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await API.post(
    `/inspections/${inspectionId}/items/${itemId}/photos`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
};

/* REMOVE PHOTO */
export const removeInspectionPhoto = async (inspectionId, itemId, url) => {
  const { data } = await API.delete(
    `/inspections/${inspectionId}/items/${itemId}/photos`,
    { params: { url } }
  );
  return data;
};

/* SIGN INSPECTION (locks it) */
export const signInspection = async (inspectionId, payload) => {
  const { data } = await API.post(`/inspections/${inspectionId}/sign`, payload);
  return data;
};

/* ADD NOTE (post-signature) */
export const addInspectionNote = async (inspectionId, note) => {
  const { data } = await API.post(`/inspections/${inspectionId}/notes`, { note });
  return data;
};
