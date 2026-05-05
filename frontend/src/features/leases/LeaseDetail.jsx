//frontend\src\features\leases\LeaseDetail.jsx
import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getLease, terminateLease } from "../../api/leases";

export default function LeaseDetail() {
  const { leaseId } = useParams();
  const navigate = useNavigate();

  const [lease, setLease] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await getLease(leaseId);
        setLease(data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load lease");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [leaseId]);

  const handleTerminate = async () => {
    if (!window.confirm("Are you sure you want to terminate this lease? This cannot be undone.")) return;

    try {
      await terminateLease(leaseId);
      setSuccess("Lease terminated");
      setLease({ ...lease, status: "terminated" });
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to terminate lease");
    }
  };

  if (loading) return <p>Loading...</p>;
  if (error && !lease) return <p className="error-text">{error}</p>;

  return (
    <section className="property-detail">
      <div className="properties-header">
        <h2>Lease Details</h2>
        <Link to="/owner/leases" className="btn btn-secondary btn-sm">← Back to Leases</Link>
      </div>

      {success && <div className="success-banner">{success}</div>}
      {error && <div className="error-text">{error}</div>}

      <div className="card">
        <div className="property-info-grid">
          <div className="info-item">
            <label>Tenant</label>
            <span>{lease.tenant_name}</span>
          </div>
          <div className="info-item">
            <label>Unit</label>
            <span>{lease.unit_name}</span>
          </div>
          <div className="info-item">
            <label>Property</label>
            <span>{lease.property_name}</span>
          </div>
          <div className="info-item">
            <label>Monthly Rent</label>
            <span>KES {Number(lease.rent_amount).toLocaleString()}</span>
          </div>
          <div className="info-item">
            <label>Deposit</label>
            <span>KES {Number(lease.deposit_amount || 0).toLocaleString()}</span>
          </div>
          <div className="info-item">
            <label>Billing Day</label>
            <span>{lease.billing_day}th of each month</span>
          </div>
          <div className="info-item">
            <label>Start Date</label>
            <span>{new Date(lease.start_date).toLocaleDateString()}</span>
          </div>
          <div className="info-item">
            <label>End Date</label>
            <span>{lease.end_date ? new Date(lease.end_date).toLocaleDateString() : "Open-ended"}</span>
          </div>
          <div className="info-item">
            <label>Status</label>
            <span className={`status-pill ${lease.status === "active" ? "status-ok" : "status-owed"}`}>
              {lease.status}
            </span>
          </div>
        </div>
      </div>

      {lease.status === "active" && (
        <div className="flex gap-sm">
          <button className="btn btn-danger" onClick={handleTerminate}>
            Terminate Lease
          </button>
        </div>
      )}
    </section>
  );
}

