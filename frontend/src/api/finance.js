//frontend\src\api\finance.js
import API from "./client";

export const getTenantBalance = async (tenantId) => {
  const { data } = await API.get(`/finance/tenant-balance/${tenantId}`);
  return data;
};

export const getDashboardSummary = async () => {
  const { data } = await API.get("/finance/dashboard-summary");
  return data;
};
