// frontend/src/features/dashboard/layout/Sidebar.jsx
//
// Config-driven sidebar. Picks the menu array for the current user's role from
// navigation.js and renders it — no role-specific JSX, so changing a role's menu
// means editing navigation.js only.
//
// Shell pass (requirement 12):
//   * items are grouped under their functional-area headings
//   * the desktop sidebar collapses to an icon rail (persisted), with
//     accessible tooltips for the icon-only links
//   * the same markup doubles as the mobile drawer, with a backdrop, Escape to
//     close, and automatic closing after navigation
//   * groups auto-expand when the current route lives inside them, so the
//     active page is never hidden behind a collapsed group

import { NavLink, useLocation } from "react-router-dom";
import { useMemo, useState } from "react";
import { FiChevronDown, FiMenu, FiX } from "react-icons/fi";
import { useAuth } from "../../../context/AuthContext";
import {
  ownerNavigation,
  staffNavigation,
  financeNavigation,
  tenantNavigation,
  superAdminNavigation,
} from "../../../config/navigation";
import { useLayoutUI } from "./useLayoutUI";

const NAV_BY_ROLE = {
  LANDLORD: ownerNavigation,
  PROPERTY_MANAGER: staffNavigation,
  FINANCE: financeNavigation,
  TENANT: tenantNavigation,
  SYSTEM: superAdminNavigation,
};

/* Groups the flat menu array into [{ section, items }] in declaration order. */
function groupBySection(navigation) {
  const groups = [];
  for (const item of navigation) {
    const section = item.section || "General";
    const existing = groups.find((g) => g.section === section);
    if (existing) existing.items.push(item);
    else groups.push({ section, items: [item] });
  }
  return groups;
}

export default function Sidebar() {
  const { user, organization } = useAuth();
  const { collapsed, toggleCollapsed, mobileOpen, closeMobile } = useLayoutUI();
  const location = useLocation();

  const navigation = NAV_BY_ROLE[user?.role] || tenantNavigation;
  const sections = useMemo(() => groupBySection(navigation), [navigation]);

  /* Which collapsible groups are open.
     `autoOpen` is derived from the current route — a page reached by direct
     link always shows its parent group open — and `menuOverrides` records the
     user's explicit toggles on top of it. Deriving instead of storing means no
     effect has to keep the two in sync. */
  const autoOpen = useMemo(() => {
    const state = {};
    for (const item of navigation) {
      if (
        item.children?.some((child) =>
          location.pathname.startsWith(child.path),
        )
      ) {
        state[item.label] = true;
      }
    }
    return state;
  }, [location.pathname, navigation]);

  const [menuOverrides, setMenuOverrides] = useState({});
  const isMenuOpen = (label) => menuOverrides[label] ?? !!autoOpen[label];
  const toggleMenu = (label) =>
    setMenuOverrides((prev) => ({ ...prev, [label]: !isMenuOpen(label) }));

  if (!user) return null;

  const linkClass = ({ isActive }) =>
    `sidebar-link ${isActive ? "active" : ""}`;

  /* Nav links close the mobile drawer once the user has chosen a destination. */
  const onNavigate = () => {
    if (mobileOpen) closeMobile();
  };

  const body = (
    <>
      <div className="sidebar-header">
        {!collapsed && (
          <h2 className="sidebar-logo text-lg font-bold company-blue">
            {organization?.name || "Rental Manager"}
          </h2>
        )}
        <button
          type="button"
          className="sidebar-collapse-btn mr-sm"
          onClick={toggleCollapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!collapsed}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <FiChevronDown className={collapsed ? "rotated" : ""} />
        </button>
        <button
          type="button"
          className="sidebar-close-btn"
          onClick={closeMobile}
          aria-label="Close navigation"
        >
          <FiX />
        </button>
      </div>

      <nav className="sidebar-nav flex flex-col gap-sm p-sm" aria-label="Main navigation">
        {sections.map(({ section, items }) => (
          <div className="sidebar-section" key={section}>
            {!collapsed && <div className="sidebar-section-label">{section}</div>}

            {items.map((item) => {
              const Icon = item.icon;

              if (item.children) {
                const open = isMenuOpen(item.label);
                return (
                  <div key={item.label}>
                    <button
                      type="button"
                      className="sidebar-link"
                      onClick={() => toggleMenu(item.label)}
                      aria-expanded={open}
                      title={collapsed ? item.label : undefined}
                    >
                      {Icon && <Icon aria-hidden="true" />}
                      {!collapsed && <span>{item.label}</span>}
                      {!collapsed && (
                        <FiChevronDown
                          className={`chevron ${open ? "rotated" : ""}`}
                          aria-hidden="true"
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
                            onClick={onNavigate}
                          >
                            {child.label}
                          </NavLink>
                        ))}
                      </div>
                    )}
                  </div>
                );
              }

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={linkClass}
                  end
                  onClick={onNavigate}
                  title={collapsed ? item.label : undefined}
                >
                  {Icon && <Icon aria-hidden="true" />}
                  {!collapsed && <span>{item.label}</span>}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`sidebar hidden-mobile ${collapsed ? "sidebar-collapsed" : ""}`}
      >
        {body}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <>
          <div
            className="sidebar-backdrop"
            onClick={closeMobile}
            aria-hidden="true"
          />
          <aside
            className="sidebar sidebar-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Navigation"
          >
            {body}
          </aside>
        </>
      )}
    </>
  );
}
