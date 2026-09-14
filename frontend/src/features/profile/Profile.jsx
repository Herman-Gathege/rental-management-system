//frontend/src/features/profile/Profile.jsx
//
// Profile page. Role-agnostic — reachable by every role under their own prefix
// (/owner/profile, /finance/profile, etc.).
//
// Editable (requirement 8): full name, phone number and email address.
//   * phone is validated and normalised server-side, must be unique, and flips
//     back to unverified when it changes
//   * email is the login identity, so it additionally requires the current
//     password
//   * role, organisation and permissions are not editable here and the API
//     ignores any attempt to send them
//
// Password changes stay a separate workflow below, as before.
//
// Tenants additionally get a "Documents" tab to upload and manage their own
// identification documents (national ID, passport biodata, other). These use
// the /tenants/me/documents endpoints, which resolve the tenant from the
// logged-in user — a tenant can only ever see their own documents. Owners/PMs
// continue to view tenant documents on the EditTenant page.

import { useState, useEffect, useMemo } from "react";
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
  const [email, setEmail] = useState(user?.email || "");
  const [phone, setPhone] = useState(user?.phone || "");
  const [emailPassword, setEmailPassword] = useState("");
  const [savingName, setSavingName] = useState(false);
  const [nameMsg, setNameMsg] = useState("");
  const [nameErr, setNameErr] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

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

  // Warn before leaving with unsaved profile edits. Declared with the other
  // hooks (before any early return) so hook order never changes between
  // renders.
  const dirty = useMemo(() => {
    const nameChanged = (fullName || "") !== (user?.full_name || "");
    const phoneChanged = (phone || "") !== (user?.phone || "");
    const emailChanged =
      (email || "").trim().toLowerCase() !== (user?.email || "").toLowerCase();
    return nameChanged || phoneChanged || emailChanged;
  }, [fullName, phone, email, user]);

  useEffect(() => {
    const onBeforeUnload = (event) => {
      if (!dirty) return undefined;
      event.preventDefault();
      event.returnValue = "";
      return "";
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [dirty]);

  if (!user) return null;

  const saveName = async () => {
    setNameErr("");
    setNameMsg("");
    setFieldErrors({});

    // Inline validation mirrors the server rules so the user gets feedback
    // before a round trip; the server still enforces all of it.
    const errors = {};
    if (phone) {
      const digits = phone.replace(/[^\d]/g, "");
      const normalised =
        digits.startsWith("0") && digits.length === 10
          ? `254${digits.slice(1)}`
          : digits;
      if (!/^254\d{9}$/.test(normalised)) {
        errors.phone = "Enter a valid phone number, e.g. 0712 345 678.";
      }
    }
    const emailChanged = (email || "").trim().toLowerCase() !== (user.email || "").toLowerCase();
    if (emailChanged) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((email || "").trim())) {
        errors.email = "Enter a valid email address.";
      } else if (!emailPassword) {
        errors.emailPassword =
          "Confirm your current password to change your email address.";
      }
    }
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setSavingName(true);
    try {
      const payload = { full_name: fullName, phone: phone || null };
      if (emailChanged) {
        payload.email = email.trim();
        payload.current_password = emailPassword;
      }
      const updated = await updateProfile(payload);
      setUser(updated); // reflect the new name in the navbar/greeting at once
      setEmail(updated.email || "");
      setPhone(updated.phone || "");
      setEmailPassword("");
      setNameMsg(
        emailChanged
          ? "Profile updated. Use your new email address next time you sign in."
          : "Profile updated.",
      );
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
                aria-invalid={Boolean(fieldErrors.full_name)}
              />
            </div>

            <div className="profile-field">
              <label htmlFor="profile-email">Email address</label>
              <input
                id="profile-email"
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                aria-invalid={Boolean(fieldErrors.email)}
              />
              {fieldErrors.email && (
                <span className="field-error">{fieldErrors.email}</span>
              )}
              <small className="text-muted">
                This is the address you sign in with. Changing it requires your
                current password.
              </small>
            </div>

            <div className="profile-field">
              <label htmlFor="profile-phone">Phone number</label>
              <input
                id="profile-phone"
                className="input"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="0712 345 678"
                aria-invalid={Boolean(fieldErrors.phone)}
              />
              {fieldErrors.phone && (
                <span className="field-error">{fieldErrors.phone}</span>
              )}
              {user.phone && (
                <small className="text-muted">
                  {user.phone_verified
                    ? "Verified"
                    : "Not yet verified — you may be asked to confirm this number."}
                </small>
              )}
            </div>

            {(email || "").trim().toLowerCase() !== (user.email || "").toLowerCase() && (
              <div className="profile-field">
                <label htmlFor="profile-email-password">Current password</label>
                <input
                  id="profile-email-password"
                  className="input"
                  type="password"
                  value={emailPassword}
                  onChange={(e) => setEmailPassword(e.target.value)}
                  autoComplete="current-password"
                  aria-invalid={Boolean(fieldErrors.emailPassword)}
                />
                {fieldErrors.emailPassword && (
                  <span className="field-error">{fieldErrors.emailPassword}</span>
                )}
                <small className="text-muted">
                  Required because your email address is your login.
                </small>
              </div>
            )}

            <div className="profile-field">
              <label>Role</label>
              <input
                className="input"
                value={user.role || ""}
                disabled
                aria-describedby="profile-role-help"
              />
              <small className="text-muted" id="profile-role-help">
                Managed by your organisation administrator.
              </small>
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
              disabled={savingName || !dirty}
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
