//frontend/src/features/profile/Profile.jsx
//
// Profile page (Sprint 4.5 profile menu). Role-agnostic — reachable by every
// role under their own prefix (/owner/profile, /finance/profile, etc.).
// Edit your name + change your password. Email and organization are shown
// read-only (changing those touches uniqueness / other tables; out of scope).
//
// Tenants additionally get a "Documents" tab to upload and manage their own
// identification documents (national ID, passport biodata, other). These use
// the /tenants/me/documents endpoints, which resolve the tenant from the
// logged-in user — a tenant can only ever see their own documents. Owners/PMs
// continue to view tenant documents on the EditTenant page.

import { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { updateProfile, changePassword } from "../../api/auth";
import {
  getMyDocuments,
  uploadMyDocument,
  deleteMyDocument,
} from "../../api/tenants";

const DOC_TYPE_LABELS = {
  national_id_front: "National ID (Front)",
  national_id_back: "National ID (Back)",
  passport_biodata: "Passport (Biodata)",
  other: "Other",
};

export default function Profile() {
  const { user, organization, setUser } = useAuth();

  const isTenant = user?.role?.toLowerCase() === "tenant";

  const [activeTab, setActiveTab] = useState("account");

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [savingName, setSavingName] = useState(false);
  const [nameMsg, setNameMsg] = useState("");
  const [nameErr, setNameErr] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [savingPw, setSavingPw] = useState(false);
  const [pwMsg, setPwMsg] = useState("");
  const [pwErr, setPwErr] = useState("");

  // Documents (tenant self-service)
  const [docs, setDocs] = useState([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [docsErr, setDocsErr] = useState("");
  const [docsMsg, setDocsMsg] = useState("");
  const [docType, setDocType] = useState("national_id_front");
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const loadDocs = async () => {
    setDocsErr("");
    setDocsLoading(true);
    try {
      const data = await getMyDocuments();
      setDocs(data);
    } catch (err) {
      setDocsErr(
        err?.response?.data?.detail || "Could not load your documents."
      );
    } finally {
      setDocsLoading(false);
    }
  };

  useEffect(() => {
    if (isTenant) loadDocs();
  }, [isTenant]);

  if (!user) return null;

  const saveName = async () => {
    setNameErr("");
    setNameMsg("");
    setSavingName(true);
    try {
      const updated = await updateProfile({ full_name: fullName });
      setUser(updated); // reflect the new name in the navbar/greeting at once
      setNameMsg("Profile updated.");
      setTimeout(() => setNameMsg(""), 3000);
    } catch (err) {
      setNameErr(err?.response?.data?.detail || "Could not update profile.");
    } finally {
      setSavingName(false);
    }
  };

  const savePassword = async () => {
    setPwErr("");
    setPwMsg("");
    if (newPassword.length < 8) {
      setPwErr("New password must be at least 8 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwErr("New passwords don't match.");
      return;
    }
    setSavingPw(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwMsg("Password updated.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => setPwMsg(""), 3000);
    } catch (err) {
      setPwErr(err?.response?.data?.detail || "Could not change password.");
    } finally {
      setSavingPw(false);
    }
  };

  const handleDocUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setDocsErr("");
    setDocsMsg("");
    setUploading(true);
    try {
      await uploadMyDocument(docType, file);
      setDocsMsg("Document uploaded.");
      setTimeout(() => setDocsMsg(""), 3000);
      await loadDocs();
    } catch (err) {
      setDocsErr(err?.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDocDelete = async (id) => {
    if (!confirm("Remove this document?")) return;
    setDocsErr("");
    setDocsMsg("");
    setDeletingId(id);
    try {
      await deleteMyDocument(id);
      await loadDocs();
    } catch (err) {
      setDocsErr(err?.response?.data?.detail || "Could not remove document.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">Profile</div>

      {/* Tab strip — tenants only (Account | Documents) */}
      {isTenant && (
        <div className="flex gap-sm mb-md">
          <button
            className={`btn btn-sm ${
              activeTab === "account" ? "btn-primary" : "btn-secondary"
            }`}
            onClick={() => setActiveTab("account")}
          >
            Account
          </button>
          <button
            className={`btn btn-sm ${
              activeTab === "documents" ? "btn-primary" : "btn-secondary"
            }`}
            onClick={() => setActiveTab("documents")}
          >
            Documents
          </button>
        </div>
      )}

      {/* ─── Account tab (default; the only view for non-tenants) ─── */}
      {(!isTenant || activeTab === "account") && (
        <>
          {/* Account details */}
          <div className="dash-panel mb-md">
            <div className="dash-panel-title">Account</div>

            <div className="profile-field">
              <label>Full name</label>
              <input
                className="input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your name"
              />
            </div>

            <div className="profile-field">
              <label>Email</label>
              <input className="input" value={user.email || ""} disabled />
            </div>

            {organization?.name && (
              <div className="profile-field">
                <label>Organization</label>
                <input className="input" value={organization.name} disabled />
              </div>
            )}

            {nameErr && <div className="error-text">{nameErr}</div>}
            {nameMsg && <div className="success-banner">{nameMsg}</div>}

            <button
              className="btn btn-primary btn-sm"
              onClick={saveName}
              disabled={savingName}
            >
              {savingName ? "Saving…" : "Save"}
            </button>
          </div>

          {/* Change password */}
          <div className="dash-panel">
            <div className="dash-panel-title">Change password</div>

            <div className="profile-field">
              <label>Current password</label>
              <input
                className="input"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>

            <div className="profile-field">
              <label>New password</label>
              <input
                className="input"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>

            <div className="profile-field">
              <label>Confirm new password</label>
              <input
                className="input"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>

            {pwErr && <div className="error-text">{pwErr}</div>}
            {pwMsg && <div className="success-banner">{pwMsg}</div>}

            <button
              className="btn btn-primary btn-sm"
              onClick={savePassword}
              disabled={
                savingPw ||
                !currentPassword ||
                !newPassword ||
                !confirmPassword
              }
            >
              {savingPw ? "Saving…" : "Update password"}
            </button>
          </div>
        </>
      )}

      {/* ─── Documents tab (tenants only) ─── */}
      {isTenant && activeTab === "documents" && (
        <div className="dash-panel">
          <div className="dash-panel-title">My Documents</div>
          <p className="text-sm text-muted">
            Upload identification documents for your landlord's records. PDF or
            image files are accepted.
          </p>

          <div className="profile-field">
            <label>Document type</label>
            <select
              className="input"
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              disabled={uploading}
            >
              <option value="national_id_front">National ID (Front)</option>
              <option value="national_id_back">National ID (Back)</option>
              <option value="passport_biodata">Passport (Biodata)</option>
              <option value="other">Other</option>
            </select>
          </div>

          <label className="btn btn-secondary btn-sm doc-upload-label">
            {uploading ? "Uploading…" : "Choose file & upload"}
            <input
              type="file"
              accept="application/pdf,image/*"
              onChange={handleDocUpload}
              disabled={uploading}
              className="doc-upload-hidden-input"
            />
          </label>

          {docsErr && <div className="error-text">{docsErr}</div>}
          {docsMsg && <div className="success-banner">{docsMsg}</div>}

          <div className="mt-md">
            {docsLoading ? (
              <p className="text-sm text-muted">Loading your documents…</p>
            ) : docs.length === 0 ? (
              <div className="empty-state-sm">
                <p className="text-sm">No documents uploaded yet.</p>
                <p className="text-xs text-muted">
                  Choose a document type above, then upload a file.
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-sm">
                {docs.map((d) => (
                  <div key={d.id} className="doc-upload-row">
                    <div className="doc-upload-row-info">
                      <div className="text-bold">
                        {DOC_TYPE_LABELS[d.document_type] || d.document_type}
                      </div>
                      <div className="text-xs text-muted file-name-ellipsis">
                        {d.original_filename || "Document"}
                      </div>
                    </div>

                    <div className="flex gap-sm">
                      <a
                        href={d.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-secondary btn-sm"
                      >
                        View
                      </a>
                      <a
                        href={d.file_url}
                        download
                        className="btn btn-secondary btn-sm"
                      >
                        Download
                      </a>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleDocDelete(d.id)}
                        disabled={deletingId === d.id}
                      >
                        {deletingId === d.id ? "Removing…" : "Remove"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
