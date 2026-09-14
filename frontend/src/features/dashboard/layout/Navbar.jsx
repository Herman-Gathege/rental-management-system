// frontend/src/features/dashboard/layout/Navbar.jsx
//
// Top bar of the app shell.
//
// Shell pass (requirement 12):
//   * mobile menu button that drives the sidebar drawer
//   * a visible global-search trigger (Ctrl+K still works from anywhere)
//   * a proper account dropdown: identity, role/organisation, Profile,
//     Settings (landlord only), Notifications with an unread badge, and a
//     Logout with a pending state and error feedback
//   * the dropdown closes on outside click, Escape, and navigation, and moves
//     focus predictably for keyboard users
//
// The old version dumped the entire navigation tree into the dropdown; that
// duplicated the sidebar and made the menu unusable on mobile.

import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  FiBell,
  FiChevronDown,
  FiLogOut,
  FiMaximize,
  FiMinimize,
  FiMenu,
  FiSearch,
  FiSettings,
  FiUser,
} from "react-icons/fi";
import { useAuth } from "../../../context/AuthContext";
import { useProperty } from "../../../context/PropertyContext";
import PropertySwitcher from "../../../components/PropertySwitcher/PropertySwitcher";
import TenantPropertySwitcher from "../../../components/PropertySwitcher/TenantPropertySwitcher";
import { getNotifications } from "../../../api/notifications";
import {
  notificationsPathFor,
  profilePathFor,
  settingsPathFor,
} from "../../../config/navigation";
import { useLayoutUI } from "./useLayoutUI";

const ROLE_LABELS = {
  LANDLORD: "Landlord",
  PROPERTY_MANAGER: "Property manager",
  FINANCE: "Finance",
  TENANT: "Tenant",
  SYSTEM: "Platform admin",
};

