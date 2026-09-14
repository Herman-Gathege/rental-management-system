// frontend/src/api/settings.js
//
// Organisation settings — billing automation + communication channels.
// Landlord-only on the backend, so every call here is owner-scoped.

import API from "./client";

/* ─── Billing automation ─── */

export const getAutomationSettings = async () => {
  const { data } = await API.get("/settings/automation");
  return data;
};

export const updateAutomationSettings = async (payload) => {
  const { data } = await API.put("/settings/automation", payload);
  return data;
};

// Runs an automation immediately (idempotent — a second run the same day is a
// no-op and returns { already_completed: true }).
export const runAutomationNow = async (job, runDate = null) => {
  const params = { job };
  if (runDate) params.run_date = runDate;
  const { data } = await API.post("/settings/automation/run", null, { params });
  return data;
};

export const getAutomationHistory = async (limit = 20) => {
  const { data } = await API.get("/settings/automation/history", {
    params: { limit },
  });
  return data;
};

/* ─── Communication channels ─── */

export const getCommunicationSettings = async () => {
  const { data } = await API.get("/settings/communication");
  return data;
};

export const updateCommunicationSettings = async (payload) => {
  const { data } = await API.put("/settings/communication", payload);
  return data;
};
