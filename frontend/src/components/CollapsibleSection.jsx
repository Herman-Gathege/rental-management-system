//frontend\src\components\CollapsibleSection.jsx
import { useState } from "react";

/**
 * Reusable collapsible section for grouping form fields.
 *
 * Usage:
 *   <CollapsibleSection title="Next of Kin" defaultOpen={false}>
 *     <input ... />
 *     <input ... />
 *   </CollapsibleSection>
 */
export default function CollapsibleSection({
  title,
  children,
  defaultOpen = false,
  summary = null
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div
      className="card"
      style={{
        marginBottom: "1rem",
        padding: 0,
        overflow: "hidden",
      }}
    >
      {/* Header — clickable */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        style={{
          width: "100%",
          padding: "12px 16px",
          background: "#f9fafb",
          border: "none",
          borderBottom: open ? "1px solid #e5e7eb" : "none",
          textAlign: "left",
          cursor: "pointer",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontWeight: 600,
          fontSize: "0.95rem",
        }}
      >
        <span>
          {title}
          {summary && !open && (
            <span className="text-sm text-muted" style={{ marginLeft: 8, fontWeight: 400 }}>
              — {summary}
            </span>
          )}
        </span>
        <span style={{ fontSize: "1.2rem", color: "#6b7280" }}>
          {open ? "−" : "+"}
        </span>
      </button>

      {/* Body */}
      {open && (
        <div style={{ padding: "16px" }}>
          {children}
        </div>
      )}
    </div>
  );
}
