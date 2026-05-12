import { useEffect, useState } from "react";
import { getAuditLogs } from "../../api/audit";

const ENTITY_TYPES = ["", "property", "unit", "tenant", "lease", "charge", "payment", "property_manager"];

const ACTION_COLORS = {
  create: "#16a34a",
  update: "#2563eb",
  delete: "#ef4444",
  terminate: "#d97706",
  payment: "#8b5cf6",
  billing: "#0891b2",
};

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
      console.error(err);
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

      <div className="flex gap-sm flex-wrap">
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

      {loading ? (
        <p>Loading history...</p>
      ) : logs.length === 0 ? (
        <div className="empty-state">
          <p>No activity recorded yet.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-sm">
          {logs.map((log) => (
            <div key={log.id} className="card" style={{ padding: "12px 16px", borderLeft: `4px solid ${ACTION_COLORS[log.action] || "#6b7280"}` }}>
              <div className="flex justify-between items-center">
                <div>
                  <span
                    className="role-badge"
                    style={{ background: ACTION_COLORS[log.action] || "#e5e7eb", color: "white", marginRight: 8 }}
                  >
                    {log.action}
                  </span>
                  <span className="text-sm text-bold">{log.entity_type}</span>
                </div>
                <span className="text-sm text-muted">
                  {new Date(log.created_at).toLocaleString()}
                </span>
              </div>
              <div className="text-sm mt-sm">{log.description}</div>
              {log.user_email && (
                <div className="text-sm text-muted">By: {log.user_email}</div>
              )}
              {log.old_values && (
                <div className="text-sm text-muted mt-sm">
                  Old: {JSON.stringify(log.old_values)}
                </div>
              )}
              {log.new_values && (
                <div className="text-sm text-muted">
                  New: {JSON.stringify(log.new_values)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
