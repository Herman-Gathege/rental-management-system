// frontend/src/components/ui/States.jsx
//
// Shared loading / empty / error primitives (system-wide states pass).
//
// One place to get these right means every page behaves the same way: a
// skeleton instead of a blank table, an empty state that explains itself, and
// an error state with a retry. All are layout-stable — the loading variants
// reserve roughly the same height as the content they replace, so the page
// doesn't jump when data arrives.

/* ─── Spinner ─── */

export function Spinner({ size = 18, label = "Loading" }) {
  return (
    <span
      className="ui-spinner"
      style={{ width: size, height: size }}
      role="status"
      aria-label={label}
    />
  );
}

/* ─── Inline / page loading ─── */

export function LoadingState({ label = "Loading…", inline = false }) {
  return (
    <div className={`ui-loading ${inline ? "ui-loading-inline" : ""}`} role="status">
      <Spinner />
      <span className="text-muted text-sm">{label}</span>
    </div>
  );
}

/* ─── Table skeleton ─── */

export function TableSkeleton({ rows = 6, columns = 5 }) {
  return (
    <div className="ui-skeleton" aria-hidden="true">
      {Array.from({ length: rows }).map((_, r) => (
        <div className="ui-skeleton-row" key={r}>
          {Array.from({ length: columns }).map((__, c) => (
            <span className="ui-skeleton-cell" key={c} />
          ))}
        </div>
      ))}
    </div>
  );
}

/* ─── Empty state ─── */

/**
 * EmptyState
 *
 * `variant="search"` renders the no-search-results wording, which must be
 * visibly different from "there are no records yet" — otherwise users can't
 * tell whether a filter hid their data or the data doesn't exist.
 *
 * `action` is only rendered when the caller passes one, so we never imply an
 * action the user isn't allowed to take.
 */
export function EmptyState({
  title,
  description,
  action = null,
  variant = "empty",
  icon = null,
}) {
  return (
    <div className={`empty-state ui-empty ui-empty-${variant}`}>
      {icon && <div className="ui-empty-icon">{icon}</div>}
      <p className="ui-empty-title">{title}</p>
      {description && <p className="text-muted text-sm">{description}</p>}
      {action && <div className="ui-empty-action">{action}</div>}
    </div>
  );
}

export function NoResultsState({ term, onClear, description }) {
  return (
    <EmptyState
      variant="search"
      title={term ? `No matches for “${term}”` : "No matching results"}
      description={
        description ||
        "Try a different search term, or clear the filters to see everything again."
      }
      action={
        onClear ? (
          <button type="button" className="btn btn-secondary btn-sm" onClick={onClear}>
            Clear search
          </button>
        ) : null
      }
    />
  );
}

/* ─── Error state ─── */

export function ErrorState({
  title = "Something went wrong",
  description,
  onRetry,
  retryLabel = "Try again",
}) {
  return (
    <div className="ui-error" role="alert">
      <p className="ui-error-title">{title}</p>
      {description && <p className="text-sm">{description}</p>}
      {onRetry && (
        <button type="button" className="btn btn-secondary btn-sm" onClick={onRetry}>
          {retryLabel}
        </button>
      )}
    </div>
  );
}

/* ─── Table search input (page-local search) ─── */

export function TableSearch({
  value,
  onChange,
  placeholder = "Search…",
  label = "Search this list",
  id = "table-search",
}) {
  return (
    <div className="ui-table-search">
      <label className="sr-only" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        type="search"
        className="input"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
      {value && (
        <button
          type="button"
          className="ui-table-search-clear"
          onClick={() => onChange("")}
          aria-label="Clear search"
        >
          ×
        </button>
      )}
    </div>
  );
}
