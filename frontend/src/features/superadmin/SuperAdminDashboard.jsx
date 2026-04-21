import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";
import SuperAdminLayout from "../dashboard/layout/SuperAdminLayout";

export default function SuperAdminDashboard() {
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);

  useEffect(() => {
    fetchOrgs();
  }, []);

  const fetchOrgs = async () => {
    try {
      setLoading(true);
      const res = await apiFetch("/api/super-admin/organizations");
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to fetch organizations");
      setOrgs(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const upgrade = async (id) => {
    try {
      await apiFetch(`/api/super-admin/organizations/${id}/upgrade`, {
        method: "POST",
      });
      setSuccessMessage("Organization upgraded successfully");
      fetchOrgs();
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch {
      setError("Failed to upgrade organization");
    }
  };

  const deactivate = async (id) => {
    try {
      await apiFetch(`/api/super-admin/organizations/${id}/deactivate`, {
        method: "POST",
      });
      setSuccessMessage("Organization deactivated successfully");
      fetchOrgs();
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch {
      setError("Failed to deactivate organization");
    }
  };

  const activate = async (id) => {
  try {
    await apiFetch(`/api/super-admin/organizations/${id}/activate`, {
      method: "POST",
    });
    setSuccessMessage("Organization activated successfully");
    fetchOrgs();
    setTimeout(() => setSuccessMessage(""), 3000);
  } catch {
    setError("Failed to activate organization");
  }
};

// const deleteOrg = async (id, name) => {
//   if (!window.confirm(`Are you sure you want to delete "${name}"? This cannot be undone.`)) {
//     return;
//   }

//   try {
//     const res = await apiFetch(`/api/super-admin/organizations/${id}`, {
//       method: "DELETE",
//     });

//     const data = await res.json();
//     if (!res.ok) throw new Error(data.error || "Failed to delete organization");

//     setSuccessMessage(data.message);
//     fetchOrgs();
//     setTimeout(() => setSuccessMessage(""), 3000);
//   } catch (err) {
//     setError(err.message || "Failed to delete organization");
//   }
// };

  // 🔎 Search filter
  const filteredOrgs = orgs.filter((org) =>
    org.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPages = Math.ceil(filteredOrgs.length / itemsPerPage);

  const paginatedOrgs = filteredOrgs.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  if (loading) return <p>Loading...</p>;
  if (error) return <p className="error-text">{error}</p>;

  return (

    <SuperAdminLayout>
    <section className="card flex flex-col gap-lg">
      <h2>Super Admin Portal</h2>

      {/* Search */}
      <div className="flex flex-mobile-col gap-sm mb-md">
        <input
          className="input"
          placeholder="Search organization..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1);
          }}
        />
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => {
            setSearchTerm("");
            setCurrentPage(1);
          }}
        >
          Clear Search
        </button>
      </div>

      {successMessage && (
        <div className="success-banner">{successMessage}</div>
      )}

      {/* Desktop Table */}
      <div className="customers-table-wrapper stock-table-wrapper hidden-on-mobile">
        <table className="customers-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Subscription</th>
              <th>Package</th>
              {/* <th>Active</th> */}
              <th>Days Remaining</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedOrgs.length === 0 ? (
              <tr>
                <td colSpan="4">No organizations found</td>
              </tr>
            ) : (
              paginatedOrgs.map((org) => (
                <tr key={org.id}>
                  <td>{org.name}</td>
                  <td>{org.subscription_status}</td>
                  <td>{org.plan}</td> 

                  {/* <td>{org.is_active ? "Active" : "Inactive"}</td> */}
                        <td>{org.days_remaining !== null ? org.days_remaining : "-"}</td> {/* Show days remaining */}

                  <td className="flex gap-sm">
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => upgrade(org.id)}
                  >
                    Upgrade
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => deactivate(org.id)}
                  >
                    Deactivate
                  </button>
                  {!org.is_active && (
                    <button
                      className="btn primary-btn btn-sm"
                      onClick={() => activate(org.id)}
                    >
                      Activate
                    </button>
                  )}
                  {/* <button
                    className="btn btn-danger btn-sm"
                    onClick={() => deleteOrg(org.id, org.name)}
                  >
                    Delete
                  </button> */}
                </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        <div className="pagination flex gap-sm mt-md justify-center">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
          >
            Prev
          </button>

          <button
            className="btn btn-secondary btn-sm"
            onClick={() =>
              setCurrentPage((prev) => Math.min(prev + 1, totalPages))
            }
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      </div>

      {/* Mobile Cards */}
      <div className="stock-cards hidden-desktop">
        {paginatedOrgs.map((org) => (
          <div key={org.id} className="card flex flex-col gap-sm">
            <strong className="text-md">{org.name}</strong>

            <div className="text-sm">
              <span className="text-muted">Subscription:</span>{" "}
              {org.subscription_status}
            </div>

            <div className="text-sm">
              <span className="text-muted">Status:</span>{" "}
              {org.is_active ? "Active" : "Inactive"}
            </div>

            <div className="flex gap-sm mt-sm flex-wrap">
  <button
    className="btn btn-primary btn-sm"
    onClick={() => upgrade(org.id)}
  >
    Upgrade
  </button>

  <button
    className="btn btn-danger btn-sm"
    onClick={() => deactivate(org.id)}
  >
    Deactivate
  </button>

  {!org.is_active && (
    <button
      className="btn btn-success btn-sm"
      onClick={() => activate(org.id)}
    >
      Activate
    </button>
  )}

  <button
    className="btn btn-danger btn-sm"
    onClick={() => deleteOrg(org.id, org.name)}
  >
    Delete
  </button>
</div>
          </div>
        ))}

        <div className="pagination flex gap-sm mt-md justify-center hidden-desktop">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
          >
            Prev
          </button>

          <button
            className="btn btn-secondary btn-sm"
            onClick={() =>
              setCurrentPage((prev) => Math.min(prev + 1, totalPages))
            }
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      </div>
    </section>
    </SuperAdminLayout>
  );
}