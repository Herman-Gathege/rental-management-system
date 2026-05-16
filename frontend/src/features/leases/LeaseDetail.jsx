//frontend\src\features\leases\LeaseDetail.jsx
import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { getLease, terminateLease, uploadSignedLease } from "../../api/leases";

export default function LeaseDetail() {
  const { leaseId } = useParams();
  const navigate = useNavigate();

  const [lease, setLease] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uploadingSigned, setUploadingSigned] = useState(false);

  const fetchLease = async () => {
    try {
      setLoading(true);
      const data = await getLease(leaseId);
      setLease(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load lease");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLease();
  }, [leaseId]);

  /* Terminate lease */
  const handleTerminate = async () => {
    if (!confirm("Terminate this lease? This action will end the tenancy.")) return;
    try {
      await terminateLease(leaseId);
      fetchLease();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to terminate lease");
    }
  };

  /* Upload signed lease document */
  const handleSignedUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadingSigned(true);
    try {
      await uploadSignedLease(leaseId, file);
      fetchLease();
    } catch (err) {
      alert(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploadingSigned(false);
      e.target.value = "";
    }
  };

  if (loading) return <p>Loading...</p>;
  if (error) return <div className="error-text">{error}</div>;
  if (!lease) return <p>Lease not found</p>;

  /* Inspection status helpers */
  const moveIn = lease.move_in_inspection;
  const moveOut = lease.move_out_inspection;

  return (
    <section className="properties-page">
      {/* Back link */}
      <div className="flex items-center gap-sm mb-sm">
        <Link to="/owner/leases" className="text-sm checklist-back-link">
          ← All Leases
        </Link>
      </div>

      <div className="properties-header">
        <div>
          <h2>{lease.tenant_name}</h2>
          <p className="text-muted">
            {lease.unit_name} — {lease.property_name}
          </p>
        </div>
        <div className="flex gap-sm">
          <span className={`role-badge status-${lease.status}`}>{lease.status}</span>
        </div>
      </div>

      {/* ─── Lease details card ─── */}
      <div className="card" style={{ padding: "1.25rem", marginTop: "1rem" }}>
        <h3 style={{ marginTop: 0 }}>Lease Details</h3>

        <div className="two-col">
          <div>
            <div className="text-sm text-muted">Start Date</div>
            <div className="text-bold">
              {new Date(lease.start_date).toLocaleDateString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-muted">End Date</div>
            <div className="text-bold">
              {lease.end_date ? new Date(lease.end_date).toLocaleDateString() : "Open-ended"}
            </div>
          </div>
        </div>

        <div className="two-col mt-md">
          <div>
            <div className="text-sm text-muted">Move-in Date</div>
            <div className="text-bold">
              {lease.move_in_date
                ? new Date(lease.move_in_date).toLocaleDateString()
                : "Same as start date"}
            </div>
          </div>
          <div>
            <div className="text-sm text-muted">Billing Day</div>
            <div className="text-bold">Day {lease.billing_day} of month</div>
          </div>
        </div>

        <div className="two-col mt-md">
          <div>
            <div className="text-sm text-muted">Monthly Rent</div>
            <div className="text-bold">
              KES {Number(lease.rent_amount).toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-muted">Security Deposit</div>
            <div className="text-bold">
              KES {Number(lease.deposit_amount).toLocaleString()}
            </div>
          </div>
        </div>

        {lease.signed_on_behalf_of && (
          <div className="mt-md">
            <div className="text-sm text-muted">Signed On Behalf Of</div>
            <div className="text-bold">{lease.signed_on_behalf_of}</div>
          </div>
        )}

        {/* Signed lease document */}
        <div className="mt-md">
          <div className="text-sm text-muted">Signed Lease Document</div>
          {lease.signed_lease_url ? (
            <div className="flex gap-sm items-center">
              <a
                href={lease.signed_lease_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary btn-sm"
              >
                View Document
              </a>
              <label className="btn btn-secondary btn-sm doc-upload-label">
                {uploadingSigned ? "Uploading..." : "Replace"}
                <input
                  type="file"
                  accept="application/pdf,image/*"
                  onChange={handleSignedUpload}
                  disabled={uploadingSigned}
                  className="doc-upload-hidden-input"
                />
              </label>
            </div>
          ) : (
            <label className="btn btn-secondary btn-sm doc-upload-label">
              {uploadingSigned ? "Uploading..." : "Upload Signed Lease"}
              <input
                type="file"
                accept="application/pdf,image/*"
                onChange={handleSignedUpload}
                disabled={uploadingSigned}
                className="doc-upload-hidden-input"
              />
            </label>
          )}
        </div>
      </div>

      {/* ─── Inspections card ─── */}
      <div className="card" style={{ padding: "1.25rem", marginTop: "1rem" }}>
        <h3 style={{ marginTop: 0 }}>Inspections</h3>

        {/* Move-In Inspection */}
        <div
          className="doc-upload-row"
          style={{ paddingTop: "12px", paddingBottom: "12px" }}
        >
          <div className="doc-upload-row-info">
            <div className="text-bold">Move-In Inspection</div>
            <div className="text-sm text-muted">
              {moveIn ? (
                <>
                  Status: <strong>{moveIn.status}</strong>
                  {moveIn.inspection_date &&
                    ` · Conducted ${new Date(moveIn.inspection_date).toLocaleDateString()}`}
                </>
              ) : (
                "Not started"
              )}
            </div>
          </div>
          {moveIn && (
            <Link
              to={`/owner/leases/${leaseId}/inspections/${moveIn.id}`}
              className="btn btn-primary btn-sm"
            >
              {moveIn.status === "draft" ? "Conduct" : "View"}
            </Link>
          )}
        </div>

        {/* Move-Out Inspection */}
        <div
          className="doc-upload-row"
          style={{ paddingTop: "12px", paddingBottom: "12px" }}
        >
          <div className="doc-upload-row-info">
            <div className="text-bold">Move-Out Inspection</div>
            <div className="text-sm text-muted">
              {moveOut ? (
                <>
                  Status: <strong>{moveOut.status}</strong>
                  {moveOut.inspection_date &&
                    ` · Conducted ${new Date(moveOut.inspection_date).toLocaleDateString()}`}
                </>
              ) : lease.status === "active" ? (
                "Will be created when lease termination is initiated"
              ) : (
                "Not applicable"
              )}
            </div>
          </div>
          {moveOut && (
            <Link
              to={`/owner/leases/${leaseId}/inspections/${moveOut.id}`}
              className="btn btn-primary btn-sm"
            >
              {moveOut.status === "draft" ? "Conduct" : "View"}
            </Link>
          )}
        </div>
      </div>

      {/* ─── Actions ─── */}
      {lease.status === "active" && (
        <div className="flex gap-sm mt-md">
          <button className="btn btn-danger" onClick={handleTerminate}>
            Terminate Lease
          </button>
        </div>
      )}
    </section>
  );
}
