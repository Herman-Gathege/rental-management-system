// frontend/src/api/search.js
//
// Global search (Ctrl+K palette). Results are already permission-scoped by the
// backend, so the frontend never has to filter for authorisation.

import API from "./client";

export const globalSearch = async ({ query, propertyId = null, signal } = {}) => {
  const params = { q: query };
  if (propertyId) params.property_id = propertyId;
  const { data } = await API.get("/search", { params, signal });
  return data;
};
