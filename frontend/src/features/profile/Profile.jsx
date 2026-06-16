//frontend/src/features/profile/Profile.jsx
//
// Profile page (Sprint 4.5 profile menu). Role-agnostic — reachable by every
// role under their own prefix (/owner/profile, /finance/profile, etc.).
// Edit your name + change your password. Email and organization are shown
// read-only (changing those touches uniqueness / other tables; out of scope).

import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { updateProfile, changePassword } from "../../api/auth";

export default function Profile() {
  const { user, organization, setUser } = useAuth();

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

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">Profile</div>

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
            savingPw || !currentPassword || !newPassword || !confirmPassword
          }
        >
          {savingPw ? "Saving…" : "Update password"}
        </button>
      </div>
    </div>
  );
}
