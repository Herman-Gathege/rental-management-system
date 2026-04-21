// frontend/src/features/super-admin/Organizations.jsx
import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";
import SuperAdminLayout from "../dashboard/layout/SuperAdminLayout";

export default function Organizations() {
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const [name, setName] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [ownerPassword, setOwnerPassword] = useState("");

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);

  const fetchOrgs = async () => {
    try {
      setLoading(true);
      const res = await apiFetch("/api/super-admin/organizations");
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to fetch organizations");

      // latest first
      setOrgs(Array.isArray(data) ? data.sort((a, b) => b.id - a.id) : []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgs();
  }, []);

  const createOrg = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const res = await apiFetch("/api/super-admin/organizations", {
        method: "POST",
        body: JSON.stringify({
          name,
          owner_name: ownerName,
          owner_email: ownerEmail,
          owner_password: ownerPassword,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to create organization");

      setSuccessMessage(data.message);
      setName("");
      setOwnerName("");
      setOwnerEmail("");
      setOwnerPassword("");
      fetchOrgs();
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  // ---------------------------
  // Pagination logic
  // ---------------------------
  const totalPages = Math.ceil(orgs.length / itemsPerPage);
  const paginatedOrgs = orgs.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <SuperAdminLayout>
      <section className="card flex flex-col gap-lg">
        <h2>Manage Organizations</h2>

        {successMessage && <div className="success-banner">{successMessage}</div>}
        {error && <div className="error-text">{error}</div>}

        {/* ======= Add Organization Form ======= */}
        <form className="flex flex-col gap-sm mb-md" onSubmit={createOrg}>
          <input
            className="input"
            placeholder="Organization Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            className="input"
            placeholder="Owner Full Name"
            value={ownerName}
            onChange={(e) => setOwnerName(e.target.value)}
            required
          />
          <input
            className="input"
            type="email"
            placeholder="Owner Email"
            value={ownerEmail}
            onChange={(e) => setOwnerEmail(e.target.value)}
            required
          />
          <input
            className="input"
            type="password"
            placeholder="Owner Password"
            value={ownerPassword}
            onChange={(e) => setOwnerPassword(e.target.value)}
            required
          />
          <button className="btn btn-primary btn-sm" type="submit">
            Create Organization
          </button>
        </form>

        {/* ======= List Organizations ======= */}
{loading ? (
  <p>Loading...</p>
) : (
  <>
    {/* Desktop Table */}
    <div className="customers-table-wrapper hidden-mobile">
      <table className="customers-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Subscription</th>
            <th>Active</th>
            <th>Days Remaining</th>
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
                <td>{org.is_active ? "Active" : "Inactive"}</td>
                <td>{org.days_remaining ?? "-"}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>

    {/* Mobile Cards */}
    <div className="hidden-desktop flex flex-col gap-sm">
      {paginatedOrgs.length === 0 && (
        <p className="text-muted">No organizations found</p>
      )}

      {paginatedOrgs.map((org) => (
        <div key={org.id} className="card flex flex-col gap-xs">
          <div className="text-sm">
            <strong>{org.name}</strong>
          </div>

          <div className="text-sm">
            <strong>Subscription:</strong> {org.subscription_status}
          </div>

          <div className="text-sm">
            <strong>Status:</strong>{" "}
            {org.is_active ? "Active" : "Inactive"}
          </div>

          <div className="text-sm">
            <strong>Days Remaining:</strong>{" "}
            {org.days_remaining ?? "-"}
          </div>
        </div>
      ))}
    </div>

    {/* Pagination */}
    <div className="pagination flex gap-sm mt-md justify-center">
      <button
        className="btn btn-secondary btn-sm"
        onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
        disabled={currentPage === 1}
      >
        Prev
      </button>

      <span className="text-sm">
        Page {currentPage} of {totalPages}
      </span>

      <button
        className="btn btn-secondary btn-sm"
        onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
        disabled={currentPage === totalPages}
      >
        Next
      </button>
    </div>
  </>
)}
      </section>
    </SuperAdminLayout>
  );
}