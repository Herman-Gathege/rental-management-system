// frontend/src/features/dashboard/layout/StaffLayout.jsx
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import StaffBottomNav from "../../../components/StaffBottomNav";

export default function StaffLayout({ children }) {
  return (
    <div className="dashboard-layout">
      <Sidebar />
      <div className="dashboard-main">
        <Navbar />
        <div className="dashboard-content">
          {children}
        </div>
        <StaffBottomNav />
      </div>
    </div>
  );
}
