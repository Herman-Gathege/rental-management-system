// frontend/src/components/BottomNav.jsx
//
// Mobile bottom navigation — config-driven, role-aware (responsiveness pass).
// Reads the current user's role and renders its quick links from navigation.js,
// the same single source of truth the sidebar uses. Replaces the old hardcoded
// BottomNav + StaffBottomNav (the latter pointed at dead /staff/* routes).
//
// Visibility is handled by the `.bottom-nav` rule in layout.css (shown below
// 768px, hidden above), so this renders for every role and the CSS hides it on
// desktop.

import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  ownerBottomNav,
  staffBottomNav,
  financeBottomNav,
  tenantBottomNav,
  superAdminBottomNav,
} from "../config/navigation";

const BOTTOM_NAV_BY_ROLE = {
  landlord: ownerBottomNav,
  property_manager: staffBottomNav,
  finance: financeBottomNav,
  tenant: tenantBottomNav,
  system: superAdminBottomNav,
};

export default function BottomNav() {
  const { user } = useAuth();
  if (!user) return null;

  const role = user.role?.toLowerCase();
  // Unknown role falls back to the most-restricted menu.
  const items = BOTTOM_NAV_BY_ROLE[role] || tenantBottomNav;

  const linkClass = ({ isActive }) =>
    `bottom-nav-item ${isActive ? "active" : ""}`;

  return (
    <nav className="bottom-nav">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.path}
            to={item.path}
            end={!!item.end}
            className={linkClass}
          >
            {Icon && <Icon />}
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
