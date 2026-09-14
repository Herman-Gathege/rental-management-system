// frontend/src/features/settings/CommunicationSettings.jsx
//
// Communication channel settings (requirement 7).
//
// WhatsApp stays the primary channel; SMTP email can be switched on as a
// fallback, as a second channel, or as the only channel. Credentials are never
// entered (or displayed) here — they live only in the deployment environment.
// This page shows each channel's live health so an admin can see at a glance
// whether email is enabled, disabled, not configured, or misconfigured.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getCommunicationSettings,
  updateCommunicationSettings,
} from "../../api/settings";
import { ErrorState, LoadingState } from "../../components/ui/States";

const STATE_LABELS = {
  enabled: "Enabled",
  disabled: "Disabled",
  not_configured: "Not configured",
  invalid: "Configuration problem",
};

const STATE_CLASS = {
  enabled: "status-ok",
  disabled: "status-paid",
  not_configured: "status-partial",
  invalid: "status-owed",
};

function ChannelCard({ name, title, channel }) {
  const state = channel?.state || "not_configured";
  return (
    <div className="card">
      <div className="flex justify-between items-center">
        <strong>{title}</strong>
        <span className={`status-pill ${STATE_CLASS[state] || "status-paid"}`}>
          {STATE_LABELS[state] || state}
        </span>
      </div>

      <ul className="text-sm text-muted mt-sm" style={{ paddingLeft: 18 }}>
        <li>Switch: {channel?.enabled ? "on" : "off"}</li>
        {name === "email" ? (
          <>
            <li>Server: {channel?.host || "—"}</li>
            <li>From: {channel?.from_email || "—"}</li>
            <li>Credentials: {channel?.has_credentials ? "present" : "not set"}</li>
          </>
        ) : (
          <li>Environment: {channel?.environment || "—"}</li>
        )}
      </ul>

      {channel?.errors?.length > 0 && (
        <div className="text-sm mt-sm" style={{ color: "#b45309" }}>
          {channel.errors.map((message) => (
            <div key={message}>{message}</div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function CommunicationSettings() {
  const [settings, setSettings] = useState(null);
  const [channels, setChannels] = useState(null);
  const [modes, setModes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [success, setSuccess] = useState("");

  const load = async () => {
    setError("");
    setLoading(true);
    try {
      const data = await getCommunicationSettings();
      setSettings(data.settings);
      setChannels(data.channels);
      setModes(data.modes || []);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Could not load communication settings.",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const update = (patch) => setSettings((prev) => ({ ...prev, ...patch }));

  const save = async (event) => {
    event.preventDefault();
    setSaving(true);
    setFormError("");
    setSuccess("");
    try {
      const data = await updateCommunicationSettings({
        channel_mode: settings.channel_mode,
        whatsapp_enabled: settings.whatsapp_enabled,
        email_enabled: settings.email_enabled,
        email_payment_receipts: settings.email_payment_receipts,
      });
      setSettings(data.settings);
      setChannels(data.channels);
      setSuccess("Communication settings saved.");
      setTimeout(() => setSuccess(""), 4000);
    } catch (err) {
      setFormError(
        err?.response?.data?.detail ||
          "Could not save communication settings.",
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingState label="Loading communication settings…" />;

  if (!settings) {
    return (
      <ErrorState
        title="Communication settings unavailable"
        description={error}
        onRetry={load}
      />
    );
  }

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Communication Channels</h2>
        <Link to="/owner/settings" className="btn btn-secondary btn-sm">
          ← Back to settings
        </Link>
      </div>

      <p className="text-muted">
        WhatsApp remains the primary channel tenants already use. Email is
        optional — switch it on to add a fallback, a second copy of every
        notification, or to send by email only. SMTP credentials are configured
        in the deployment environment and are never stored or shown here.
      </p>

      {success && <div className="success-banner">{success}</div>}
      {formError && <div className="error-text">{formError}</div>}

      {channels && (
        <div
          className="grid gap-md mb-md"
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}
        >
          <ChannelCard name="whatsapp" title="WhatsApp" channel={channels.whatsapp} />
          <ChannelCard name="email" title="Email (SMTP)" channel={channels.email} />
        </div>
      )}

      <form className="card" onSubmit={save}>
        <h3>Delivery mode</h3>
        <div className="flex flex-col gap-sm mt-sm">
          {modes.map((mode) => (
            <label key={mode.value} className="flex items-start gap-sm">
              <input
                type="radio"
                name="channel-mode"
                value={mode.value}
                checked={settings.channel_mode === mode.value}
                onChange={() => update({ channel_mode: mode.value })}
              />
              <span>
                <strong>{mode.label}</strong>
                <span className="text-muted text-sm" style={{ display: "block" }}>
                  {mode.description}
                </span>
              </span>
            </label>
          ))}
        </div>

        <div className="dropdown-divider" />

        <h3>Channel switches</h3>
        <div className="flex flex-col gap-sm mt-sm">
          <label className="flex items-center gap-sm">
            <input
              type="checkbox"
              checked={settings.whatsapp_enabled}
              onChange={(e) => update({ whatsapp_enabled: e.target.checked })}
            />
            <span>WhatsApp enabled</span>
          </label>

          <label className="flex items-center gap-sm">
            <input
              type="checkbox"
              checked={settings.email_enabled}
              onChange={(e) => update({ email_enabled: e.target.checked })}
            />
            <span>Email enabled</span>
          </label>

          <label className="flex items-center gap-sm">
            <input
              type="checkbox"
              checked={settings.email_payment_receipts}
              disabled={!settings.email_enabled}
              onChange={(e) =>
                update({ email_payment_receipts: e.target.checked })
              }
            />
            <span>Include payment receipts on email</span>
          </label>
        </div>

        <p className="text-sm text-muted mt-sm">
          At least one channel must stay enabled — otherwise tenants would
          receive no notifications at all.
        </p>

        <button type="submit" className="btn btn-primary mt-md" disabled={saving}>
          {saving ? "Saving…" : "Save settings"}
        </button>
      </form>
    </section>
  );
}
