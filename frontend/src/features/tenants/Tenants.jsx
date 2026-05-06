//frontend\src\features\tenants\Tenants.jsx
import { useEffect, useState } from "react";
import { getTenants } from "../../api/tenants";
import { Link } from "react-router-dom";

export default function Tenants() {
  const [tenants, setTenants] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchTenants = async (query = null) => {
    try {
      setLoading(true);
      const data = await getTenants(query);
      setTenants(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load tenants");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTenants();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchTenants(search || null);
  };

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Tenants</h2>
        <Link to="/owner/tenants/add" className="btn btn-primary btn-sm">+ Add Tenant</Link>
      </div>

      {/* Search */}
      <div className="flex gap-sm items-center flex-wrap">
        <input
          className="input"
          placeholder="Search by name, phone, ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 300 }}
        />
        <button className="btn btn-secondary btn-sm" onClick={handleSearch}>Search</button>
      </div>

      {loading ? (
        <p>Loading tenants...</p>
      ) : error ? (
        <p className="error-text">{error}</p>
      ) : tenants.length === 0 ? (
        <div className="empty-state">
          <p>No tenants yet.</p>
          <p className="text-muted">Add tenants to assign them to units with leases.</p>
          <Link to="/owner/tenants/add" className="btn btn-primary">Add First Tenant</Link>
        </div>
      ) : (
        <>
          {/* Desktop Table */}
          <div className="properties-table-wrapper hidden-mobile">
            <table className="properties-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Phone</th>
                  <th>Email</th>
                  <th>ID Number</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {tenants.map((t) => (
                  <tr key={t.id}>
                    <td className="prop-name">{t.full_name}</td>
                    <td>{t.phone}</td>
                    <td>{t.email || "—"}</td>
                    <td>{t.id_number || "—"}</td>
                    <td>
                      <Link to={`/owner/tenants/${t.id}`} className="btn btn-secondary btn-sm">View</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="hidden-desktop properties-cards">
            {tenants.map((t) => (
              <div key={t.id} className="property-card card">
                <strong>{t.full_name}</strong>
                <div className="text-sm">{t.phone}</div>
                {t.email && <div className="text-sm text-muted">{t.email}</div>}
                <Link to={`/owner/tenants/${t.id}`} className="btn btn-secondary btn-sm mt-sm">View</Link>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

