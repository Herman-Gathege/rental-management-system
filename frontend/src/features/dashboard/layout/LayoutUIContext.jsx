// frontend/src/features/dashboard/layout/LayoutUIContext.jsx
//
// Shared layout state for the app shell (requirement 12).
//
// The sidebar and navbar are siblings rendered by three different layouts
// (DashboardLayout, StaffLayout, SuperAdminLayout). Putting the mobile-drawer
// and collapse state here means the navbar's menu button and the sidebar's
// drawer stay in sync without duplicating the logic in every layout.

import { useCallback, useEffect, useState } from "react";

import { LayoutUIContext } from "./layoutUIContext";

const COLLAPSE_KEY = "sidebarCollapsed";

export function LayoutUIProvider({ children }) {
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem(COLLAPSE_KEY) === "true",
  );
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem(COLLAPSE_KEY, collapsed);
  }, [collapsed]);

  const toggleCollapsed = useCallback(() => setCollapsed((c) => !c), []);
  const openMobile = useCallback(() => setMobileOpen(true), []);
  const closeMobile = useCallback(() => setMobileOpen(false), []);

  // Close the drawer on Escape, and whenever the viewport grows past the
  // mobile breakpoint (otherwise it would stay "open" invisibly and reappear
  // on the next resize).
  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "Escape") setMobileOpen(false);
    };
    const onResize = () => {
      if (window.innerWidth > 768) setMobileOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  // Prevent the page behind the drawer from scrolling while it's open.
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <LayoutUIContext.Provider
      value={{
        collapsed,
        setCollapsed,
        toggleCollapsed,
        mobileOpen,
        openMobile,
        closeMobile,
      }}
    >
      {children}
    </LayoutUIContext.Provider>
  );
}
