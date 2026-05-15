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
  summary = null,
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="card collapsible-section">
      {/* Header — clickable */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={`collapsible-header ${open ? "open" : ""}`}
      >
        <span>
          {title}
          {summary && !open && (
            <span className="collapsible-summary">— {summary}</span>
          )}
        </span>
        <span className="collapsible-toggle">{open ? "−" : "+"}</span>
      </button>

      {/* Body */}
      {open && <div className="collapsible-body">{children}</div>}
    </div>
  );
}
