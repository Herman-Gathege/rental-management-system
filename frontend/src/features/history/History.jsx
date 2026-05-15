//frontend\src\features\history\History.jsx
import { useEffect, useState } from "react";
import { getAuditLogs } from "../../api/audit";

const ENTITY_TYPES = [
  "",
  "property",
  "unit",
  "tenant",
  "lease",
  "charge",
  "payment",
  "property_manager",
];

export default function History() {
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await getAuditLogs(filter || null);
      setLogs(data);
    } catch (err) {
      console.error("Failed to fetch audit logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filter]);

  return (
    <section className="properties-page">
      <h2>Activity History</h2>

      {/* Filter buttons */}
      <div className="flex gap-sm flex-wrap mb-md">
        {ENTITY_TYPES.map((t) => (
          <button
            key={t}
            className={`btn btn-sm ${filter === t ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setFilter(t)}
          >
            {t || "All"}
          </button>
        ))}
      </div>

      {/* Log entries */}
      {loading ? (
        <p>Loading history...</p>
      ) : logs.length === 0 ? (
        <div className="empty-state">
          <p>No activity recorded yet.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-sm">
          {logs.map((log) => (
            <div
              key={log.id}
              className={`card audit-entry action-${log.action}`}
            >
              {/* Header row */}
              <div className="flex justify-between items-center">
                <div>
                  <span className={`audit-action-badge action-${log.action}`}>
                    {log.action}
                  </span>
                  <span className="text-sm text-bold">{log.entity_type}</span>
                </div>
                <span className="text-sm text-muted">
                  {new Date(log.created_at).toLocaleString()}
                </span>
              </div>

              {/* Description */}
              <div className="text-sm audit-entry-description">{log.description}</div>

              {/* User */}
              {log.user_email && (
                <div className="text-sm text-muted">By: {log.user_email}</div>
              )}

              {/* Old / New values */}
              {log.old_values && (
                <div className="audit-entry-values">
                  <strong>Old:</strong> {JSON.stringify(log.old_values)}
                </div>
              )}
              {log.new_values && (
                <div className="audit-entry-values">
                  <strong>New:</strong> {JSON.stringify(log.new_values)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
