//frontend\src\features\notifications\Notifications.jsx
//
// Notifications page — the sidebar "Notifications" menu destination for every
// role. Shows the last 50 notifications (unread first), with mark-read and
// mark-all-read. The unread count badge in the page title stays live.

import { useEffect, useState } from "react";
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from "../../api/notifications";

const fmtDate = (d) =>
  d
    ? new Date(d).toLocaleString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

// Friendly label for each notification type.
const typeLabel = (type) => {
  const labels = {
    ticket_created:    "New Ticket",
    ticket_assigned:   "Ticket Assigned",
    ticket_in_progress:"Work Started",
    ticket_resolved:   "Issue Resolved",
    ticket_closed:     "Ticket Closed",
    ticket_message:    "New Message",
  };
  return labels[type] || type?.replace(/_/g, " ") || "Notification";
};

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const load = async () => {
    try {
      setLoading(true);
      const data = await getNotifications(false); // all, not just unread
      setNotifications(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load notifications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleMarkRead = async (id) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch { /* best-effort */ }
  };

  const handleMarkAll = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch { /* best-effort */ }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-md">
        <div className="text-lg font-bold">
          Notifications
          {unreadCount > 0 && (
            <span
              style={{
                marginLeft: 8,
                background: "#ef4444",
                color: "#fff",
                borderRadius: 12,
                padding: "2px 8px",
                fontSize: 12,
                fontWeight: 700,
                verticalAlign: "middle",
              }}
            >
              {unreadCount}
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button className="btn btn-secondary btn-sm" onClick={handleMarkAll}>
            Mark all read
          </button>
        )}
      </div>

      {error && <p className="error-text">{error}</p>}

      {loading ? (
        <div className="dash-panel">
          <div className="text-muted">Loading…</div>
        </div>
      ) : notifications.length === 0 ? (
        <div className="dash-panel">
          <div className="text-muted">
            You're all caught up — no new notifications.
          </div>
        </div>
      ) : (
        <div className="card">
          {notifications.map((n) => (
            <div
              key={n.id}
              className="dash-row"
              style={{
                opacity: n.is_read ? 0.55 : 1,
                cursor: n.is_read ? "default" : "pointer",
                borderLeft: n.is_read ? "none" : "3px solid #2563eb",
                paddingLeft: n.is_read ? 0 : 12,
              }}
              onClick={() => !n.is_read && handleMarkRead(n.id)}
            >
              <div className="flex flex-col gap-sm" style={{ flex: 1 }}>
                <div className="flex items-center gap-sm">
                  <span
                    className="text-xs"
                    style={{
                      background: "#eef2f7",
                      borderRadius: 8,
                      padding: "2px 8px",
                      color: "#555",
                    }}
                  >
                    {typeLabel(n.notification_type)}
                  </span>
                  {!n.is_read && (
                    <span
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: "#2563eb",
                        display: "inline-block",
                      }}
                    />
                  )}
                </div>
                <div className="text-bold text-sm">{n.title}</div>
                {n.body && (
                  <div className="text-muted text-xs">{n.body}</div>
                )}
              </div>
              <div className="text-muted text-xs" style={{ whiteSpace: "nowrap" }}>
                {fmtDate(n.created_at)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
