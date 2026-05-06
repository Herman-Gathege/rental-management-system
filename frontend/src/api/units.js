//frontend\src\api\units.js
import API from "./client";

export const createUnit = async (payload) => {
  const { data } = await API.post("/units/", payload);
  return data;
};

export const getUnits = async (propertyId = null) => {
  const params = propertyId ? { property_id: propertyId } : {};
  const { data } = await API.get("/units/", { params });
  return data;
};

export const getUnit = async (unitId) => {
  const { data } = await API.get(`/units/${unitId}`);
  return data;
};

export const updateUnit = async (unitId, payload) => {
  const { data } = await API.put(`/units/${unitId}`, payload);
  return data;
};

export const deleteUnit = async (unitId) => {
  const { data } = await API.delete(`/units/${unitId}`);
  return data;
};
