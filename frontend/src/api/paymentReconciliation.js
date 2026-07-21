//frontend\src\api\paymentReconciliation.js
//
// Payment reconciliation API — Sprint 7 cleanup (Batch 3).
//
// Landlord + Finance can call these. Backend enforces the role check;
// UI should still gate the nav link and page mount to those two.

import API from "./client";

// Bulk save flagged items — usually called from BatchPayments right
// after preview, with items derived from non-matched preview rows.
export const saveReviewItems = async (items) => {
  const { data } = await API.post("/payments/reconciliation", { items });
  return data;
};

// status: null | "pending_review" | "applied" | "rejected" | "all"
// Default (null) returns pending_review only.
export const listReviewItems = async (status = null) => {
  const params = status ? { status } : {};
  const { data } = await API.get("/payments/reconciliation", { params });
  return data;
};

export const getReviewItem = async (itemId) => {
  const { data } = await API.get(`/payments/reconciliation/${itemId}`);
  return data;
};

// payload:
// {
//   tenant_id, lease_id, amount, payment_date,   // required
//   reference?, payment_method?, payment_type?,  // optional
//   notes?, notify?                              // optional
// }
export const applyReviewItem = async (itemId, payload) => {
  const { data } = await API.post(
    `/payments/reconciliation/${itemId}/apply`,
    payload,
  );
  return data;
};

export const rejectReviewItem = async (itemId, reason = null) => {
  const { data } = await API.post(
    `/payments/reconciliation/${itemId}/reject`,
    { reason },
  );
  return data;
};

// Hard delete — allowed for pending / rejected only. Applied items 400.
export const deleteReviewItem = async (itemId) => {
  const { data } = await API.delete(`/payments/reconciliation/${itemId}`);
  return data;
};
