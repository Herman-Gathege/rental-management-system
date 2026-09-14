/* frontend/src/features/properties/Properties.jsx */
//
// Properties list.
//
// Landlord-only CRUD (requirement 1): create, view, edit and delete are exposed
// here, but the backend is the source of truth — a property manager or finance
// user calling these endpoints directly still gets a 403, and a property with
// units cannot be deleted at all. The UI simply reflects what the API allows.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteProperty, getProperties } from "../../api/properties";
import { useAuth } from "../../context/AuthContext";
import { useDebouncedValue } from "../../hooks/useDebouncedValue";
import {
  EmptyState,
  ErrorState,
  NoResultsState,
  TableSearch,
  TableSkeleton,
} from "../../components/ui/States";

export default function Properties() {
  const { user } = useAuth();
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [success, setSuccess] = useState("");
  const [deletingId, setDeletingId] = useState(null);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 250);

  const canManage = user?.role === "LANDLORD";

  const fetchProperties = async () => {
    try {
      setLoading(true);
      setError("");
      setProperties(await getProperties());
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load properties");
      setProperties([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProperties();
  }, []);

  const handleDelete = async (property) => {
    if (
      !confirm(
        `Delete "${property.name}"? This cannot be undone. Properties that still have units can't be deleted.`,
      )
    ) {
      return;
    }

    setActionError("");
    setSuccess("");
    setDeletingId(property.id);
    try {
      await deleteProperty(property.id);
      setProperties((prev) => prev.filter((p) => p.id !== property.id));
      setSuccess(`${property.name} was deleted.`);
      setTimeout(() => setSuccess(""), 4000);
    } catch (err) {
      // The API explains exactly why a delete was refused (e.g. the property
      // still has units) — surface that instead of a generic failure.
      setActionError(
        err?.response?.data?.detail || "Could not delete this property.",
      );
    } finally {
      setDeletingId(null);
    }
  };

  const term = debouncedSearch.trim().toLowerCase();
  const visible = term
    ? properties.filter((p) =>
        `${p.name} ${p.address} ${p.city} ${p.country}`
          .toLowerCase()
          .includes(term),
      )
    : properties;

  if (loading) {
    return (
      <section className="properties-page">
        <div className="properties-header">
          <h2>Properties</h2>
        </div>
        <TableSkeleton rows={6} columns={6} />
      </section>
    );
  }

  if (error) {
    return (
      <section className="properties-page">
        <div className="properties-header">
          <h2>Properties</h2>
        </div>
        <ErrorState
          title="Couldn’t load properties"
          description={error}
          onRetry={fetchProperties}
        />
      </section>
    );
  }

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Properties</h2>
        {canManage && (
          <Link to="/owner/properties/new" className="btn btn-primary btn-sm">
            + Add Property
          </Link>
        )}
      </div>

      {success && <div className="success-banner mb-sm">{success}</div>}
      {actionError && <div className="error-text mb-sm">{actionError}</div>}

      {properties.length === 0 ? (
        <EmptyState
          title="No properties yet"
          description="A property is the top-level container for units, tenants, leases and all financial records."
          action={
            canManage ? (
              <Link to="/owner/properties/new" className="btn btn-primary">
                Create your first property
              </Link>
            ) : null
          }
        />
      ) : (
        <>
          <div className="mb-sm">
            <TableSearch
              id="properties-search"
              value={search}
              onChange={setSearch}
              placeholder="Search by name, address or city…"
              label="Search properties"
            />
          </div>

          {visible.length === 0 ? (
            <NoResultsState term={debouncedSearch} onClear={() => setSearch("")} />
          ) : (
            <>
              {/* Desktop Table */}
              <div className="properties-table-wrapper hidden-mobile">
                <table className="properties-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Address</th>
                      <th>City</th>
                      <th>Country</th>
                      <th>Created</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((prop) => (
                      <tr key={prop.id}>
                        <td className="prop-name">{prop.name}</td>
                        <td>{prop.address}</td>
                        <td>{prop.city}</td>
                        <td>{prop.country}</td>
                        <td>
                          {prop.created_at
                            ? new Date(prop.created_at).toLocaleDateString()
                            : "—"}
                        </td>
                        <td>
                          <div className="flex gap-xs">
                            <Link
                              to={`/owner/properties/${prop.id}`}
                              className="btn btn-secondary btn-sm"
                            >
                              View
                            </Link>
                            {canManage && (
                              <>
                                <Link
                                  to={`/owner/properties/${prop.id}/edit`}
                                  className="btn btn-secondary btn-sm"
                                >
                                  Edit
                                </Link>
                                <button
                                  type="button"
                                  className="btn btn-secondary btn-sm dropdown-danger"
                                  onClick={() => handleDelete(prop)}
                                  disabled={deletingId === prop.id}
                                >
                                  {deletingId === prop.id ? "Deleting…" : "Delete"}
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
                {visible.map((prop) => (
                  <div key={prop.id} className="property-card card">
                    <div className="property-card-header">
                      <strong>{prop.name}</strong>
                    </div>
                    <div className="text-sm">{prop.address}</div>
                    <div className="text-sm text-muted">
                      {prop.city}, {prop.country}
                    </div>
                    <div className="flex gap-xs mt-sm">
                      <Link
                        to={`/owner/properties/${prop.id}`}
                        className="btn btn-secondary btn-sm"
                      >
                        View details
                      </Link>
                      {canManage && (
                        <Link
                          to={`/owner/properties/${prop.id}/edit`}
                          className="btn btn-secondary btn-sm"
                        >
                          Edit
                        </Link>
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
