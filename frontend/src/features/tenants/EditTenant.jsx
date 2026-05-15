//frontend\src\features\tenants\EditTenant.jsx
import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  getTenant,
  updateTenant,
  uploadTenantDocument,
  getTenantDocuments,
  deleteTenantDocument,
} from "../../api/tenants";
import CollapsibleSection from "../../components/CollapsibleSection";

export default function EditTenant() {
  const { tenantId } = useParams();
  const navigate = useNavigate();

  const [form, setForm] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [uploadingType, setUploadingType] = useState(null);

  /* Load tenant data + documents */
  useEffect(() => {
    const fetchData = async () => {
      try {
        const tenant = await getTenant(tenantId);
        setForm({
          full_name: tenant.full_name || "",
          email: tenant.email || "",
          phone: tenant.phone || "",
          alternative_phone: tenant.alternative_phone || "",
          id_number: tenant.id_number || "",
          emergency_contact: tenant.emergency_contact || "",

          next_of_kin_name: tenant.next_of_kin_name || "",
          next_of_kin_relationship: tenant.next_of_kin_relationship || "",
          next_of_kin_phone: tenant.next_of_kin_phone || "",
          next_of_kin_alt_phone: tenant.next_of_kin_alt_phone || "",
          next_of_kin_email: tenant.next_of_kin_email || "",

          employer_name: tenant.employer_name || "",
          employer_location: tenant.employer_location || "",
          employer_phone: tenant.employer_phone || "",
          employer_email: tenant.employer_email || "",
        });

        const docs = await getTenantDocuments(tenantId);
        setDocuments(docs);
      } catch (err) {
        setError("Failed to load tenant");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [tenantId]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  /* Upload a document immediately on edit page */
  const handleFileUpload = async (e, documentType) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadingType(documentType);
    try {
      const newDoc = await uploadTenantDocument(tenantId, documentType, file);
      setDocuments((prev) => [newDoc, ...prev]);
    } catch (err) {
      alert(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploadingType(null);
      // Reset the file input so the same file can be re-selected if needed
      e.target.value = "";
    }
  };

  /* Delete a document */
  const handleDeleteDocument = async (documentId) => {
    if (!confirm("Delete this document?")) return;
    try {
      await deleteTenantDocument(tenantId, documentId);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete document");
    }
  };

  /* Save tenant details */
  const handleSubmit = async () => {
    setError("");
    setSubmitting(true);
    try {
      // Convert empty strings to null
      const payload = {};
      Object.entries(form).forEach(([key, value]) => {
        payload[key] = value || null;
      });
      payload.full_name = form.full_name;
      payload.phone = form.phone;

      await updateTenant(tenantId, payload);
      navigate("/owner/tenants");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update tenant");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <p>Loading...</p>;
  if (!form) return <p>Tenant not found</p>;

  return (
    <section className="properties-page">
      <h2>Edit Tenant</h2>

      {error && <div className="error-text">{error}</div>}

      <div className="property-form card">
        {/* ─── Personal Information ─── */}
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

        {/* ─── Identification Documents (live management) ─── */}
        <CollapsibleSection
          title="Identification Documents"
          summary={documents.length > 0 ? `${documents.length} on file` : null}
          defaultOpen={true}
        >
          <p className="text-sm text-muted" style={{ marginBottom: 12 }}>
            Upload or remove ID documents. Changes happen immediately.
          </p>

          {/* Existing documents list */}
          {documents.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "8px 0",
                    borderBottom: "1px solid #f3f4f6",
                  }}
                >
                  <div>
                    <div className="text-sm text-bold">
                      {formatDocType(doc.document_type)}
                    </div>
                    <div className="text-sm text-muted">{doc.original_filename}</div>
                  </div>
                  <div className="flex gap-sm">
                    <a
                      href={doc.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary btn-sm"
                    >
                      View
                    </a>
                    <button
                      type="button"
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDeleteDocument(doc.id)}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Upload buttons */}
          <UploadRow
            label="National ID — Front"
            documentType="national_id_front"
            onUpload={handleFileUpload}
            uploadingType={uploadingType}
          />
          <UploadRow
            label="National ID — Back"
            documentType="national_id_back"
            onUpload={handleFileUpload}
            uploadingType={uploadingType}
          />
          <UploadRow
            label="Passport (Biodata page)"
            documentType="passport_biodata"
            onUpload={handleFileUpload}
            uploadingType={uploadingType}
          />
        </CollapsibleSection>

        {/* ─── Next of Kin ─── */}
        <CollapsibleSection
          title="Next of Kin / Emergency Contact"
          summary={form.next_of_kin_name || null}
          defaultOpen={!!form.next_of_kin_name}
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

        {/* ─── Employer ─── */}
        <CollapsibleSection
          title="Employer / Business"
          summary={form.employer_name || null}
          defaultOpen={!!form.employer_name}
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

        {/* ─── Save buttons ─── */}
        <div className="flex gap-sm mt-md">
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "Saving..." : "Save Changes"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => navigate("/owner/tenants")}
          >
            Cancel
          </button>
        </div>
      </div>
    </section>
  );
}


/* ─── Helpers ─── */

function formatDocType(type) {
  const map = {
    national_id_front: "National ID — Front",
    national_id_back: "National ID — Back",
    passport_biodata: "Passport Biodata",
    other: "Other Document",
  };
  return map[type] || type;
}


function UploadRow({ label, documentType, onUpload, uploadingType }) {
  const isUploading = uploadingType === documentType;

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "8px 0",
      }}
    >
      <div className="text-sm">{label}</div>
      <label className="btn btn-secondary btn-sm" style={{ marginBottom: 0 }}>
        {isUploading ? "Uploading..." : "Upload"}
        <input
          type="file"
          accept="image/*,application/pdf"
          onChange={(e) => onUpload(e, documentType)}
          disabled={isUploading}
          style={{ display: "none" }}
        />
      </label>
    </div>
  );
}
