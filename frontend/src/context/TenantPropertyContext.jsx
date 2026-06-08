// frontend/src/context/TenantPropertyContext.jsx
//
// Tenant-scoped property switcher state (Sprint 4.5).
//
// Unlike PropertyContext -- which fetches the whole ORGANISATION's properties
// via the landlord endpoint -- this derives the tenant's properties from THEIR
// OWN leases (/dashboard/tenant/me). It's only mounted under the /tenant/*
// routes, so it never runs for other roles.
//
// It also caches the /tenant/me payload (`dashboard`) so the tenant pages can
// reuse it instead of each refetching. `activeProperty === null` means "All".

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getTenantDashboard } from "../api/dashboard";

const TenantPropertyContext = createContext(null);
export const useTenantProperty = () => useContext(TenantPropertyContext);

const STORAGE_KEY = "tenant_active_property_id";

export function TenantPropertyProvider({ children }) {
  const [dashboard, setDashboard] = useState(null);
  const [activePropertyId, setActivePropertyId] = useState(null); // null = All
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setLoading(true);
        const d = await getTenantDashboard();
        if (!active) return;
        setDashboard(d);

        // Restore the saved selection only if it still matches one of the
        // tenant's current properties; otherwise fall back to All.
        const saved = localStorage.getItem(STORAGE_KEY);
        const ids = new Set(
          (d?.leases || []).map((l) => l.property_id).filter(Boolean)
        );
        setActivePropertyId(saved && saved !== "ALL" && ids.has(saved) ? saved : null);
      } catch (err) {
        if (!active) return;
        setError(err?.response?.data?.detail || "Could not load your portal.");
      } finally {
        if (active) setLoading(false);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, []);

  // Distinct properties drawn from the tenant's leases.
  const properties = useMemo(() => {
    const map = new Map();
    for (const l of dashboard?.leases || []) {
      if (l.property_id && !map.has(l.property_id)) {
        map.set(l.property_id, { id: l.property_id, name: l.property_name });
      }
    }
    return Array.from(map.values());
  }, [dashboard]);

  const activeProperty = useMemo(
    () => properties.find((p) => p.id === activePropertyId) || null,
    [properties, activePropertyId]
  );

  const switchProperty = (propOrNull) => {
    const id = propOrNull ? propOrNull.id : null;
    setActivePropertyId(id);
    localStorage.setItem(STORAGE_KEY, id || "ALL");
  };

  return (
    <TenantPropertyContext.Provider
      value={{
        dashboard,
        properties,
        activeProperty,
        activePropertyId,
        switchProperty,
        loading,
        error,
      }}
    >
      {children}
    </TenantPropertyContext.Provider>
  );
}
