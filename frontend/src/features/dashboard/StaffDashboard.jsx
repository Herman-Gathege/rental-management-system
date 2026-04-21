// frontend/src/features/dashboard/StaffDashboard.jsx
import { Outlet } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import StaffLayout from "./layout/StaffLayout";
import { updateStaffPassword } from "../../api/staff";



// -----------------------------
// Nested Components for Staff
// -----------------------------

export function StaffSales() {
  const { user } = useAuth();
  return (
    <>
      <header className="mb-md">
        <h2 className="text-lg text-bold">Welcome, <span>{user.full_name}</span> 👋</h2>
        {/* <p>Organization: {organization?.name}</p>
        <p>Role: Staff</p> */}
      </header>

      <section className="card">
        <h3 className="text-md text-bold mb-sm">Sales</h3>
        <p className="text-muted">Sales functionality will appear here.</p>
      </section>
    </>
  );
}

export function StaffProfile() {
  const { user } = useAuth();
  return (
    <section className="card flex flex-col gap-sm">
      <h3 className="text-md text-bold">My Profile</h3>

      <div className="flex justify-between">
        <strong>Name:</strong>
        <span>{user.full_name}</span>
      </div>

      <div className="flex justify-between">
        <strong>Email:</strong>
        <span>{user.email}</span>
      </div>
    </section>
  );
}

export function StaffPassword() {
  const { user } = useAuth();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState(""); // new state
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // const API_BASE = import.meta.env.VITE_API_URL;

  const handlePasswordChange = async (e) => {
  e.preventDefault();
  setMessage("");

  if (newPassword !== confirmPassword) {
    setMessage("Passwords do not match");
    return;
  }

  setLoading(true);

  try {
    await updateStaffPassword(user.id, newPassword);

    setMessage("Password updated successfully");
    setNewPassword("");
    setConfirmPassword("");
  } catch (err) {
    setMessage(err.message);
  } finally {
    setLoading(false);
  }
};


  return (
    <section className="card">
      <h3 className="text-md text-bold mb-md">Change Password</h3>

      <form
        onSubmit={handlePasswordChange}
        className="flex flex-col gap-md"
      >
        <input
          className="input"
          type="password"
          placeholder="New password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
        />

        <input
          className="input"
          type="password"
          placeholder="Confirm password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? "Updating..." : "Update Password"}
        </button>

        {message && (
          <p
            className={`text-sm ${
              message.includes("success")
                ? "text-success"
                : "text-error"
            }`}
          >
            {message}
          </p>
        )}
      </form>
    </section>
  );
}


// -----------------------------
// StaffDashboard Layout
// -----------------------------
// StaffDashboard layout

export default function StaffDashboard() {
  return (
    <StaffLayout>
      <Outlet />
    </StaffLayout>
  );
}