export default function Navbar() {
  const { user, organization, logout } = useAuth();
  const { properties } = useProperty();
  const { openMobile } = useLayoutUI();
  const navigate = useNavigate();
  const location = useLocation();

  const [open, setOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  const [unread, setUnread] = useState(0);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isFullscreen, setIsFullscreen] = useState(!!document.fullscreenElement);

  const menuRef = useRef(null);
  const triggerRef = useRef(null);

  const role = user?.role;

  /* ── Clock ── */
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  /* ── Fullscreen tracking ── */
  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  /* ── Unread notification badge ──
     Best-effort: a failure here must never break the shell, so errors are
     swallowed and the badge simply stays hidden. Refreshed whenever the route
     changes (marking something read on another page updates the badge). */
  useEffect(() => {
    if (!user) return undefined;
    let cancelled = false;
    getNotifications(true)
      .then((items) => {
        if (!cancelled) setUnread(Array.isArray(items) ? items.length : 0);
      })
      .catch(() => {
        if (!cancelled) setUnread(0);
      });
    return () => {
      cancelled = true;
    };
  }, [user, location.pathname]);

  /* ── Close the dropdown on outside click / Escape, and on navigation ── */
  useEffect(() => {
    if (!open) return undefined;

    const onPointerDown = (event) => {
      if (
        menuRef.current?.contains(event.target) ||
        triggerRef.current?.contains(event.target)
      ) {
        return;
      }
      setOpen(false);
    };

    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  const openSearch = () => {
    window.dispatchEvent(new CustomEvent("alphaone:open-global-search"));
  };

  const handleLogout = async () => {
    setLogoutError("");
    setLoggingOut(true);
    try {
      await Promise.resolve(logout());
      navigate("/login", { replace: true });
    } catch (err) {
      setLogoutError(err?.message || "Could not sign out. Please try again.");
    } finally {
      setLoggingOut(false);
    }
  };

  if (!user) return <header className="navbar" />;

  const showOrgSwitcher =
    role === "LANDLORD" ||
    role === "PROPERTY_MANAGER" ||
    (role === "FINANCE" && (properties?.length || 0) > 0);

  const displayName = user.full_name || user.email || "User";
  const avatarLetter = displayName.charAt(0).toUpperCase();
  const settingsPath = settingsPathFor(role);
  const notificationsPath = notificationsPathFor(role);

  const formattedTime = currentTime.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  const formattedDate = currentTime.toLocaleDateString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
  });

  return (
    <header className="navbar flex justify-between items-center p-md">
      {/* LEFT */}
      <div className="flex items-center gap-sm">
        <button
          type="button"
          className="btn-ghost navbar-menu-btn"
          onClick={openMobile}
          aria-label="Open navigation"
        >
          <FiMenu />
        </button>

        <button
          type="button"
          onClick={toggleFullscreen}
          className="btn-ghost hidden-mobile"
          title="Toggle fullscreen"
          aria-label="Toggle fullscreen"
        >
          {isFullscreen ? <FiMinimize size={18} /> : <FiMaximize size={18} />}
        </button>

        {showOrgSwitcher && <PropertySwitcher />}
        {role === "TENANT" && <TenantPropertySwitcher />}
      </div>

      {/* CENTER */}
      <div className="navbar-center hidden-mobile">
        <button
          type="button"
          className="navbar-search-trigger"
          onClick={openSearch}
          aria-label="Search the system (Ctrl+K)"
        >
          <FiSearch aria-hidden="true" />
          <span className="navbar-search-label">Search…</span>
          <span className="navbar-search-kbd">Ctrl K</span>
        </button>
      </div>

      {/* RIGHT */}
      <div className="relative flex items-center gap-xs">
        <button
          type="button"
          className="btn-ghost navbar-search-btn-mobile"
          onClick={openSearch}
          aria-label="Search"
        >
          <FiSearch />
        </button>

        <Link
          to={notificationsPath}
          className="btn-ghost navbar-bell"
          aria-label={
            unread > 0 ? `Notifications, ${unread} unread` : "Notifications"
          }
        >
          <FiBell />
          {unread > 0 && <span className="navbar-badge">{unread > 9 ? "9+" : unread}</span>}
        </Link>

        <span className="navbar-clock text-muted text-sm hidden-mobile">
          {formattedDate} · {formattedTime}
        </span>

        <button
          type="button"
          ref={triggerRef}
          className="navbar-account-trigger"
          onClick={() => setOpen((o) => !o)}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-label="Account menu"
        >
          <span className="avatar avatar-sm" aria-hidden="true">
            {avatarLetter}
          </span>
          <FiChevronDown
            className={`chevron navbar-chevron ${open ? "rotate-180" : ""}`}
            aria-hidden="true"
          />
        </button>

        {open && (
          <div className="dropdown dropdown-lg" role="menu" ref={menuRef}>
            <div className="dropdown-header">
              <div className="avatar avatar-sm" aria-hidden="true">
                {avatarLetter}
              </div>
              <div className="dropdown-user-info">
                <div className="dropdown-name">{displayName}</div>
                <div className="dropdown-email">{user.email}</div>
              </div>
            </div>

            <div className="dropdown-meta">
              <span className="dropdown-chip">{ROLE_LABELS[role] || role}</span>
              {organization?.name && (
                <span className="dropdown-chip dropdown-chip-muted">
                  {organization.name}
                </span>
              )}
            </div>

            <div className="dropdown-divider" />

            <Link
              to={profilePathFor(role)}
              className="dropdown-item dropdown-item-row"
              role="menuitem"
              onClick={() => setOpen(false)}
            >
              <FiUser aria-hidden="true" />
              <span>Profile</span>
            </Link>

            {settingsPath && (
              <Link
                to={settingsPath}
                className="dropdown-item dropdown-item-row"
                role="menuitem"
                onClick={() => setOpen(false)}
              >
                <FiSettings aria-hidden="true" />
                <span>Settings</span>
              </Link>
            )}

            <Link
              to={notificationsPath}
              className="dropdown-item dropdown-item-row"
              role="menuitem"
              onClick={() => setOpen(false)}
            >
              <FiBell aria-hidden="true" />
              <span>Notifications</span>
              {unread > 0 && <span className="dropdown-count">{unread}</span>}
            </Link>

            <div className="dropdown-divider" />

            {logoutError && <p className="dropdown-error text-sm">{logoutError}</p>}

            <button
              type="button"
              className="dropdown-item dropdown-item-row dropdown-danger"
              role="menuitem"
              onClick={handleLogout}
              disabled={loggingOut}
            >
              <FiLogOut aria-hidden="true" />
              <span>{loggingOut ? "Signing out…" : "Log out"}</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
