//frontend\src\features\tickets\TicketDetail.jsx
//
// Ticket detail (Sprint 6). Shows ticket info, role-aware lifecycle action
// buttons (Pizza Inn stages), an assignee picker (Landlord/PM), the message
// thread (internal notes hidden from tenants), and the attachments panel.
//
// RBAC summary (mirrors backend):
//   Landlord  → all actions including assign/close/reopen/delete
//   PM        → assign, start, wait, resolve, close; can post messages
//   Finance   → can post messages; no status transitions, no assign
//   Tenant    → can post messages (no internal notes); sees their own ticket
//
// Sprint 7 cleanup: internal notes can now target a single staff user via
// a recipient dropdown that appears when the "Internal note" checkbox is
// checked. NULL recipient = broadcast (visible to all staff — the previous
// behaviour). A user id = targeted (visible only to sender + landlord +
// that user). Existing targeted messages render as
// "🔒 Internal note (to john@x.com)" so a landlord reviewing the thread
// can tell what was broadcast and what wasn't.

import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  getTicket,
  assignTicket,
  startTicket,
  waitTicket,
  resolveTicket,
  closeTicket,
  reopenTicket,
  deleteTicket,
  getMessages,
  addMessage,
  deleteMessage,
  getAttachments,
  uploadAttachment,
  deleteAttachment,
} from "../../api/tickets";
import { getMyOrganization } from "../../api/organizations";
import { useAuth } from "../../context/AuthContext";

// ─── Helpers ─────────────────────────────────────────────────────────────

const fmtDate = (d) =>
  d
    ? new Date(d).toLocaleString("en-GB", {
        day: "2-digit", month: "short", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      })
    : "—";

const fmtShort = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-GB", {
        day: "2-digit", month: "short", year: "numeric",
      })
    : "—";

const statusClass = (s) => {
  switch (s) {
    case "closed":      return "status-paid";
    case "resolved":    return "status-ok";
    case "in_progress": return "status-ok";
    default:            return "status-owed";
  }
};

const priorityColor = (p) => {
  switch (p) {
    case "critical": return "#ef4444";
    case "high":     return "#f59e0b";
    case "medium":   return "#2563eb";
    default:         return "#6b7280";
  }
};

function dashboardBase(role) {
  switch (role) {
    case "property_manager": return "/manager";
    case "finance":          return "/finance";
    case "tenant":           return "/tenant";
    default:                 return "/owner";
  }
}

// Roles assignable to a ticket (staff who can do work). Tenants excluded.
// Also the set of users who can receive a targeted internal note.
const ASSIGNABLE_ROLES = ["LANDLORD", "PROPERTY_MANAGER", "FINANCE"];

// ─── Component ───────────────────────────────────────────────────────────

