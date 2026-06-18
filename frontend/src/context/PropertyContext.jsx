/*frontend\src\context\PropertyContext.jsx */
//
// Org property switcher state (landlord / property manager / finance).
// activeProperty === null means "All Properties". Default is All; a specific
// property is remembered across reloads (stored as its id; "ALL" = All).

import { createContext, useContext, useEffect, useState } from "react";
import { getProperties } from "../api/properties";
import { useAuth } from "./AuthContext";

const PropertyContext = createContext();
export const useProperty = () => useContext(PropertyContext);

const STORAGE_KEY = "active_property_id";

export function PropertyProvider({ children }) {
  const { user } = useAuth();
  const [properties, setProperties] = useState([]);
  const [activeProperty, setActiveProperty] = useState(null); // null = All
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setProperties([]);
      setActiveProperty(null);
      setLoading(false);
      return;
    }

    const fetchProperties = async () => {
      try {
        setLoading(true);
        const data = await getProperties();
        setProperties(data);

        // Restore a saved specific property only if it still exists; otherwise
        // fall back to All (the default).
        const savedId = localStorage.getItem(STORAGE_KEY);
        if (savedId && savedId !== "ALL") {
          const saved = data.find((p) => p.id === savedId);
          setActiveProperty(saved || null);
        } else {
          setActiveProperty(null);
        }
      } catch (err) {
        console.error("Failed to fetch properties:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProperties();
  }, [user]);

  // Pass a property to scope to it, or null/undefined to select All.
  const switchProperty = (property) => {
    if (property) {
      setActiveProperty(property);
      localStorage.setItem(STORAGE_KEY, property.id);
    } else {
      setActiveProperty(null);
      localStorage.setItem(STORAGE_KEY, "ALL");
    }
  };

  const refreshProperties = async () => {
    try {
      const data = await getProperties();
      setProperties(data);
      // If the currently-selected property disappeared, fall back to All.
      if (activeProperty && !data.find((p) => p.id === activeProperty.id)) {
        setActiveProperty(null);
        localStorage.setItem(STORAGE_KEY, "ALL");
      }
    } catch (err) {
      console.error("Failed to refresh properties:", err);
    }
  };

  return (
    <PropertyContext.Provider
      value={{
        properties,
        activeProperty,
        switchProperty,
        refreshProperties,
        loading,
      }}
    >
      {children}
    </PropertyContext.Provider>
  );
}
