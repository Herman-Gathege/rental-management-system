import API from "./client";

export const getAuditLogs = async (entityType = null, entityId = null, limit = 50) => {
  const params = { limit };
  if (entityType) params.entity_type = entityType;
  if (entityId) params.entity_id = entityId;
  const { data } = await API.get("/audit/", { params });
  return data;
};
