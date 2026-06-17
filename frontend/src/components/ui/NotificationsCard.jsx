//frontend/src/components/ui/NotificationsCard.jsx
//
// Notifications placeholder card, shown on every role's dashboard.
// The notifications module isn't built yet, so this renders an honest empty
// state. When there's a feed/endpoint, pass `items` (or fetch inside here) and
// the map below takes over — every dashboard updates from this one place.

const fmtDate = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "";

export default function NotificationsCard({ items = [] }) {
  return (
    <div className="dash-panel mb-md">
      <div className="dash-panel-title">Notifications</div>
      {items.length === 0 ? (
        <div className="text-muted">
          You're all caught up — no new notifications.
        </div>
      ) : (
        items.map((n, i) => (
          <div className="dash-row" key={n.id || i}>
            <div>
              <div className="text-bold">{n.title}</div>
              <div className="text-muted">{n.body}</div>
            </div>
            <span className="text-muted">{fmtDate(n.created_at)}</span>
          </div>
        ))
      )}
    </div>
  );
}
