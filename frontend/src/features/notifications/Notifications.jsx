//frontend/src/features/notifications/Notifications.jsx
//
// Notifications page — the sidebar "Notifications" menu destination for every
// role. Placeholder until the notifications module exists; mirrors the empty
// state of the dashboard NotificationsCard. Role-agnostic (reads nothing
// role-specific yet), mounted under each role prefix in AppRoutes.

export default function Notifications() {
  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">Notifications</div>
      <div className="dash-panel">
        <div className="text-muted">
          You're all caught up — no new notifications.
        </div>
      </div>
    </div>
  );
}
