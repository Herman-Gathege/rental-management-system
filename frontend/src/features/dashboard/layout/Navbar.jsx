// frontend/src/features/dashboard/layout/Navbar.jsx
import { useState, useEffect, useMemo } from "react";
import { useAuth } from "../../../context/AuthContext";
import { FiMaximize, FiMinimize, FiChevronDown } from "react-icons/fi";
import { NavLink } from "react-router-dom";
import PropertySwitcher from "../../../components/PropertySwitcher/PropertySwitcher";
import {
  ownerNavigation,
  staffNavigation,
  superAdminNavigation,
} from "../../../config/navigation";

export default function Navbar() {
  const { user, logout } = useAuth();

  const [open, setOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isFullscreen, setIsFullscreen] = useState(
    !!document.fullscreenElement,
  );

  // ----------------------------
  // TIME HANDLING
  // ----------------------------
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // ----------------------------
  // FULLSCREEN HANDLING
  // ----------------------------
  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);

    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  if (!user) return <header className="navbar" />;

  // ----------------------------
  // NORMALIZE ROLE (IMPORTANT FIX)
  // ----------------------------
  const role = user.role?.toLowerCase();

  const navigation = useMemo(() => {
    switch (role) {
      case "landlord":
        return ownerNavigation;
      case "system":
        return superAdminNavigation;
      default:
        return staffNavigation;
    }
  }, [role]);

  // ----------------------------
  // SAFE USER DISPLAY HELPERS
  // ----------------------------
  const displayName = user.full_name || user.email || "User";

  const avatarLetter = (user.full_name || user.email || "U")
    .charAt(0)
    .toUpperCase();

  // ----------------------------
  // FORMATTED TIME
  // ----------------------------
  const formattedTime = currentTime.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const formattedDate = currentTime.toLocaleDateString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  // ----------------------------
  // FULLSCREEN TOGGLE
  // ----------------------------
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(console.error);
    } else {
      document.exitFullscreen();
    }
  };

  return (
    <header className="navbar flex justify-between items-center p-md">
      {/* LEFT */}
      <div className="flex items-center gap-md">
        <button
          type="button"
          onClick={toggleFullscreen}
          className="btn"
          title="Toggle Fullscreen"
        >
          {isFullscreen ? <FiMinimize size={20} /> : <FiMaximize size={20} />}
        </button>

        {/* Property Switcher — Sprint 2 */}
        {(role === "landlord" || role === "property_manager") && (
          <PropertySwitcher />
        )}
      </div>

      {/* CENTER */}
      <div className="flex flex-col items-center text-sm hidden-mobile gap-md">
        <span className="text-muted mr-sm">{formattedDate}</span>
        <span className="text-bold">{formattedTime}</span>
      </div>

      {/* RIGHT */}
      <div className="relative flex items-center gap-xs">
        {/* Avatar */}
        <div
          className="avatar cursor-pointer"
          onClick={() => setOpen((o) => !o)}
        >
          {avatarLetter}
        </div>

        {/* Chevron */}
        <FiChevronDown
          onClick={() => setOpen((o) => !o)}
          className={`chevron cursor-pointer transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        />

        {/* DROPDOWN */}
        {open && (
          <div className="dropdown dropdown-lg">
            {/* USER HEADER */}
            <div className="dropdown-header">
              <div className="avatar avatar-sm">{avatarLetter}</div>

              <div className="dropdown-user-info">
                <div className="dropdown-name">{displayName}</div>
                <div className="dropdown-role">{user.role}</div>
              </div>
            </div>

            <div className="dropdown-divider" />

            {/* NAVIGATION */}
            {navigation.map((item) =>
              item.children ? (
                item.children.map((child) => (
                  <NavLink
                    key={child.path}
                    to={child.path}
                    className="dropdown-item"
                    onClick={() => setOpen(false)}
                  >
                    {child.label}
                  </NavLink>
                ))
              ) : (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className="dropdown-item"
                  onClick={() => setOpen(false)}
                >
                  {item.label}
                </NavLink>
              ),
            )}

            <div className="dropdown-divider" />

            {/* LOGOUT */}
            <button className="btn btn-secondary mr-sm ml-sm" onClick={logout}>
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}