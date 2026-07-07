//frontend\src\api\audit.js
import API from "./client";

// getAuditLogs supports optional pagination. When `offset` is passed, the
// backend returns { items, total, limit, offset }; otherwise a bare array
// (backward compatible). Callers that paginate should read `.items`/`.total`.
export const getAuditLogs = async (
  entityType = null,
  entityId = null,
  limit = 50,
  offset = null
) => {
  const params = { limit };
  if (entityType) params.entity_type = entityType;
  if (entityId) params.entity_id = entityId;
  if (offset != null) params.offset = offset;
  const { data } = await API.get("/audit/", { params });
  return data;
};