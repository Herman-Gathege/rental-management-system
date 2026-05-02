/*frontend\src\features\properties\propertydetail.jsx*/

import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getProperty, assignManager, removeManager } from "../../api/properties";
import { getMyOrganization } from "../../api/organizations";
// import "./Properties.css";

export default function PropertyDetail() {
  const { propertyId } = useParams();

  const [property, setProperty] = useState(null);
  const [orgMembers, setOrgMembers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchData = async () => {
    try {
      setLoading(true);
      const [propData, orgData] = await Promise.all([
        getProperty(propertyId),
        getMyOrganization(),
      ]);

      setProperty(propData);

      // Filter to only show PROPERTY_MANAGER members who aren't already assigned
      const assignedIds = (propData.managers || []).map((m) => m.user_id);
      const available = orgData.members.filter(
        (m) =>
          m.role === "PROPERTY_MANAGER" && !assignedIds.includes(m.user_id)
      );
      setOrgMembers(available);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load property");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [propertyId]);

  const handleAssign = async () => {
    if (!selectedUserId) return;
    setError("");
    try {
      await assignManager(propertyId, selectedUserId);
      setSuccess("Manager assigned!");
      setSelectedUserId("");
      await fetchData();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to assign manager");
    }
  };

  const handleRemove = async (userId) => {
    setError("");
    try {
      await removeManager(propertyId, userId);
      setSuccess("Manager removed");
      await fetchData();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to remove manager");
    }
  };

  if (loading) return <p>Loading...</p>;
  if (error && !property) return <p className="error-text">{error}</p>;

  return (
    <section className="property-detail">
      <div className="properties-header">
        <h2>{property.name}</h2>
        <Link to="/owner/properties" className="btn btn-secondary btn-sm">
          ← Back to Properties
        </Link>
      </div>

      {success && <div className="success-banner">{success}</div>}
      {error && <div className="error-text">{error}</div>}

      {/* Property Info */}
      <div className="card">
        <div className="property-info-grid">
          <div className="info-item">
            <label>Address</label>
            <span>{property.address}</span>
          </div>
          <div className="info-item">
            <label>City</label>
            <span>{property.city}</span>
          </div>
          <div className="info-item">
            <label>Country</label>
            <span>{property.country}</span>
          </div>
          <div className="info-item">
            <label>Created</label>
            <span>{new Date(property.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      {/* Managers */}
      <div className="card managers-section">
        <h3>Assigned Managers</h3>

        {(property.managers || []).length === 0 ? (
          <p className="text-muted">No managers assigned yet.</p>
        ) : (
          property.managers.map((mgr) => (
            <div key={mgr.user_id} className="manager-row">
              <span>{mgr.email}</span>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handleRemove(mgr.user_id)}
              >
                Remove
              </button>
            </div>
          ))
        )}

        {/* Assign new manager */}
        {orgMembers.length > 0 && (
          <div className="assign-form">
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
            >
              <option value="">Select a manager...</option>
              {orgMembers.map((m) => (
                <option key={m.user_id} value={m.user_id}>
                  {m.email}
                </option>
              ))}
            </select>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleAssign}
              disabled={!selectedUserId}
            >
              Assign
            </button>
          </div>
        )}

        {orgMembers.length === 0 && (property.managers || []).length === 0 && (
          <p className="text-sm text-muted">
            Invite a property manager to your organization first, then assign
            them here.
          </p>
        )}
      </div>
    </section>
  );
}
