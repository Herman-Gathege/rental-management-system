// frontend/src/components/StaffBottomNav.jsx
import { NavLink } from "react-router-dom";
import {
  FiHome,
  FiUser,
  FiLock
} from "react-icons/fi";

export default function StaffBottomNav() {
  const linkClass = ({ isActive }) =>
    `bottom-nav-link bottom-nav-item ${isActive ? "active" : ""}`;

  return (
    <nav className="bottom-nav show-mobile">
      <NavLink to="/staff" end className={linkClass}>
        <FiHome />
        <span>Home</span>
      </NavLink>

      <NavLink to="/staff/profile" className={linkClass}>
        <FiUser />
        <span>Profile</span>
      </NavLink>

      <NavLink to="/staff/password" className={linkClass}>
        <FiLock />
        <span>Password</span>
      </NavLink>
    </nav>
  );
}