export default function TicketDetail() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const role = user?.role?.toLowerCase();
  const base = dashboardBase(role);

  const isLandlord = role === "landlord";
  const isPM       = role === "property_manager";
  const isFinance  = role === "finance";
  const isTenant   = role === "tenant";
  const canManage  = isLandlord || isPM;  // status transitions
  const canAssign  = isLandlord || isPM;
  const canClose   = isLandlord || isPM;
  const canReopen  = isLandlord;
  const canDelete  = isLandlord;

  const [ticket, setTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Message compose
  const [msgText, setMsgText] = useState("");
  const [isInternal, setIsInternal] = useState(false);
  // Sprint 7 cleanup: null = broadcast to all internal users (default),
  // else a user_id from the staff list = targeted note.
  const [internalRecipient, setInternalRecipient] = useState(null);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  const load = async () => {
    try {
      const [t, m, a] = await Promise.all([
        getTicket(ticketId),
        getMessages(ticketId),
        getAttachments(ticketId),
      ]);
      setTicket(t);
      setMessages(m);
      setAttachments(a);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load ticket");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [ticketId]);

  // Load staff for the assignment picker AND the internal-note recipient
  // dropdown. Previously loaded only for Landlord/PM; Finance also needs it
  // now that they can pick a targeted recipient for their internal notes.
  // Tenants never need this list.
  useEffect(() => {
    if (isTenant) return;
    getMyOrganization()
      .then((org) => {
        const assignable = (org.members || []).filter((m) =>
          ASSIGNABLE_ROLES.includes(m.role)
        );
        setStaff(assignable);
      })
      .catch(() => setStaff([]));
  }, [isTenant]);

  // Scroll to bottom of thread when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ─── Lifecycle actions ─────────────────────────────────────────────

  const runAction = async (fn) => {
    setBusy(true);
    try {
      const updated = await fn();
      setTicket(updated);
    } catch (err) {
      alert(err.response?.data?.detail || "Action failed");
    } finally {
      setBusy(false);
    }
  };

  const handleAssign = async (e) => {
    const assigned_to = e.target.value || null; // "" → unassign
    setBusy(true);
    try {
      const updated = await assignTicket(ticketId, { assigned_to });
      setTicket(updated);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to assign");
    } finally {
      setBusy(false);
    }
  };

  const handleStart    = () => runAction(() => startTicket(ticketId));
  const handleWait     = () => runAction(() => waitTicket(ticketId));
  const handleResolve  = () => {
    const note = prompt("Resolution note (optional):");
    if (note === null) return;
    runAction(() => resolveTicket(ticketId, note || null));
  };
  const handleClose    = () => {
    if (!confirm("Close this ticket?")) return;
    runAction(() => closeTicket(ticketId));
  };
  const handleReopen   = () => {
    if (!confirm("Reopen this ticket?")) return;
    runAction(() => reopenTicket(ticketId));
  };
  const handleDelete   = async () => {
    if (!confirm("Delete this ticket? This cannot be undone.")) return;
    setBusy(true);
    try {
      await deleteTicket(ticketId);
      navigate(`${base}/tickets`);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete ticket");
      setBusy(false);
    }
  };

  // ─── Messages ──────────────────────────────────────────────────────

  const handleToggleInternal = (checked) => {
    setIsInternal(checked);
    // Reset recipient when leaving internal mode — otherwise flipping the
    // checkbox off and back on would silently keep a stale recipient.
    if (!checked) setInternalRecipient(null);
  };

  const handleSendMessage = async () => {
    if (!msgText.trim()) return;
    setSending(true);
    try {
      const payload = {
        message: msgText.trim(),
        is_internal: isInternal,
      };
      // Only send recipient_id on internal notes. Backend also ignores it
      // on public messages, but keeping the payload lean here.
      if (isInternal && internalRecipient) {
        payload.recipient_id = internalRecipient;
      }
      const msg = await addMessage(ticketId, payload);
      setMessages((prev) => [...prev, msg]);
      setMsgText("");
      setInternalRecipient(null);   // reset for next message
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const handleDeleteMessage = async (messageId) => {
    if (!confirm("Delete this message?")) return;
    try {
      await deleteMessage(ticketId, messageId);
      setMessages((prev) => prev.filter((m) => m.id !== messageId));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete message");
    }
  };

  // ─── Attachments ───────────────────────────────────────────────────

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      const att = await uploadAttachment(ticketId, file);
      setAttachments((prev) => [...prev, att]);
    } catch (err) {
      alert(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDeleteAttachment = async (attachmentId) => {
    if (!confirm("Remove this attachment?")) return;
    try {
      await deleteAttachment(ticketId, attachmentId);
      setAttachments((prev) => prev.filter((a) => a.id !== attachmentId));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to remove attachment");
    }
  };

  // ─── Render ────────────────────────────────────────────────────────

  if (loading) return <p>Loading...</p>;
  if (error)   return <div className="error-text">{error}</div>;
  if (!ticket) return <p>Ticket not found</p>;

  const status = ticket.status;
  const isClosed = status === "closed";

  // Recipient options for the internal-note dropdown: any staff in this
  // org EXCEPT the current user (sending an internal note to yourself is
  // never what you want).
  const recipientOptions = staff.filter((s) => s.user_id !== user?.id);

  return (
    <section className="properties-page">
      {/* Back link */}
      <div className="flex items-center gap-sm mb-sm">
        <Link to={`${base}/tickets`} className="text-sm checklist-back-link">
          ← All Tickets
        </Link>
      </div>

      {/* Header — Sprint 7 cleanup: added tenant_name so the top-of-page
          context line shows Property · Unit · Tenant · Category. Backend's
          _enrich() populates these; falls through gracefully when a field
          is missing (e.g. tickets without a tenant, or older data). */}
      <div className="properties-header">
        <div>
          <h2>{ticket.title}</h2>
          <p className="text-muted text-sm">
            {ticket.property_name || "No property"}
            {ticket.unit_name ? ` · ${ticket.unit_name}` : ""}
            {ticket.tenant_name ? ` · ${ticket.tenant_name}` : ""}
            {ticket.category ? ` · ${ticket.category.replace(/_/g, " ")}` : ""}
          </p>
        </div>
        <div className="flex gap-sm items-center">
          <span style={{ color: priorityColor(ticket.priority), fontWeight: 700 }}>
            {ticket.priority}
          </span>
          <span className={`status-pill ${statusClass(status)}`}>
            {status.replace(/_/g, " ")}
          </span>
        </div>
      </div>

      {/* ─── Details ─── */}
      <div className="card detail-card">
        <h3>Details</h3>
        <div className="two-col">
          <div>
            <div className="text-sm text-muted">Opened</div>
            <div className="text-bold">{fmtShort(ticket.opened_at || ticket.created_at)}</div>
          </div>
          <div>
            <div className="text-sm text-muted">Source</div>
            <div className="text-bold">{ticket.source?.replace(/_/g, " ") || "—"}</div>
          </div>
        </div>
        <div className="two-col mt-md">
          <div>
            <div className="text-sm text-muted">Assigned to</div>
            <div className="text-bold">{ticket.assignee_email || "Unassigned"}</div>
          </div>
          <div>
            <div className="text-sm text-muted">Reported by</div>
            <div className="text-bold">{ticket.creator_email || "—"}</div>
          </div>
        </div>
        {ticket.resolved_at && (
          <div className="mt-md">
            <div className="text-sm text-muted">Resolved</div>
            <div className="text-bold">{fmtShort(ticket.resolved_at)}</div>
          </div>
        )}
        <div className="mt-md">
          <div className="text-sm text-muted">Description</div>
          <div style={{ whiteSpace: "pre-wrap" }}>{ticket.description}</div>
        </div>
      </div>

      {/* ─── Actions (Pizza Inn lifecycle) ─── */}
      {!isTenant && (
        <div className="card detail-card">
          <h3>Actions</h3>

          {/* Assignment picker — Landlord/PM only */}
          {canAssign && !isClosed && (
            <div className="form-group" style={{ maxWidth: 360 }}>
              <label htmlFor="assignee">Assign to</label>
              <select
                id="assignee"
                className="input"
                value={ticket.assigned_to || ""}
                onChange={handleAssign}
                disabled={busy}
              >
                <option value="">Unassigned</option>
                {staff.map((s) => (
                  <option key={s.user_id} value={s.user_id}>
                    {s.name} ({s.role.replace(/_/g, " ").toLowerCase()})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex gap-sm flex-wrap mt-sm">
            {/* start: assigned → in_progress */}
            {canManage && status === "assigned" && (
              <button className="btn btn-primary" onClick={handleStart} disabled={busy}>
                Start Work
              </button>
            )}
            {/* wait: in_progress → waiting */}
            {canManage && status === "in_progress" && (
              <button className="btn btn-secondary" onClick={handleWait} disabled={busy}>
                Mark as Waiting
              </button>
            )}
            {/* resolve: any open status */}
            {canManage && ["open","assigned","in_progress","waiting"].includes(status) && (
              <button className="btn btn-primary" onClick={handleResolve} disabled={busy}>
                Mark Resolved
              </button>
            )}
            {/* close: resolved only */}
            {canClose && status === "resolved" && (
              <button className="btn btn-primary" onClick={handleClose} disabled={busy}>
                Close Ticket
              </button>
            )}
            {/* reopen: resolved or closed */}
            {canReopen && ["resolved","closed"].includes(status) && (
              <button className="btn btn-secondary" onClick={handleReopen} disabled={busy}>
                Reopen
              </button>
            )}
            {/* delete: landlord only, any non-closed status */}
            {canDelete && !isClosed && (
              <button className="btn btn-danger" onClick={handleDelete} disabled={busy}>
                Delete
              </button>
            )}
          </div>

          {status === "open" && canAssign && (
            <p className="text-sm text-muted mt-sm">
              Assign this ticket to a staff member to begin the workflow, or mark it resolved directly.
            </p>
          )}
          {isClosed && (
            <p className="text-sm text-muted mt-sm">
              This ticket is closed. {canReopen ? "Reopen it if the issue has recurred." : ""}
            </p>
          )}
          {isFinance && (
            <p className="text-sm text-muted">
              Finance can respond to this ticket but cannot change its status or assignment.
            </p>
          )}
        </div>
      )}

      {/* ─── Conversation ─── */}
      <div className="card detail-card">
        <h3>Conversation</h3>

        {/* Thread */}
        <div
          style={{
            maxHeight: 400,
            overflowY: "auto",
            marginBottom: 16,
            display: "flex",
            flexDirection: "column",
            gap: 8,
          }}
        >
          {messages.length === 0 ? (
            <p className="text-sm text-muted">No messages yet. Start the conversation below.</p>
          ) : (
            messages.map((m) => {
              const isOwn = m.sender_id === user?.id;
              return (
                <div
                  key={m.id}
                  style={{
                    alignSelf: isOwn ? "flex-end" : "flex-start",
                    maxWidth: "78%",
                    background: m.is_internal
                      ? "#fef9c3"
                      : isOwn ? "#2563eb" : "#f1f5f9",
                    color: isOwn && !m.is_internal ? "#fff" : "#1e293b",
                    borderRadius: 12,
                    padding: "8px 12px",
                    position: "relative",
                  }}
                >
                  {m.is_internal && (
                    <div className="text-xs" style={{ color: "#92400e", marginBottom: 2 }}>
                      🔒 Internal note
                      {m.recipient_email ? ` (to ${m.recipient_email})` : ""}
                    </div>
                  )}
                  <div className="text-sm" style={{ whiteSpace: "pre-wrap" }}>
                    {m.message}
                  </div>
                  <div
                    className="text-xs"
                    style={{ opacity: 0.65, marginTop: 4 }}
                  >
                    {m.sender_email || "System"} · {fmtDate(m.created_at)}
                  </div>
                  {(isOwn || isLandlord) && (
                    <button
                      onClick={() => handleDeleteMessage(m.id)}
                      style={{
                        position: "absolute",
                        top: 4, right: 6,
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        fontSize: 10,
                        opacity: 0.4,
                      }}
                      title="Delete message"
                    >
                      ✕
                    </button>
                  )}
                </div>
              );
            })
          )}
          <div ref={bottomRef} />
        </div>

        {/* Compose */}
        {!isClosed && (
          <div className="flex flex-col gap-sm">
            <textarea
              className="input"
              rows={3}
              placeholder="Type a message…"
              value={msgText}
              onChange={(e) => setMsgText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleSendMessage();
              }}
            />

            {/* Sprint 7 cleanup: when the internal checkbox is checked, show
                a recipient dropdown right below it — defaults to "All
                internal users" (broadcast); pick a name to target it at
                one person. */}
            {isInternal && !isTenant && recipientOptions.length > 0 && (
              <div className="flex items-center gap-sm">
                <label htmlFor="internal-recipient" className="text-sm">
                  Send to:
                </label>
                <select
                  id="internal-recipient"
                  className="input"
                  value={internalRecipient || ""}
                  onChange={(e) => setInternalRecipient(e.target.value || null)}
                  style={{ maxWidth: 320 }}
                >
                  <option value="">All internal users</option>
                  {recipientOptions.map((s) => (
                    <option key={s.user_id} value={s.user_id}>
                      {s.name} ({s.role.replace(/_/g, " ").toLowerCase()})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-sm">
                {!isTenant && (
                  <label className="flex items-center gap-sm text-sm" style={{ cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={isInternal}
                      onChange={(e) => handleToggleInternal(e.target.checked)}
                    />
                    Internal note (hidden from tenant)
                  </label>
                )}
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleSendMessage}
                disabled={sending || !msgText.trim()}
              >
                {sending ? "Sending…" : "Send"}
              </button>
            </div>
            <p className="text-xs text-muted">Ctrl+Enter to send</p>
          </div>
        )}
        {isClosed && (
          <p className="text-sm text-muted">This ticket is closed — conversation is locked.</p>
        )}
      </div>

      {/* ─── Attachments ─── */}
      <div className="card detail-card">
        <div className="flex items-center justify-between mb-sm">
          <h3>Attachments</h3>
          {!isClosed && (
            <label className="btn btn-secondary btn-sm doc-upload-label">
              {uploading ? "Uploading…" : "Add File"}
              <input
                type="file"
                accept="image/*,application/pdf,.doc,.docx,.xls,.xlsx"
                onChange={handleUpload}
                disabled={uploading}
                className="doc-upload-hidden-input"
              />
            </label>
          )}
        </div>

        {attachments.length === 0 ? (
          <div className="empty-state-sm">
            <p className="text-sm">No files attached yet.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-sm">
            {attachments.map((a) => (
              <div key={a.id} className="doc-upload-row">
                <div className="doc-upload-row-info">
                  <div className="text-sm text-bold file-name-ellipsis">
                    {a.file_name || "Attachment"}
                  </div>
                  <div className="text-xs text-muted">{fmtShort(a.created_at)}</div>
                </div>
                <div className="flex gap-sm">
                  <a
                    href={a.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-secondary btn-sm"
                  >
                    View
                  </a>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDeleteAttachment(a.id)}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
