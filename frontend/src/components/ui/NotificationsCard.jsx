//frontend\src\components\ui\NotificationsCard.jsx
//
// Notifications dashboard card — connected to the real /notifications API.
// Shows the 4 most recent unread notifications; each row marks itself read
// on click. A "Mark all read" link clears the badge in one tap.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from "../../api/notifications";

// Cap on dashboard-preview rows. The full list is still reachable via the
// "View all" link — this just keeps the card compact so it fits alongside
// other widgets without dominating the page.
const PREVIEW_LIMIT = 4;

const fmtDate = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "";

function notificationsPath(role) {
  switch ((role || "").toLowerCase()) {
    case "property_manager": return "/manager/notifications";
    case "finance":          return "/finance/notifications";
    case "tenant":           return "/tenant/notifications";
    default:                 return "/owner/notifications";
  }
}

export default function NotificationsCard() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const data = await getNotifications(true); // unread only
      setItems(data.slice(0, PREVIEW_LIMIT));
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleMarkRead = async (id) => {
    try {
      await markNotificationRead(id);
      setItems((prev) => prev.filter((n) => n.id !== id));
    } catch { /* best-effort */ }
  };

  const handleMarkAll = async () => {
    try {
      await markAllNotificationsRead();
      setItems([]);
    } catch { /* best-effort */ }
  };

  const path = notificationsPath(user?.role);

  return (
    <div className="dash-panel mb-md">
      <div className="flex items-center justify-between mb-sm">
        <div className="dash-panel-title">Notifications</div>
        <div className="flex gap-sm items-center">
          {items.length > 0 && (
            <button
              className="btn btn-secondary btn-sm"
              onClick={handleMarkAll}
            >
              Mark all read
            </button>
          )}
          <Link to={path} className="btn btn-secondary btn-sm">
            View all
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="text-muted text-sm">Loading…</div>
      ) : items.length === 0 ? (
        <div className="text-muted">
          You're all caught up — no new notifications.
        </div>
      ) : (
        items.map((n) => (
          <div
            className="dash-row"
            key={n.id}
            style={{ cursor: "pointer" }}
            onClick={() => handleMarkRead(n.id)}
          >
            <div>
              <div className="text-bold text-sm">{n.title}</div>
              {n.body && (
                <div className="text-muted text-xs">{n.body}</div>
              )}
            </div>
            <span className="text-muted text-xs">{fmtDate(n.created_at)}</span>
          </div>
        ))
      )}
    </div>
  );
}
