// frontend/src/components/PropertySwitcher/TenantPropertySwitcher.jsx
//
// Property switcher for the tenant portal (Sprint 4.5). Same look as the
// landlord PropertySwitcher (shares PropertySwitcher.css), but its options come
// from the tenant's OWN leased properties plus an "All Properties" option.
// Hidden automatically when the tenant has only one property -- nothing to
// switch between.

import { useState, useRef, useEffect } from "react";
import { useTenantProperty } from "../../context/TenantPropertyContext";
import "./PropertySwitcher.css";

export default function TenantPropertySwitcher() {
  const ctx = useTenantProperty();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (!ctx) return null;

  const { properties, activeProperty, switchProperty } = ctx;

  // A tenant with a single property has nothing to switch between.
  if (properties.length <= 1) return null;

  return (
    <div className="property-switcher" ref={ref}>
      <button
        className="switcher-trigger"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="switcher-icon">🏠</span>
        <span className="switcher-label">
          {activeProperty ? activeProperty.name : "All Properties"}
        </span>
        <span className={`switcher-arrow ${open ? "open" : ""}`}>▾</span>
      </button>

      {open && (
        <div className="switcher-dropdown">
          <button
            className={`switcher-option ${!activeProperty ? "active" : ""}`}
            onClick={() => {
              switchProperty(null);
              setOpen(false);
            }}
          >
            <span className="option-name">All Properties</span>
          </button>

          {properties.map((prop) => (
            <button
              key={prop.id}
              className={`switcher-option ${
                activeProperty?.id === prop.id ? "active" : ""
              }`}
              onClick={() => {
                switchProperty(prop);
                setOpen(false);
              }}
            >
              <span className="option-name">{prop.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
