//frontend\src\api\reports.js
import API from "./client";

// Landlord / finance financial reports. Each report has a JSON endpoint (for
// the on-screen table) and a matching /csv endpoint (for download).

const buildParams = ({ propertyId, startDate, endDate, activeOnly } = {}) => {
  const params = {};
  if (propertyId) params.property_id = propertyId;
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  if (activeOnly !== undefined) params.active_only = activeOnly;
  return params;
};

export const getRentRoll = async (opts = {}) => {
  const { data } = await API.get("/reports/rent-roll", { params: buildParams(opts) });
  return data;
};

export const getCollectionReport = async (opts = {}) => {
  const { data } = await API.get("/reports/collection", { params: buildParams(opts) });
  return data;
};

export const getVendorReport = async (opts = {}) => {
  const { data } = await API.get("/reports/vendor", { params: buildParams(opts) });
  return data;
};

export const getProfitByProperty = async (opts = {}) => {
  const { data } = await API.get("/reports/profit-by-property", { params: buildParams(opts) });
  return data;
};

// Trigger a CSV download for a given report path (e.g. "rent-roll").
// Fetches as a blob so the bearer token / axios interceptors still apply,
// then saves it via a temporary object URL.
export const downloadReportCsv = async (reportPath, opts = {}) => {
  const res = await API.get(`/reports/${reportPath}/csv`, {
    params: buildParams(opts),
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([res.data], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = `${reportPath}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};
