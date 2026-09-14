// frontend/src/features/dashboard/layout/SuperAdminLayout.jsx
//
// Shell for the /super-admin/* routes. Mirrors StaffLayout so the platform
// admin gets the same sidebar, account dropdown and global search as every
// other role; previously this component rendered a `children` prop that the
// router never passed, leaving the section blank.

import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import GlobalSearch from "../../../components/GlobalSearch/GlobalSearch";
import { LayoutUIProvider } from "./LayoutUIContext";

export default function SuperAdminLayout() {
  return (
    <LayoutUIProvider>
      <div className="dashboard-layout">
        <Sidebar />
        <div className="dashboard-main">
          <Navbar />
          <main className="dashboard-content">
            <Outlet />
          </main>
        </div>
      </div>
      <GlobalSearch />
    </LayoutUIProvider>
  );
}
