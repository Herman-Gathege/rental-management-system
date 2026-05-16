//frontend\src\features\inspections\ConductInspection.jsx
import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import SignatureCanvas from "react-signature-canvas";
import {
  getInspection,
  updateInspectionItem,
  uploadInspectionPhoto,
  removeInspectionPhoto,
  signInspection,
  addInspectionNote,
} from "../../api/inspections";
import { getLease } from "../../api/leases";

const CONDITIONS = [
  { value: "good", label: "Good" },
  { value: "fair", label: "Fair" },
  { value: "poor", label: "Poor" },
  { value: "damaged", label: "Damaged" },
];

export default function ConductInspection() {
  const { leaseId, inspectionId } = useParams();
  const navigate = useNavigate();

  const [inspection, setInspection] = useState(null);
  const [lease, setLease] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingItem, setSavingItem] = useState(null);

  // Signature state
  const sigPadRef = useRef(null);
  const [tenantName, setTenantName] = useState("");
  const [signing, setSigning] = useState(false);

  // Post-signature note state
  const [newNote, setNewNote] = useState("");
  const [addingNote, setAddingNote] = useState(false);

  /* Load inspection + lease */
  const fetchData = async () => {
    try {
      setLoading(true);
      const [insp, lse] = await Promise.all([
        getInspection(inspectionId),
        getLease(leaseId),
      ]);
      setInspection(insp);
      setLease(lse);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load inspection");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [inspectionId, leaseId]);

  const isLocked = inspection?.status !== "draft";
  const isMoveOut = inspection?.inspection_type === "move_out";

  /* Update a single item field */
  const handleItemChange = async (itemId, updates) => {
    setSavingItem(itemId);
    try {
      const updated = await updateInspectionItem(inspectionId, itemId, updates);
      setInspection((prev) => ({
        ...prev,
        items: prev.items.map((i) => (i.id === itemId ? updated : i)),
      }));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to save");
    } finally {
      setSavingItem(null);
    }
  };

  /* Upload a photo */
  const handlePhotoUpload = async (itemId, file) => {
    try {
      const updated = await uploadInspectionPhoto(inspectionId, itemId, file);
      setInspection((prev) => ({
        ...prev,
        items: prev.items.map((i) => (i.id === itemId ? updated : i)),
      }));
    } catch (err) {
      alert(err.response?.data?.detail || "Photo upload failed");
    }
  };

  /* Remove a photo */
  const handlePhotoRemove = async (itemId, url) => {
    if (!confirm("Remove this photo?")) return;
    try {
      const updated = await removeInspectionPhoto(inspectionId, itemId, url);
      setInspection((prev) => ({
        ...prev,
        items: prev.items.map((i) => (i.id === itemId ? updated : i)),
      }));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to remove photo");
    }
  };

  /* Clear signature pad */
  const clearSignature = () => {
    if (sigPadRef.current) sigPadRef.current.clear();
  };

  /* Sign & Lock */
  const handleSign = async () => {
    if (!tenantName.trim()) {
      alert("Please enter the tenant's full name");
      return;
    }
    if (!sigPadRef.current || sigPadRef.current.isEmpty()) {
      alert("Please draw the tenant's signature");
      return;
    }

    const missing = inspection.items.filter((i) => !i.condition);
    if (missing.length > 0) {
      alert(`Please set a condition for all ${missing.length} remaining item(s)`);
      return;
    }

    if (
      !confirm(
        "Sign and lock this inspection? After this, items cannot be edited. Only notes can be added."
      )
    )
      return;

    setSigning(true);
    try {
      const signatureData = sigPadRef.current.toDataURL("image/png");
      const updated = await signInspection(inspectionId, {
        tenant_signed_name: tenantName.trim(),
        tenant_signature_data: signatureData,
      });
      setInspection(updated);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to sign inspection");
    } finally {
      setSigning(false);
    }
  };

  /* Add a post-signature note */
  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    setAddingNote(true);
    try {
      const note = await addInspectionNote(inspectionId, newNote.trim());
      setInspection((prev) => ({
        ...prev,
        notes: [...prev.notes, note],
      }));
      setNewNote("");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to add note");
    } finally {
      setAddingNote(false);
    }
  };

  if (loading) return <p>Loading inspection...</p>;
  if (error) return <div className="error-text">{error}</div>;
  if (!inspection) return <p>Inspection not found</p>;

  return (
    <section className="properties-page">
      {/* Back link */}
      <div className="flex items-center gap-sm mb-sm">
        <Link to={`/owner/leases/${leaseId}`} className="text-sm checklist-back-link">
          ← Back to Lease
        </Link>
      </div>

      {/* Header */}
      <div className="properties-header">
        <div>
          <h2 className="mb-xs">
            {isMoveOut ? "Move-Out Inspection" : "Move-In Inspection"}
          </h2>
          {lease && (
            <p className="text-sm text-muted">
              {lease.tenant_name} — {lease.unit_name}, {lease.property_name}
            </p>
          )}
        </div>
        <span className={`role-badge inspection-status-${inspection.status}`}>
          {inspection.status}
        </span>
      </div>

      {/* Locked banner */}
      {isLocked && (
        <div className="inspection-locked-banner card mt-md">
          <p>
            <strong>This inspection is locked.</strong> Signed by{" "}
            <strong>{inspection.tenant_signed_name}</strong> on{" "}
            {new Date(inspection.tenant_signed_at).toLocaleString()}. Items cannot be
            edited. Use the notes section at the bottom to record any additional
            observations.
          </p>
        </div>
      )}

      {/* Checklist items */}
      <div className="mt-md">
        {inspection.items.map((item, idx) => (
          <InspectionItemCard
            key={item.id}
            item={item}
            index={idx}
            isLocked={isLocked}
            isMoveOut={isMoveOut}
            saving={savingItem === item.id}
            onChange={(updates) => handleItemChange(item.id, updates)}
            onPhotoUpload={(file) => handlePhotoUpload(item.id, file)}
            onPhotoRemove={(url) => handlePhotoRemove(item.id, url)}
          />
        ))}
      </div>

      {/* Move-out deduction total */}
      {isMoveOut && isLocked && (
        <div className="card mt-md inspection-deduction-summary">
          <h3>Deposit Reconciliation</h3>
          <div className="two-col">
            <div>
              <div className="text-sm text-muted">Original Deposit</div>
              <div className="text-bold">
                KES {Number(lease?.deposit_amount || 0).toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted">Total Deductions</div>
              <div className="text-bold">
                KES {Number(inspection.total_deduction_amount).toLocaleString()}
              </div>
            </div>
          </div>
          <div className="inspection-refundable mt-md">
            <div className="text-sm text-muted">Refundable to Tenant</div>
            <div className="text-bold">
              KES{" "}
              {Math.max(
                0,
                (lease?.deposit_amount || 0) - inspection.total_deduction_amount
              ).toLocaleString()}
            </div>
          </div>
        </div>
      )}

      {/* Signature section (only if draft) */}
      {!isLocked && (
        <div className="card mt-md inspection-signature-card">
          <h3>Tenant Signature</h3>
          <p className="text-sm text-muted">
            The tenant must confirm the inspection results by signing below before
            this can be locked.
          </p>

          <div className="form-group">
            <label>Tenant's Full Name (as it should appear on the record)</label>
            <input
              className="input"
              type="text"
              placeholder="Enter the tenant's full name"
              value={tenantName}
              onChange={(e) => setTenantName(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Signature</label>
            <div className="signature-pad-wrapper">
              <SignatureCanvas
                ref={sigPadRef}
                penColor="#1f2937"
                canvasProps={{
                  className: "signature-pad-canvas",
                  width: 500,
                  height: 200,
                }}
              />
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm mt-sm"
              onClick={clearSignature}
            >
              Clear Signature
            </button>
          </div>

          <div className="flex gap-sm mt-md">
            <button
              className="btn btn-primary"
              onClick={handleSign}
              disabled={signing}
            >
              {signing ? "Signing..." : "Sign & Lock Inspection"}
            </button>
            <Link to={`/owner/leases/${leaseId}`} className="btn btn-secondary">
              Save Draft & Exit
            </Link>
          </div>
        </div>
      )}

      {/* Signed signature display */}
      {isLocked && inspection.tenant_signature_data && (
        <div className="card mt-md">
          <h3>Tenant Signature</h3>
          <div className="text-sm text-muted">Signed by</div>
          <div className="text-bold mb-sm">{inspection.tenant_signed_name}</div>
          <img
            src={inspection.tenant_signature_data}
            alt="Tenant signature"
            className="signed-signature-image"
          />
        </div>
      )}

      {/* Notes section */}
      <div className="card mt-md">
        <h3>Notes</h3>

        {inspection.notes.length === 0 ? (
          <p className="text-sm text-muted">No notes yet.</p>
        ) : (
          <div className="inspection-notes-list">
            {inspection.notes.map((note) => (
              <div key={note.id} className="inspection-note-item">
                <div className="text-sm">{note.note}</div>
                <div className="text-sm text-muted">
                  {note.user_email} ·{" "}
                  {new Date(note.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-md">
          <textarea
            className="input"
            rows={3}
            placeholder="Add a note about this inspection..."
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
          />
          <button
            className="btn btn-primary btn-sm mt-sm"
            onClick={handleAddNote}
            disabled={!newNote.trim() || addingNote}
          >
            {addingNote ? "Adding..." : "Add Note"}
          </button>
        </div>
      </div>
    </section>
  );
}


/* ─────────────────────────────────────────────────────────────
   InspectionItemCard — one row per checklist item
   ───────────────────────────────────────────────────────────── */

function InspectionItemCard({
  item,
  index,
  isLocked,
  isMoveOut,
  saving,
  onChange,
  onPhotoUpload,
  onPhotoRemove,
}) {
  const [commentsValue, setCommentsValue] = useState(item.comments || "");
  const [deductionValue, setDeductionValue] = useState(
    item.deduction_amount ? String(item.deduction_amount) : ""
  );

  // Keep local state in sync with prop changes (after server save)
  useEffect(() => {
    setCommentsValue(item.comments || "");
    setDeductionValue(item.deduction_amount ? String(item.deduction_amount) : "");
  }, [item.comments, item.deduction_amount]);

  const handleConditionChange = (condition) => {
    onChange({ condition });
  };

  const handleCommentsBlur = () => {
    if (commentsValue !== (item.comments || "")) {
      onChange({ comments: commentsValue || null });
    }
  };

  const handleDeductionBlur = () => {
    const val = deductionValue ? parseFloat(deductionValue) : 0;
    if (val !== (item.deduction_amount || 0)) {
      onChange({ deduction_amount: val });
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    onPhotoUpload(file);
    e.target.value = "";
  };

  return (
    <div className="card inspection-item-card">
      <div className="inspection-item-header">
        <div className="inspection-item-number">{index + 1}</div>
        <div className="inspection-item-name">{item.item_name}</div>
        {saving && <span className="text-sm text-muted">Saving...</span>}
      </div>

      {/* Condition radio buttons */}
      <div className="inspection-condition-row">
        {CONDITIONS.map((c) => {
          const selected = item.condition === c.value;
          const classes = [
            "inspection-condition-option",
            selected ? "selected" : "",
            selected ? `condition-${c.value}` : "",
            isLocked ? "disabled" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <label key={c.value} className={classes}>
              <input
                type="radio"
                name={`condition-${item.id}`}
                value={c.value}
                checked={selected}
                onChange={() => handleConditionChange(c.value)}
                disabled={isLocked}
              />
              {c.label}
            </label>
          );
        })}
      </div>

      {/* Comments */}
      <div className="form-group mt-sm">
        <label>Comments</label>
        <textarea
          className="input"
          rows={2}
          placeholder="Any specific details about the condition..."
          value={commentsValue}
          onChange={(e) => setCommentsValue(e.target.value)}
          onBlur={handleCommentsBlur}
          disabled={isLocked}
        />
      </div>

      {/* Move-out deduction */}
      {isMoveOut && (
        <div className="form-group">
          <label>Damage Deduction (KES)</label>
          <input
            className="input"
            type="number"
            placeholder="0"
            value={deductionValue}
            onChange={(e) => setDeductionValue(e.target.value)}
            onBlur={handleDeductionBlur}
            disabled={isLocked}
          />
          <p className="text-sm text-muted">
            Amount to deduct from the tenant's security deposit for this item.
          </p>
        </div>
      )}

      {/* Photos */}
      <div className="inspection-photos-section">
        <label className="text-sm">
          Photos ({item.photo_urls.length} / 5)
        </label>
        <div className="inspection-photos-grid">
          {item.photo_urls.map((url) => (
            <div key={url} className="inspection-photo-thumb">
              <a href={url} target="_blank" rel="noopener noreferrer">
                <img src={url} alt="Inspection" />
              </a>
              {!isLocked && (
                <button
                  type="button"
                  className="inspection-photo-remove"
                  onClick={() => onPhotoRemove(url)}
                  title="Remove photo"
                >
                  ×
                </button>
              )}
            </div>
          ))}
          {!isLocked && item.photo_urls.length < 5 && (
            <label className="inspection-photo-add">
              + Add Photo
              <input
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="doc-upload-hidden-input"
              />
            </label>
          )}
        </div>
      </div>
    </div>
  );
}
