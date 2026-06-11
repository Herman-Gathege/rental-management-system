// frontend/src/features/dashboard/layout/StaffLayout.jsx
//
// Layout shell for the /manager/* routes.
// Uses <Outlet/> so nested routes (the index StaffDashboard) render, and the
// shared config-driven <BottomNav/> (responsiveness pass) so the PM mobile bar
// shows the right items pointing at real /manager/* routes — replacing the old
// StaffBottomNav, which linked to dead /staff/* paths.

import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import BottomNav from "../../../components/BottomNav";

export default function StaffLayout() {
  return (
    <div className="dashboard-layout">
      <Sidebar />

      <div className="dashboard-main">
        <Navbar />
        <main className="dashboard-content">
          <Outlet />
        </main>

        <BottomNav />
      </div>
    </div>
  );
}
