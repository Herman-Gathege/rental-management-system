/*frontend\src\features\properties\properties.jsx*/

import { useEffect, useState } from "react";
import { getProperties } from "../../../api/properties";
import { Link } from "react-router-dom";
import "./Properties.css";

export default function Properties() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await getProperties();
        setProperties(data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load properties");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  if (loading) return <p>Loading properties...</p>;
  if (error) return <p className="error-text">{error}</p>;

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Properties</h2>
        <Link to="/owner/properties/new" className="btn btn-primary btn-sm">
          + Add Property
        </Link>
      </div>

      {properties.length === 0 ? (
        <div className="empty-state">
          <p>No properties yet.</p>
          <p className="text-muted">
            Add your first property to start managing units and tenants.
          </p>
          <Link to="/owner/properties/new" className="btn btn-primary">
            Create Your First Property
          </Link>
        </div>
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
                {properties.map((prop) => (
                  <tr key={prop.id}>
                    <td className="prop-name">{prop.name}</td>
                    <td>{prop.address}</td>
                    <td>{prop.city}</td>
                    <td>{prop.country}</td>
                    <td>
                      {new Date(prop.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <Link
                        to={`/owner/properties/${prop.id}`}
                        className="btn btn-secondary btn-sm"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="hidden-desktop properties-cards">
            {properties.map((prop) => (
              <div key={prop.id} className="property-card card">
                <div className="property-card-header">
                  <strong>{prop.name}</strong>
                </div>
                <div className="text-sm">{prop.address}</div>
                <div className="text-sm text-muted">
                  {prop.city}, {prop.country}
                </div>
                <Link
                  to={`/owner/properties/${prop.id}`}
                  className="btn btn-secondary btn-sm mt-sm"
                >
                  View Details
                </Link>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
