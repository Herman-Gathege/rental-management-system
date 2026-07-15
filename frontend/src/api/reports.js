import API from "./client";

// -----------------------------------------------------------
// Reports API
// -----------------------------------------------------------

const buildParams = ({
  propertyId,
  startDate,
  endDate,
  activeOnly,
  status,
  search,
} = {}) => {
  const params = {};

  if (propertyId) params.property_id = propertyId;
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  if (activeOnly !== undefined) params.active_only = activeOnly;

  // Future filters
  if (status) params.status = status;
  if (search) params.search = search;

  return params;
};

export const getRentRoll = async (opts = {}) => {
  const { data } = await API.get("/reports/rent-roll", {
    params: buildParams(opts),
  });

  return data;
};

export const getCollectionReport = async (opts = {}) => {
  const { data } = await API.get("/reports/collection", {
    params: buildParams(opts),
  });

  return data;
};

export const getVendorReport = async (opts = {}) => {
  const { data } = await API.get("/reports/vendor", {
    params: buildParams(opts),
  });

  return data;
};

export const getProfitByProperty = async (opts = {}) => {
  const { data } = await API.get("/reports/profit-by-property", {
    params: buildParams(opts),
  });

  return data;
};

export const downloadReportCsv = async (reportPath, opts = {}) => {
  const res = await API.get(`/reports/${reportPath}/csv`, {
    params: buildParams(opts),
    responseType: "blob",
  });

  const blob = new Blob([res.data], {
    type: "text/csv;charset=utf-8;",
  });

  const url = window.URL.createObjectURL(blob);

  const link = document.createElement("a");

  const today = new Date().toISOString().slice(0, 10);

  link.href = url;
  link.download = `${reportPath}-${today}.csv`;

  document.body.appendChild(link);

  link.click();

  link.remove();

  window.URL.revokeObjectURL(url);
};