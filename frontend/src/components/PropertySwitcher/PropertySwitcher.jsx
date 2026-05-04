/*frontend\src\components\PropertySwitcher.jsx*/

import { useState, useRef, useEffect } from "react";
import { useProperty } from "../../context/PropertyContext";
import "./PropertySwitcher.css";

export default function PropertySwitcher() {
  const { properties, activeProperty, switchProperty } = useProperty();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (properties.length === 0) {
    return <span className="switcher-empty">No properties yet</span>;
  }

  return (
    <div className="property-switcher" ref={ref}>
      <button
        className="switcher-trigger"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="switcher-icon">🏠</span>
        <span className="switcher-label">
          {activeProperty ? activeProperty.name : "Select Property"}
        </span>
        <span className={`switcher-arrow ${open ? "open" : ""}`}>▾</span>
      </button>

      {open && (
        <div className="switcher-dropdown">
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
              <span className="option-city">{prop.city}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
