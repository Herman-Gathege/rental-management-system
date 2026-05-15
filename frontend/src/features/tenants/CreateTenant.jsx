//frontend\src\features\tenants\CreateTenant.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createTenant, uploadTenantDocument } from "../../api/tenants";
import CollapsibleSection from "../../components/CollapsibleSection";

export default function CreateTenant() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    // Personal
    full_name: "",
    email: "",
    phone: "",
    alternative_phone: "",
    id_number: "",
    emergency_contact: "",

    // Next of kin
    next_of_kin_name: "",
    next_of_kin_relationship: "",
    next_of_kin_phone: "",
    next_of_kin_alt_phone: "",
    next_of_kin_email: "",

    // Employer
    employer_name: "",
    employer_location: "",
    employer_phone: "",
    employer_email: "",
  });

  // Pending uploads (file + type) — uploaded after tenant is created
  const [pendingDocs, setPendingDocs] = useState([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  /* Add a file to the pending upload list */
  const handleFileSelect = (e, documentType) => {
    const file = e.target.files[0];
    if (!file) return;

    setPendingDocs((prev) => [
      ...prev.filter((d) => d.documentType !== documentType),
      { documentType, file, filename: file.name },
    ]);
  };

  const removePendingDoc = (documentType) => {
    setPendingDocs((prev) => prev.filter((d) => d.documentType !== documentType));
  };

  const handleSubmit = async () => {
    setError("");
    setSubmitting(true);

    try {
      // Build payload — clean empty strings to null
      const payload = {};
      Object.entries(form).forEach(([key, value]) => {
        payload[key] = value || null;
      });
      // full_name and phone are required — don't null them
      payload.full_name = form.full_name;
      payload.phone = form.phone;

      // Step 1: create the tenant
      const tenant = await createTenant(payload);

      // Step 2: upload any pending documents
      for (const doc of pendingDocs) {
        try {
          await uploadTenantDocument(tenant.id, doc.documentType, doc.file);
        } catch (err) {
          console.error(`Failed to upload ${doc.documentType}:`, err);
        }
      }

      navigate("/owner/tenants");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create tenant");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="properties-page">
      <h2>Add New Tenant</h2>

      {error && <div className="error-text">{error}</div>}

      <div className="property-form card">
        {/* ─── Personal Information (always open) ─── */}
        <div className="form-group">
          <label>Full Name *</label>
          <input
            className="input"
            name="full_name"
            value={form.full_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="two-col">
          <div className="form-group">
            <label>Primary Phone *</label>
            <input
              className="input"
              name="phone"
              value={form.phone}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label>Alternative Phone</label>
            <input
              className="input"
              name="alternative_phone"
              value={form.alternative_phone}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="two-col">
          <div className="form-group">
            <label>Email</label>
            <input
              className="input"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label>National ID / Passport No.</label>
            <input
              className="input"
              name="id_number"
              value={form.id_number}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* ─── Identification Documents ─── */}
        <CollapsibleSection
          title="Identification Documents"
          summary={pendingDocs.length > 0 ? `${pendingDocs.length} file(s) ready` : null}
        >
          <p className="text-sm doc-upload-hint">
            Upload clear copies of National ID (both sides) or Passport biodata page.
            Documents upload after the tenant is created.
          </p>

          <DocumentUploadRow
            label="National ID — Front"
            documentType="national_id_front"
            pendingDocs={pendingDocs}
            onSelect={handleFileSelect}
            onRemove={removePendingDoc}
          />
          <DocumentUploadRow
            label="National ID — Back"
            documentType="national_id_back"
            pendingDocs={pendingDocs}
            onSelect={handleFileSelect}
            onRemove={removePendingDoc}
          />
          <DocumentUploadRow
            label="Passport (Biodata page)"
            documentType="passport_biodata"
            pendingDocs={pendingDocs}
            onSelect={handleFileSelect}
            onRemove={removePendingDoc}
          />
        </CollapsibleSection>

        {/* ─── Next of Kin ─── */}
        <CollapsibleSection
          title="Next of Kin / Emergency Contact"
          summary={form.next_of_kin_name || null}
        >
          <div className="two-col">
            <div className="form-group">
              <label>Full Name</label>
              <input
                className="input"
                name="next_of_kin_name"
                value={form.next_of_kin_name}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>Relationship</label>
              <input
                className="input"
                name="next_of_kin_relationship"
                value={form.next_of_kin_relationship}
                onChange={handleChange}
                placeholder="e.g. Spouse, Sibling, Parent"
              />
            </div>
          </div>

          <div className="two-col">
            <div className="form-group">
              <label>Mobile Number</label>
              <input
                className="input"
                name="next_of_kin_phone"
                value={form.next_of_kin_phone}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>Alternative Number</label>
              <input
                className="input"
                name="next_of_kin_alt_phone"
                value={form.next_of_kin_alt_phone}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Email</label>
            <input
              className="input"
              name="next_of_kin_email"
              type="email"
              value={form.next_of_kin_email}
              onChange={handleChange}
            />
          </div>
        </CollapsibleSection>

        {/* ─── Employer / Business ─── */}
        <CollapsibleSection
          title="Employer / Business"
          summary={form.employer_name || null}
        >
          <div className="form-group">
            <label>Name</label>
            <input
              className="input"
              name="employer_name"
              value={form.employer_name}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>Location</label>
            <input
              className="input"
              name="employer_location"
              value={form.employer_location}
              onChange={handleChange}
            />
          </div>

          <div className="two-col">
            <div className="form-group">
              <label>Work Phone</label>
              <input
                className="input"
                name="employer_phone"
                value={form.employer_phone}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>Work Email</label>
              <input
                className="input"
                name="employer_email"
                type="email"
                value={form.employer_email}
                onChange={handleChange}
              />
            </div>
          </div>
        </CollapsibleSection>

        {/* ─── Submit ─── */}
        <div className="flex gap-sm mt-md">
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={submitting || !form.full_name || !form.phone}
          >
            {submitting ? "Creating..." : "Create Tenant"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => navigate("/owner/tenants")}
            type="button"
          >
            Cancel
          </button>
        </div>
      </div>
    </section>
  );
}


/* ─── Helper component: a single document upload row ─── */
function DocumentUploadRow({ label, documentType, pendingDocs, onSelect, onRemove }) {
  const pending = pendingDocs.find((d) => d.documentType === documentType);

  return (
    <div className="doc-upload-row">
      <div className="doc-upload-row-info">
        <div className="text-sm text-bold">{label}</div>
        {pending && <div className="text-sm text-muted">{pending.filename}</div>}
      </div>

      <div className="flex gap-sm">
        {pending ? (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => onRemove(documentType)}
          >
            Remove
          </button>
        ) : (
          <label className="btn btn-secondary btn-sm doc-upload-label">
            Choose file
            <input
              type="file"
              accept="image/*,application/pdf"
              onChange={(e) => onSelect(e, documentType)}
              className="doc-upload-hidden-input"
            />
          </label>
        )}
      </div>
    </div>
  );
}
