//frontend\src\features\leases\LeaseDetail.jsx
import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { getLease, initiateMoveOut, uploadSignedLease } from "../../api/leases";

export default function LeaseDetail() {
  const { leaseId } = useParams();
  const navigate = useNavigate();

  const [lease, setLease] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uploadingSigned, setUploadingSigned] = useState(false);
  const [initiating, setInitiating] = useState(false);

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

  /* Initiate move-out → creates the move-out inspection, redirects to it */
  const handleInitiateMoveOut = async () => {
    if (
      !confirm(
        "Initiate move-out? This will create a move-out inspection that you must complete and sign with the tenant before the lease can be terminated."
      )
    )
      return;

    setInitiating(true);
    try {
      const result = await initiateMoveOut(leaseId);
      // Redirect straight to the move-out inspection page
      navigate(`/owner/leases/${leaseId}/inspections/${result.inspection_id}`);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to initiate move-out");
    } finally {
      setInitiating(false);
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

  const moveIn = lease.move_in_inspection;
  const moveOut = lease.move_out_inspection;

  // Move-out states
  const hasMoveOutDraft = moveOut?.status === "draft";
  const hasMoveOutSigned = moveOut?.status === "signed";

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
      <div className="card detail-card">
        <h3>Lease Details</h3>

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
      <div className="card detail-card">
        <h3>Inspections</h3>

        {/* Move-In Inspection */}
        <div className="doc-upload-row inspection-status-row">
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
        <div className="doc-upload-row inspection-status-row">
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
                "Click 'Initiate Move-Out' below to begin"
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

      {/* ─── Move-out action ─── */}
      {lease.status === "active" && (
        <div className="card detail-card info-banner-warning">
          <h3>End This Tenancy</h3>
          <p className="text-sm">
            To terminate this lease, you must first conduct and sign a move-out
            inspection with the tenant. This documents the unit's condition at
            handover and determines any deposit deductions for damage.
          </p>

          <div className="flex gap-sm mt-md">
            {!moveOut && (
              <button
                className="btn btn-primary"
                onClick={handleInitiateMoveOut}
                disabled={initiating}
              >
                {initiating ? "Creating inspection..." : "Initiate Move-Out"}
              </button>
            )}
            {hasMoveOutDraft && (
              <Link
                to={`/owner/leases/${leaseId}/inspections/${moveOut.id}`}
                className="btn btn-primary"
              >
                Continue Move-Out Inspection
              </Link>
            )}
            {hasMoveOutSigned && (
              <div className="text-sm text-muted">
                Move-out inspection is signed but lease status is still active.
                Refresh the page to see updated status.
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
