//frontend\src\api\checklistTemplate.js
import API from "./client";

/* LIST CHECKLIST ITEMS */
export const getChecklistItems = async () => {
  const { data } = await API.get("/checklist-template/");
  return data;
};

/* CREATE ITEM */
export const createChecklistItem = async (payload) => {
  const { data } = await API.post("/checklist-template/", payload);
  return data;
};

/* UPDATE ITEM */
export const updateChecklistItem = async (itemId, payload) => {
  const { data } = await API.put(`/checklist-template/${itemId}`, payload);
  return data;
};

/* DELETE ITEM */
export const deleteChecklistItem = async (itemId) => {
  const { data } = await API.delete(`/checklist-template/${itemId}`);
  return data;
};

/* RESET TO DEFAULTS */
export const resetChecklistToDefaults = async () => {
  const { data } = await API.post("/checklist-template/reset-defaults");
  return data;
};
