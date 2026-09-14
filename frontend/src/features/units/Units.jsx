//frontend\src\features\units\Units.jsx
import { useEffect, useState } from "react";
import { deleteUnit, getUnits } from "../../api/units";
import { useProperty } from "../../context/PropertyContext";
import { useAuth } from "../../context/AuthContext";
import { Link, useLocation } from "react-router-dom";
import { useDebouncedValue } from "../../hooks/useDebouncedValue";
import {
  EmptyState,
  ErrorState,
  NoResultsState,
  TableSearch,
  TableSkeleton,
} from "../../components/ui/States";

export default function Units() {
  const { activeProperty } = useProperty();
  const { user } = useAuth();
  const location = useLocation();

  // Unit create/edit/delete is a landlord action (enforced by the API). Every
  // route that mounts this page is already landlord-scoped — this guard keeps
  // the UI honest if that ever changes.
  const canManage = user?.role === "LANDLORD";

  // The "Vacant Units" menu points at /owner/units/vacant; that just preselects
  // the Vacant filter on this same page. "All Units" (/owner/units) defaults to
  // All. Either way the user can switch between All / Occupied / Vacant.
  const isVacantRoute = location.pathname.endsWith("/vacant");

  const [units, setUnits] = useState([]);
  // Derived from the route with an explicit user override, so switching
  // between "All Units" and "Vacant Units" needs no state-syncing effect.
  const [statusOverride, setStatusOverride] = useState(null);
  const statusFilter = statusOverride ?? (isVacantRoute ? "vacant" : "");
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 250);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  const fetchUnits = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getUnits(activeProperty?.id || null);
      setUnits(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load units");
      setUnits([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnits();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeProperty]);

  const handleDelete = async (unit) => {
    if (
      !confirm(
        `Delete unit "${unit.name}"? This cannot be undone. Units with lease or payment history can't be deleted.`,
      )
    ) {
      return;
    }
    setActionError("");
    setDeletingId(unit.id);
    try {
      await deleteUnit(unit.id);
      setUnits((prev) => prev.filter((u) => u.id !== unit.id));
    } catch (err) {
      setActionError(
        err?.response?.data?.detail || "Could not delete this unit.",
      );
    } finally {
      setDeletingId(null);
    }
  };

  const term = debouncedSearch.trim().toLowerCase();

  const visible = units
    .filter((u) => (statusFilter ? u.occupancy_status === statusFilter : true))
    .filter((u) =>
      term
        ? `${u.name} ${u.property_name || ""} ${u.tenant_name || ""}`
            .toLowerCase()
            .includes(term)
        : true,
    );

  if (loading) return <TableSkeleton rows={6} columns={5} />;
  if (error) {
    return (
      <ErrorState
        title="Couldn’t load units"
        description={error}
        onRetry={fetchUnits}
      />
    );
  }

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Units {activeProperty ? `— ${activeProperty.name}` : ""}</h2>
        {canManage && (
          <Link to="/owner/units/add" className="btn btn-primary btn-sm">
            + Add Unit
          </Link>
        )}
      </div>

      {actionError && <div className="error-text mb-sm">{actionError}</div>}

      {units.length === 0 ? (
        <EmptyState
          title="No units yet"
          description="Units define what you rent out and drive leases, rent charges and occupancy reporting."
          action={
            canManage ? (
              <Link to="/owner/units/add" className="btn btn-primary">
                Add first unit
              </Link>
            ) : null
          }
        />
      ) : (
        <>
          {/* Status filter */}
          <div className="flex gap-sm flex-wrap">
            {[
              { key: "", label: "All" },
              { key: "occupied", label: "Occupied" },
              { key: "vacant", label: "Vacant" },
            ].map((f) => (
              <button
                key={f.key}
                className={`btn btn-sm ${statusFilter === f.key ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setStatusOverride(f.key)}
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="mt-sm">
            <TableSearch
              id="units-search"
              value={search}
              onChange={setSearch}
              placeholder="Search unit, property or tenant…"
              label="Search units"
            />
          </div>

          {visible.length === 0 ? (
            <NoResultsState
              term={debouncedSearch || statusFilter}
              onClear={() => {
                setSearch("");
                setStatusOverride("");
              }}
              description={
                statusFilter
                  ? `No ${statusFilter} units match your search.`
                  : "No units match your search."
              }
            />
          ) : (
            <>
              {/* Desktop Table */}
              <div className="properties-table-wrapper hidden-mobile">
                <table className="properties-table">
                  <thead>
                    <tr>
                      <th>Unit</th>
                      <th>Property</th>
                      <th>Rent (KES)</th>
                      <th>Status</th>
                      <th>Tenant</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((u) => (
                      <tr key={u.id}>
                        <td className="prop-name">{u.name}</td>
                        <td>{u.property_name}</td>
                        <td>{Number(u.rent_amount).toLocaleString()}</td>
                        <td>
                          <span className={`status-pill ${u.occupancy_status === "occupied" ? "status-ok" : "status-owed"}`}>
                            {u.occupancy_status}
                          </span>
                        </td>
                        <td>{u.tenant_name || "—"}</td>
                        <td>
                          <div className="flex gap-xs">
                            <Link
                              to={`/owner/units/${u.id}`}
                              state={{ unit: u }}
                              className="btn btn-secondary btn-sm"
                            >
                              View
                            </Link>
                            {canManage && (
                              <>
                                <Link
                                  to={`/owner/units/${u.id}/edit`}
                                  state={{ unit: u }}
                                  className="btn btn-secondary btn-sm"
                                >
                                  Edit
                                </Link>
                                <button
                                  type="button"
                                  className="btn btn-secondary btn-sm dropdown-danger"
                                  onClick={() => handleDelete(u)}
                                  disabled={deletingId === u.id}
                                >
                                  {deletingId === u.id ? "Deleting…" : "Delete"}
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile Cards */}
              <div className="hidden-desktop properties-cards">
                {visible.map((u) => (
                  <div key={u.id} className="property-card card">
                    <div className="property-card-header">
                      <strong>{u.name}</strong>
                      <span className={`status-pill ${u.occupancy_status === "occupied" ? "status-ok" : "status-owed"}`}>
                        {u.occupancy_status}
                      </span>
                    </div>
                    <div className="text-sm">{u.property_name}</div>
                    <div className="text-sm">KES {Number(u.rent_amount).toLocaleString()}</div>
                    {u.tenant_name && <div className="text-sm text-muted">Tenant: {u.tenant_name}</div>}
                    <div className="flex gap-xs mt-sm">
                      <Link
                        to={`/owner/units/${u.id}`}
                        state={{ unit: u }}
                        className="btn btn-secondary btn-sm"
                      >
                        View
                      </Link>
                      {canManage && (
                        <>
                          <Link
                            to={`/owner/units/${u.id}/edit`}
                            state={{ unit: u }}
                            className="btn btn-secondary btn-sm"
                          >
                            Edit
                          </Link>
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm dropdown-danger"
                            onClick={() => handleDelete(u)}
                            disabled={deletingId === u.id}
                          >
                            {deletingId === u.id ? "Deleting…" : "Delete"}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </section>
  );
}
