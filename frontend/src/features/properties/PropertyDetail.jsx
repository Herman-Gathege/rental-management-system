/*frontend\src\features\properties\PropertyDetail.jsx*/

import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getProperty,
  assignManager,
  removeManager,
  assignFinance,
  removeFinance,
} from "../../api/properties";
import { getMyOrganization } from "../../api/organizations";
// import "./Properties.css";

export default function PropertyDetail() {
  const { propertyId } = useParams();

  const [property, setProperty] = useState(null);
  const [orgMembers, setOrgMembers] = useState([]);
  const [financeMembers, setFinanceMembers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [selectedFinanceId, setSelectedFinanceId] = useState("");
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

      // Property managers not already assigned.
      const assignedPmIds = (propData.managers || []).map((m) => m.user_id);
      setOrgMembers(
        orgData.members.filter(
          (m) =>
            m.role === "PROPERTY_MANAGER" && !assignedPmIds.includes(m.user_id)
        )
      );

      // Finance members not already assigned.
      const assignedFinIds = (propData.finance_managers || []).map(
        (m) => m.user_id
      );
      setFinanceMembers(
        orgData.members.filter(
          (m) => m.role === "FINANCE" && !assignedFinIds.includes(m.user_id)
        )
      );
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

  const handleAssignFinance = async () => {
    if (!selectedFinanceId) return;
    setError("");
    try {
      await assignFinance(propertyId, selectedFinanceId);
      setSuccess("Finance manager assigned!");
      setSelectedFinanceId("");
      await fetchData();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to assign finance manager");
    }
  };

  const handleRemoveFinance = async (userId) => {
    setError("");
    try {
      await removeFinance(propertyId, userId);
      setSuccess("Finance manager removed");
      await fetchData();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to remove finance manager");
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

      {/* Finance Managers */}
      <div className="card managers-section">
        <h3>Assigned Finance Managers</h3>

        {(property.finance_managers || []).length === 0 ? (
          <p className="text-muted">No finance managers assigned yet.</p>
        ) : (
          property.finance_managers.map((fm) => (
            <div key={fm.user_id} className="manager-row">
              <span>{fm.email}</span>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handleRemoveFinance(fm.user_id)}
              >
                Remove
              </button>
            </div>
          ))
        )}

        {/* Assign new finance manager */}
        {financeMembers.length > 0 && (
          <div className="assign-form">
            <select
              value={selectedFinanceId}
              onChange={(e) => setSelectedFinanceId(e.target.value)}
            >
              <option value="">Select a finance manager...</option>
              {financeMembers.map((m) => (
                <option key={m.user_id} value={m.user_id}>
                  {m.email}
                </option>
              ))}
            </select>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleAssignFinance}
              disabled={!selectedFinanceId}
            >
              Assign
            </button>
          </div>
        )}

        {financeMembers.length === 0 &&
          (property.finance_managers || []).length === 0 && (
            <p className="text-sm text-muted">
              Invite a finance manager (FINANCE role) to your organization
              first, then assign them here.
            </p>
          )}
      </div>
    </section>
  );
}
