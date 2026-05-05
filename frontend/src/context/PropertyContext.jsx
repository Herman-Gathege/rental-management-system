/*frontend\src\context\PropertyContext.jsx */

import { createContext, useContext, useEffect, useState } from "react";
import { getProperties } from "../api/properties";
import { useAuth } from "./AuthContext";

const PropertyContext = createContext();
export const useProperty = () => useContext(PropertyContext);

export function PropertyProvider({ children }) {
  const { user } = useAuth();
  const [properties, setProperties] = useState([]);
  const [activeProperty, setActiveProperty] = useState(null);
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

        const savedId = localStorage.getItem("active_property_id");
        const saved = data.find((p) => p.id === savedId);

        if (saved) {
          setActiveProperty(saved);
        } else if (data.length > 0) {
          setActiveProperty(data[0]);
        }
      } catch (err) {
        console.error("Failed to fetch properties:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProperties();
  }, [user]);

  const switchProperty = (property) => {
    setActiveProperty(property);
    localStorage.setItem("active_property_id", property.id);
  };

  const refreshProperties = async () => {
    try {
      const data = await getProperties();
      setProperties(data);

      if (!activeProperty && data.length > 0) {
        setActiveProperty(data[0]);
        localStorage.setItem("active_property_id", data[0].id);
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
