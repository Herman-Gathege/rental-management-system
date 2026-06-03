// frontend/src/features/dashboard/layout/StaffLayout.jsx
//
// Layout shell for the /manager/* routes.
// Fixed (Sprint 4.5): was rendering {children}, which meant nested routes
// (the index StaffDashboard) never appeared because react-router renders
// nested routes through <Outlet/>, not children. Now matches DashboardLayout.

import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import StaffBottomNav from "../../../components/StaffBottomNav";

export default function StaffLayout() {
  return (
    <div className="dashboard-layout">
      <Sidebar />

      <div className="dashboard-main">
        <Navbar />
        <main className="dashboard-content">
          <Outlet />
        </main>

        <StaffBottomNav />
      </div>
    </div>
  );
}
