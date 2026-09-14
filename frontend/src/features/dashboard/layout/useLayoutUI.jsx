// frontend/src/features/dashboard/layout/useLayoutUI.jsx
//
// Reads the app-shell layout state. Kept in its own file so
// LayoutUIContext.jsx exports only components (react-refresh rule).

import { useContext } from "react";
import { LayoutUIContext } from "./layoutUIContext";

export function useLayoutUI() {
  return (
    useContext(LayoutUIContext) || {
      collapsed: false,
      toggleCollapsed: () => {},
      mobileOpen: false,
      openMobile: () => {},
      closeMobile: () => {},
    }
  );
}

export default useLayoutUI;
