// frontend/src/components/GlobalSearch/GlobalSearch.jsx
//
// System-wide search palette (requirement 11).
//
//   Ctrl+K / Cmd+K  open (also via the navbar search button, which dispatches
//                   the "alphaone:open-global-search" window event)
//   Esc             close
//   ↑ / ↓           move through results (across groups)
//   Enter           open the highlighted result
//
// Results come from GET /search, which applies organisation, property and role
// scoping in the database — the palette never filters for authorisation and so
// can never reveal a record the user cannot open. The active property from the
// sidebar switcher is passed through as a filter, so search follows the same
// context as the rest of the page.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiSearch } from "react-icons/fi";
import { globalSearch } from "../../api/search";
import { useProperty } from "../../context/PropertyContext";
import { LoadingState, NoResultsState, ErrorState } from "../ui/States";
import "./GlobalSearch.css";

const DEBOUNCE_MS = 250;
const MIN_TERM_LENGTH = 2;

export default function GlobalSearch() {
  const navigate = useNavigate();
  const { activeProperty } = useProperty();

  const [open, setOpen] = useState(false);
  const [term, setTerm] = useState("");
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  const inputRef = useRef(null);
  const panelRef = useRef(null);
  const requestRef = useRef(null);

  /* Flat list of results, in render order, so arrow keys can walk across
     group boundaries with a single index. */
  const flatResults = useMemo(
    () => groups.flatMap((group) => group.items.map((item) => ({ ...item, type: group.type }))),
    [groups],
  );

  const close = useCallback(() => {
    setOpen(false);
    setTerm("");
    setGroups([]);
    setError("");
    setActiveIndex(0);
  }, []);

  /* ── Open/close wiring ── */
  useEffect(() => {
    const onKeyDown = (event) => {
      const isPaletteShortcut =
        (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";
      if (isPaletteShortcut) {
        event.preventDefault();
        setOpen((prev) => !prev);
        return;
      }
      if (event.key === "Escape") {
        setOpen((prev) => {
          if (prev) event.preventDefault();
          return false;
        });
      }
    };

    const onOpenEvent = () => setOpen(true);

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("alphaone:open-global-search", onOpenEvent);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("alphaone:open-global-search", onOpenEvent);
    };
  }, []);

  /* Focus the input as soon as the palette opens, and restore focus after. */
  useEffect(() => {
    if (open) {
      const previouslyFocused = document.activeElement;
      inputRef.current?.focus();
      return () => {
        if (previouslyFocused instanceof HTMLElement) previouslyFocused.focus();
      };
    }
    return undefined;
  }, [open]);

  /* ── Debounced search ── */
  useEffect(() => {
    if (!open) return undefined;

    const trimmed = term.trim();
    if (trimmed.length < MIN_TERM_LENGTH) {
      // Nothing to search: results were already cleared by the input handler,
      // so this effect only needs to stop here.
      return undefined;
    }

    const handle = setTimeout(async () => {
      // Entered from a timer callback (not synchronously in the effect body)
      // so the spinner doesn't cause a cascading render on every keystroke.
      setLoading(true);
      // Cancel any in-flight request so a slow early response can't overwrite
      // the results of a later, more specific query.
      requestRef.current?.abort?.();
      const controller = new AbortController();
      requestRef.current = controller;

      try {
        const data = await globalSearch({
          query: trimmed,
          propertyId: activeProperty?.id || null,
          signal: controller.signal,
        });
        setGroups(data.groups || []);
        setActiveIndex(0);
        setError("");
      } catch (err) {
        if (err?.name === "CanceledError" || err?.code === "ERR_CANCELED") return;
        setGroups([]);
        setError(
          err?.response?.data?.detail ||
            "Search is unavailable right now. Please try again.",
        );
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(handle);
  }, [term, open, activeProperty]);

  const goTo = useCallback(
    (item) => {
      close();
      navigate(item.path);
    },
    [close, navigate],
  );

  const onInputKeyDown = (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => (flatResults.length ? (i + 1) % flatResults.length : 0));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) =>
        flatResults.length ? (i - 1 + flatResults.length) % flatResults.length : 0,
      );
    } else if (event.key === "Enter") {
      const item = flatResults[activeIndex];
      if (item) {
        event.preventDefault();
        goTo(item);
      }
    } else if (event.key === "Tab") {
      // Keep focus inside the dialog for keyboard users.
      event.preventDefault();
    }
  };

  if (!open) return null;

  const showEmpty = !loading && !error && term.trim().length >= MIN_TERM_LENGTH;
  const noResults = showEmpty && flatResults.length === 0;

  return (
    <div
      className="gs-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) close();
      }}
    >
      <div
        className="gs-panel"
        role="dialog"
        aria-modal="true"
        aria-label="Search the system"
        ref={panelRef}
      >
        <div className="gs-input-row">
          <FiSearch className="gs-input-icon" aria-hidden="true" />
          <input
            ref={inputRef}
            className="gs-input"
            type="text"
            value={term}
            onChange={(event) => {
              const value = event.target.value;
              setTerm(value);
              // Clear stale results immediately when the query becomes too
              // short to run, instead of doing it from inside the effect.
              if (value.trim().length < MIN_TERM_LENGTH) {
                setGroups([]);
                setError("");
                setLoading(false);
              }
            }}
            onKeyDown={onInputKeyDown}
            placeholder="Search properties, units, tenants, leases, payments…"
            aria-label="Search"
            autoComplete="off"
            aria-controls="gs-results"
            role="combobox"
            aria-expanded={flatResults.length > 0}
          />
          <button type="button" className="gs-esc" onClick={close}>
            Esc
          </button>
        </div>

        {activeProperty && (
          <div className="gs-scope">
            Scoped to <strong>{activeProperty.name}</strong>
          </div>
        )}

        <div className="gs-results" id="gs-results" role="listbox">
          {loading && <LoadingState label="Searching…" inline />}

          {!loading && error && (
            <ErrorState
              title="Search failed"
              description={error}
              onRetry={() => setTerm((t) => `${t} `.trim())}
            />
          )}

          {!loading &&
            !error &&
            term.trim().length < MIN_TERM_LENGTH && (
              <p className="gs-hint text-muted text-sm">
                Type at least {MIN_TERM_LENGTH} characters to search.
              </p>
            )}

          {noResults && (
            <NoResultsState
              term={term.trim()}
              onClear={() => {
                setTerm("");
                setGroups([]);
                inputRef.current?.focus();
              }}
              description="Nothing in the records you have access to matches this search."
            />
          )}

          {!loading &&
            !error &&
            groups.map((group) => (
              <div className="gs-group" key={group.type}>
                <div className="gs-group-label">{group.label}</div>
                {group.items.map((item) => {
                  const index = flatResults.findIndex(
                    (r) => r.type === group.type && r.id === item.id,
                  );
                  return (
                    <button
                      type="button"
                      key={`${group.type}-${item.id}`}
                      className={`gs-item ${index === activeIndex ? "gs-item-active" : ""}`}
                      role="option"
                      aria-selected={index === activeIndex}
                      onMouseEnter={() => setActiveIndex(index)}
                      onClick={() => goTo(item)}
                    >
                      <span className="gs-item-label">{item.label}</span>
                      {item.sublabel && (
                        <span className="gs-item-sub">{item.sublabel}</span>
                      )}
                    </button>
                  );
                })}
              </div>
            ))}
        </div>

        <div className="gs-footer">
          <span>↑↓ navigate</span>
          <span>↵ open</span>
          <span>Esc close</span>
        </div>
      </div>
    </div>
  );
}
