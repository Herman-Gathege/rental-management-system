import { NavLink } from "react-router-dom";
import {
  FiHome,
  FiBriefcase,
  FiLayers,
  FiUsers,
  FiDollarSign,
} from "react-icons/fi";

export default function BottomNav() {
  return (
    <nav className="bottom-nav hidden-desktop">
      <NavLink to="/owner/dashboard" end className="bottom-nav-item">
        <FiHome />
        <span>Home</span>
      </NavLink>

      <NavLink to="/owner/properties" className="bottom-nav-item">
        <FiBriefcase />
        <span>Properties</span>
      </NavLink>

      <NavLink to="/owner/units" className="bottom-nav-item">
        <FiLayers />
        <span>Units</span>
      </NavLink>

      <NavLink to="/owner/tenants" className="bottom-nav-item">
        <FiUsers />
        <span>Tenants</span>
      </NavLink>

      <NavLink to="/owner/payments" className="bottom-nav-item">
        <FiDollarSign />
        <span>Rent</span>
      </NavLink>
    </nav>
  );
}