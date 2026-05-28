/*frontend\src\features\team\team.jsx*/

import { useEffect, useState } from "react";
import {
  getMyOrganization,
  inviteUser,
  getInvitations,
} from "../../api/organizations";
// import "./Team.css";

const INVITABLE_ROLES = ["PROPERTY_MANAGER", "FINANCE", "TENANT"];

export default function Team() {
  const [org, setOrg] = useState(null);
  const [members, setMembers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [myRole, setMyRole] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Invite form
  const [inviteEmail, setInviteEmail] = useState("");
  const [invitePhone, setInvitePhone] = useState("");
  const [inviteRole, setInviteRole] = useState("PROPERTY_MANAGER");
  const [inviting, setInviting] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [orgData, invData] = await Promise.all([
        getMyOrganization(),
        getInvitations(),
      ]);

      setOrg(orgData.organization);
      setMembers(orgData.members);
      setMyRole(orgData.my_role);
      setInvitations(invData);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load organization");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleInvite = async (e) => {
    e.preventDefault();
    setError("");
    setInviting(true);

    try {
      const data = await inviteUser(inviteEmail, invitePhone, inviteRole);
      setSuccess(data.message);
      setInviteEmail("");
      setInvitePhone("");
      await fetchData();
      setTimeout(() => setSuccess(""), 4000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send invitation");
    } finally {
      setInviting(false);
    }
  };

  if (loading) return <p>Loading team...</p>;

  return (
    <section className="team-page">
      <h2>{org?.name} — Team</h2>

      {success && <div className="success-banner">{success}</div>}
      {error && <div className="error-text">{error}</div>}

      {/* ─── Invite Form (Landlords only) ─── */}
      {myRole === "LANDLORD" && (
        <div className="card invite-section">
          <h3>Invite Team Member</h3>
          <div className="invite-form">
            <input
              className="input"
              type="phone"
              placeholder="WhatsApp phone number"
              value={invitePhone}
              onChange={(e) => setInvitePhone(e.target.value)}
              required
            />
            <input
              className="input"
              type="email"
              placeholder="Email address"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              required
            />
            <select
              className="input"
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
            >
              {INVITABLE_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r.replace("_", " ")}
                </option>
              ))}
            </select>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleInvite}
              disabled={inviting || !inviteEmail}
            >
              {inviting ? "Sending..." : "Send Invite"}
            </button>
          </div>
        </div>
      )}

      {/* ─── Members ─── */}
      <div className="card">
        <h3>Members</h3>

        {/* Desktop */}
        <div className="hidden-mobile">
          <table className="team-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              {members.map((m) => (
                <tr key={m.user_id}>
                  <td>{m.email}</td>
                  <td>
                    <span className={`role-badge role-${m.role.toLowerCase()}`}>
                      {m.role.replace("_", " ")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Mobile */}
        <div className="hidden-desktop team-cards">
          {members.map((m) => (
            <div key={m.user_id} className="team-card">
              <strong>{m.email}</strong>
              <span className={`role-badge role-${m.role.toLowerCase()}`}>
                {m.role.replace("_", " ")}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ─── Pending Invitations ─── */}
      {invitations.filter((i) => i.status === "pending").length > 0 && (
        <div className="card">
          <h3>Pending Invitations</h3>
          <div className="invitations-list">
            {invitations
              .filter((i) => i.status === "pending")
              .map((inv) => (
                <div key={inv.id} className="invitation-row">
                  <span>{inv.email}</span>
                  <span className={`role-badge role-${inv.role.toLowerCase()}`}>
                    {inv.role.replace("_", " ")}
                  </span>
                  <span className="badge-pending">Pending</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </section>
  );
}
