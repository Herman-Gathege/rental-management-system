//frontend/src/components/BottomNav.jsx
import { NavLink } from "react-router-dom";
import {
  FiBarChart2,
  FiBox,
  FiUsers,
  FiMenu,
  FiHome
} from "react-icons/fi";
import { useState } from "react";

export default function BottomNav() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <nav className="bottom-nav hidden-desktop">

        <NavLink to="/owner/dashboard" end className="bottom-nav-item">
         <FiHome />
         <span>Home</span>
       </NavLink>

        <NavLink to="/owner/sales" className="bottom-nav-item">
          <FiBarChart2 />
          <span>Sales</span>
        </NavLink>

        <NavLink to="/owner/stock" className="bottom-nav-item">
          <FiBox />
          <span>Stock</span>
        </NavLink>

        <NavLink to="/owner/customers/debtors" className="bottom-nav-item">
          <FiUsers />
          <span>Customers</span>
        </NavLink>

        

      </nav>

      
    </>
  );
}
