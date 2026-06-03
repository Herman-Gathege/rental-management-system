/*frontend\src\features\dashboard\layout\Sidebar.jsx*/

import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../../../context/AuthContext";
import { useEffect, useState } from "react";
import {
  FiChevronDown,
  FiHome,
  FiUsers,
  FiFileText,
  FiSettings,
  FiBriefcase,
  FiDollarSign,
  FiKey,
  FiLayers,
} from "react-icons/fi";

export default function Sidebar() {
  const { user, organization } = useAuth();
  const location = useLocation();

  /* ================= COLLAPSE STATE ================= */
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem("sidebarCollapsed") === "true";
  });

  useEffect(() => {
    localStorage.setItem("sidebarCollapsed", collapsed);
  }, [collapsed]);

  /* ================= ROLE FLAGS ================= */
  const isLandlord = user?.role === "LANDLORD";
  const isManager = user?.role === "PROPERTY_MANAGER";
  const isFinance = user?.role === "FINANCE";
  const isTenant = user?.role === "TENANT";
  const isSystem = user?.role === "SYSTEM";

  if (!user) return null;

  const linkClass = ({ isActive }) =>
    `sidebar-link ${isActive ? "active" : ""}`;

  /* ================= DROPDOWN STATE ================= */
  const [propertyOpen, setPropertyOpen] = useState(false);
  const [unitsOpen, setUnitsOpen] = useState(false);
  const [tenantsOpen, setTenantsOpen] = useState(false);
  const [leasesOpen, setLeasesOpen] = useState(false);
  const [paymentsOpen, setPaymentsOpen] = useState(false);
  const [financeOpen, setFinanceOpen] = useState(false);

  const toggle = (setter) => setter((prev) => !prev);

  return (
    <aside className={`sidebar hidden-mobile ${collapsed ? "sidebar-collapsed" : ""}`}>
      
      {/* ================= HEADER ================= */}
      <div className="sidebar-header">
        {!collapsed && (
          <h2 className="sidebar-logo text-lg font-bold company-blue">
            {organization?.name || "Rental Manager"}
          </h2>
        )}

        <button
          className="sidebar-collapse-btn mr-sm"
          onClick={() => setCollapsed(!collapsed)}
        >
          <FiChevronDown className={collapsed ? "rotated" : ""} />
        </button>
      </div>

      <nav className="sidebar-nav flex flex-col gap-sm p-sm">

        {/* ================= LANDLORD ================= */}
        {isLandlord && (
          <>
            <NavLink to="/owner/dashboard" className={linkClass}>
              <FiHome /> {!collapsed && <span>Dashboard</span>}
            </NavLink>

            {/* PROPERTIES */}
            <button className="sidebar-link" onClick={() => toggle(setPropertyOpen)}>
              <FiBriefcase /> {!collapsed && <span>Properties</span>}
              {!collapsed && <FiChevronDown className={`chevron ${propertyOpen ? "rotated" : ""}`} />}
            </button>
            {propertyOpen && !collapsed && (
              <div className="sidebar-submenu">
                <NavLink to="/owner/properties" className={linkClass}>All Properties</NavLink>
                <NavLink to="/owner/properties/new" className={linkClass}>Add Property</NavLink>
              </div>
            )}

            {/* UNITS */}
            <button className="sidebar-link" onClick={() => toggle(setUnitsOpen)}>
              <FiLayers /> {!collapsed && <span>Units</span>}
              {!collapsed && <FiChevronDown className={`chevron ${unitsOpen ? "rotated" : ""}`} />}
            </button>
            {unitsOpen && !collapsed && (
              <div className="sidebar-submenu">
                <NavLink to="/owner/units" className={linkClass}>All Units</NavLink>
                <NavLink to="/owner/units/vacant" className={linkClass}>Vacant Units</NavLink>
                <NavLink to="/owner/units/add" className={linkClass}>Add Unit</NavLink>
              </div>
            )}

            {/* TENANTS */}
            <button className="sidebar-link" onClick={() => toggle(setTenantsOpen)}>
              <FiUsers /> {!collapsed && <span>Tenants</span>}
              {!collapsed && <FiChevronDown className={`chevron ${tenantsOpen ? "rotated" : ""}`} />}
            </button>
            {tenantsOpen && !collapsed && (
              <div className="sidebar-submenu">
                <NavLink to="/owner/tenants" className={linkClass}>All Tenants</NavLink>
                <NavLink to="/owner/tenants/add" className={linkClass}>Add Tenant</NavLink>
                <NavLink to="/owner/tenants/notices" className={linkClass}>Notices & Evictions</NavLink>
              </div>
            )}

            {/* LEASES */}
            <button className="sidebar-link" onClick={() => toggle(setLeasesOpen)}>
              <FiFileText /> {!collapsed && <span>Leases</span>}
              {!collapsed && <FiChevronDown className={`chevron ${leasesOpen ? "rotated" : ""}`} />}
            </button>
            {leasesOpen && !collapsed && (
              <div className="sidebar-submenu">
                <NavLink to="/owner/leases" className={linkClass}>Active Leases</NavLink>
                <NavLink to="/owner/leases/create" className={linkClass}>Create Lease</NavLink>
                <NavLink to="/owner/leases/expired" className={linkClass}>Expired Leases</NavLink>
              </div>
            )}

            {/* PAYMENTS */}
            <button className="sidebar-link" onClick={() => toggle(setPaymentsOpen)}>
              <FiDollarSign /> {!collapsed && <span>Rent & Payments</span>}
              {!collapsed && <FiChevronDown className={`chevron ${paymentsOpen ? "rotated" : ""}`} />}
            </button>
            {paymentsOpen && !collapsed && (
              <div className="sidebar-submenu">
                <NavLink to="/owner/billing" className={linkClass}>Rent Dashboard</NavLink>
                <NavLink to="/owner/payments/history" className={linkClass}>Payment History</NavLink>
                <NavLink to="/owner/payments/late" className={linkClass}>Late Payments</NavLink>
              </div>
            )}

            {/* TEAM — Sprint 2 */}
            <NavLink to="/owner/team" className={linkClass}>
              <FiKey /> {!collapsed && <span>Team</span>}
            </NavLink>

            <NavLink to="/owner/settings" className={linkClass}>
              <FiSettings /> {!collapsed && <span>Settings</span>}
            </NavLink>
          </>
        )}

        {/* ================= PROPERTY MANAGER ================= */}
        {(isManager || isFinance) && (
          <>
            <NavLink to="/manager/dashboard" className={linkClass}>
              <FiHome /> {!collapsed && <span>Dashboard</span>}
            </NavLink>

            <NavLink to="/manager/properties" className={linkClass}>
              <FiBriefcase /> {!collapsed && <span>Properties</span>}
            </NavLink>

            <NavLink to="/manager/tenants" className={linkClass}>
              <FiUsers /> {!collapsed && <span>Tenants</span>}
            </NavLink>

            <NavLink to="/manager/payments" className={linkClass}>
              <FiDollarSign /> {!collapsed && <span>Payments</span>}
            </NavLink>

            <NavLink to="/manager/leases" className={linkClass}>
              <FiFileText /> {!collapsed && <span>Leases</span>}
            </NavLink>
          </>
        )}

        {/* ================= TENANT ================= */}
        {isTenant && (
          <>
            <NavLink to="/tenant" className={linkClass}>
              <FiHome /> {!collapsed && <span>My Home</span>}
            </NavLink>

            <NavLink to="/tenant/payments" className={linkClass}>
              <FiDollarSign /> {!collapsed && <span>My Payments</span>}
            </NavLink>

            <NavLink to="/tenant/lease" className={linkClass}>
              <FiFileText /> {!collapsed && <span>My Lease</span>}
            </NavLink>
            
          </>
        )}

        {/* ================= SYSTEM ADMIN ================= */}
        {isSystem && (
          <>
            <NavLink to="/super-admin/dashboard" className={linkClass}>
              <FiHome /> {!collapsed && <span>System Dashboard</span>}
            </NavLink>

            <NavLink to="/super-admin/organizations" className={linkClass}>
              <FiUsers /> {!collapsed && <span>Organizations</span>}
            </NavLink>
          </>
        )}

      </nav>
    </aside>
  );
}
