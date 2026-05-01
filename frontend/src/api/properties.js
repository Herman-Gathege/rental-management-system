/*frontend\src\api\properties.js*/

import API from "./client";

/* CREATE a property */
export const createProperty = async (payload) => {
  const { data } = await API.post("/properties/", payload);
  return data;
};

/* LIST all properties for current org */
export const getProperties = async () => {
  const { data } = await API.get("/properties/");
  return data;
};

/* GET single property details */
export const getProperty = async (propertyId) => {
  const { data } = await API.get(`/properties/${propertyId}`);
  return data;
};

/* ASSIGN manager to a property */
export const assignManager = async (propertyId, userId) => {
  const { data } = await API.post(`/properties/${propertyId}/assign-manager`, {
    user_id: userId,
  });
  return data;
};

/* REMOVE manager from a property */
export const removeManager = async (propertyId, userId) => {
  const { data } = await API.delete(
    `/properties/${propertyId}/remove-manager/${userId}`
  );
  return data;
};