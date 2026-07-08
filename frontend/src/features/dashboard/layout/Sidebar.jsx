/*frontend/src/features/dashboard/layout/Sidebar.jsx*/
//
// Config-driven sidebar (Sprint 4.5, Chunk 5).
// Picks the menu array for the current user's role from navigation.js and
// renders it. No role-specific JSX blocks and no hardcoded menus — fixing a
// role's menu now means editing navigation.js only. Replaces the old version
// that hardcoded every role's tree (and gave FINANCE the manager menu).

import { NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { FiChevronDown } from "react-icons/fi";
import { useAuth } from "../../../context/AuthContext";
import {
  ownerNavigation,
  staffNavigation,
  financeNavigation,
  tenantNavigation,
  superAdminNavigation,
} from "../../../config/navigation";

const NAV_BY_ROLE = {
  LANDLORD: ownerNavigation,
  PROPERTY_MANAGER: staffNavigation,
  FINANCE: financeNavigation,
  TENANT: tenantNavigation,
  SYSTEM: superAdminNavigation,
};

export default function Sidebar() {
  const { user, organization } = useAuth();

  /* ===== Collapse state (persisted) ===== */
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem("sidebarCollapsed") === "true",
  );
  useEffect(() => {
    localStorage.setItem("sidebarCollapsed", collapsed);
  }, [collapsed]);

  /* ===== Which groups are expanded (keyed by label) ===== */
  const [openMenus, setOpenMenus] = useState({});
  const toggleMenu = (label) =>
    setOpenMenus((prev) => ({ ...prev, [label]: !prev[label] }));

  if (!user) return null;
  console.group("===== Sidebar Debug =====");
  console.log("User:", user);
  console.log("Role:", user.role);

  // Unknown role falls back to the most-restricted menu (tenant) rather than
  // exposing management links.
  const navigation = NAV_BY_ROLE[user.role] || tenantNavigation;

  console.log("Navigation array:", navigation);
  console.log(
    "Navigation labels:",
    navigation.map((item) => item.label),
  );
  console.log("Navigation count:", navigation.length);
  console.groupEnd();

  const linkClass = ({ isActive }) =>
    `sidebar-link ${isActive ? "active" : ""}`;

  return (
    <aside
      className={`sidebar hidden-mobile ${collapsed ? "sidebar-collapsed" : ""}`}
    >
      {/* ===== HEADER ===== */}
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

      {/* ===== NAV ===== */}
      <nav className="sidebar-nav flex flex-col gap-sm p-sm">
        {navigation.map((item, index) => {
  console.log(
    `Rendering menu ${index + 1}/${navigation.length}:`,
    item.label,
    item.path || "(group)"
  );

  const Icon = item.icon;

          // Collapsible group (has children)
          if (item.children) {
            const open = !!openMenus[item.label];
            return (
              <div key={item.label}>
                <button
                  className="sidebar-link"
                  onClick={() => toggleMenu(item.label)}
                >
                  {Icon && <Icon />} {!collapsed && <span>{item.label}</span>}
                  {!collapsed && (
                    <FiChevronDown
                      className={`chevron ${open ? "rotated" : ""}`}
                    />
                  )}
                </button>

                {open && !collapsed && (
                  <div className="sidebar-submenu">
                    {item.children.map((child) => (
                      <NavLink
                        key={child.path}
                        to={child.path}
                        className={linkClass}
                        end
                      >
                        {child.label}
                      </NavLink>
                    ))}
                  </div>
                )}
              </div>
            );
          }

          // Simple link
          return (
            <NavLink key={item.path} to={item.path} className={linkClass} end>
              {Icon && <Icon />} {!collapsed && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
