//frontend\src\api\ticketMetrics.js
import API from "./client";

// Role-scoped dashboard ticket metrics.
export const getTicketMetrics = async () => {
  const { data } = await API.get("/tickets/metrics/summary");
  return data;
};
