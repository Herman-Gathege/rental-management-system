// frontend/src/features/settings/AutomationSettings.jsx
//
// Billing automation settings (requirement 3).
//
// Invoice generation defaults to the 1st and pending-payment reminders to the
// 10th; both are configurable here. The backend rejects days 29-31 because
// those don't exist in every month, and every run is idempotent — so "Run now"
// is safe to press twice.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getAutomationSettings,
  updateAutomationSettings,
  runAutomationNow,
  getAutomationHistory,
} from "../../api/settings";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  TableSkeleton,
} from "../../components/ui/States";

const DAYS = Array.from({ length: 28 }, (_, i) => i + 1);

const fmtDateTime = (value) =>
  value ? new Date(value).toLocaleString() : "—";

export default function AutomationSettings() {
  const [settings, setSettings] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = async () => {
    setError("");
    setLoading(true);
    try {
      const data = await getAutomationSettings();
      setSettings(data.settings);
    } catch (err) {
      setError(
        err?.response?.data?.detail || "Could not load automation settings.",
      );
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      setHistory(await getAutomationHistory(15));
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    load();
    loadHistory();
  }, []);

  const update = (patch) =>
    setSettings((prev) => ({ ...prev, ...patch }));

  const save = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const data = await updateAutomationSettings({
        invoice_generation_day: Number(settings.invoice_generation_day),
        reminder_day: Number(settings.reminder_day),
        invoice_automation_enabled: settings.invoice_automation_enabled,
        reminder_automation_enabled: settings.reminder_automation_enabled,
        timezone: settings.timezone,
      });
      setSettings(data.settings);
      setSuccess("Automation settings saved.");
      setTimeout(() => setSuccess(""), 4000);
    } catch (err) {
      setError(
        err?.response?.data?.detail || "Could not save automation settings.",
      );
    } finally {
      setSaving(false);
    }
  };

  const runNow = async (job) => {
    setRunning(job);
    setError("");
    setSuccess("");
    try {
      const result = await runAutomationNow(job);
      setSuccess(
        result.already_completed
          ? result.message
          : result.run?.message || "Automation run completed.",
      );
      await loadHistory();
      setTimeout(() => setSuccess(""), 6000);
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not run the automation.");
    } finally {
      setRunning("");
    }
  };

  if (loading) return <LoadingState label="Loading automation settings…" />;

  if (!settings) {
    return (
      <ErrorState
        title="Automation settings unavailable"
        description={error}
        onRetry={load}
      />
    );
  }

  return (
    <section className="properties-page">
      <div className="properties-header">
        <h2>Billing Automation</h2>
        <Link to="/owner/settings" className="btn btn-secondary btn-sm">
          ← Back to settings
        </Link>
      </div>

      <p className="text-muted">
        Invoices are raised for every active lease on your chosen day, and
        tenants with an outstanding balance are reminded on the reminder day.
        Running either job twice on the same day is safe — the system will not
        create duplicate invoices or send duplicate reminders.
      </p>

      {success && <div className="success-banner">{success}</div>}
      {error && <div className="error-text">{error}</div>}

      <form className="card" onSubmit={save}>
        <div className="grid gap-md" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}>
          <div className="form-group">
            <label htmlFor="invoice-day">Invoice generation day</label>
            <select
              id="invoice-day"
              className="input"
              value={settings.invoice_generation_day}
              disabled={!settings.invoice_automation_enabled}
              onChange={(e) => update({ invoice_generation_day: e.target.value })}
            >
              {DAYS.map((day) => (
                <option key={day} value={day}>
                  Day {day} of each month
                </option>
              ))}
            </select>
            <small className="text-muted">
              Default: day 1. Days 29–31 aren’t available because they don’t
              exist in every month.
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="reminder-day">Pending-payment reminder day</label>
            <select
              id="reminder-day"
              className="input"
              value={settings.reminder_day}
              disabled={!settings.reminder_automation_enabled}
              onChange={(e) => update({ reminder_day: e.target.value })}
            >
              {DAYS.map((day) => (
                <option key={day} value={day}>
                  Day {day} of each month
                </option>
              ))}
            </select>
            <small className="text-muted">
              Default: day 10. Tenants who have already paid are skipped.
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="timezone">Timezone</label>
            <input
              id="timezone"
              className="input"
              type="text"
              value={settings.timezone}
              onChange={(e) => update({ timezone: e.target.value })}
              placeholder="Africa/Nairobi"
            />
            <small className="text-muted">
              Determines which calendar day counts as “today”.
            </small>
          </div>
        </div>

        <div className="flex flex-col gap-sm mt-md">
          <label className="flex items-center gap-sm">
            <input
              type="checkbox"
              checked={settings.invoice_automation_enabled}
              onChange={(e) =>
                update({ invoice_automation_enabled: e.target.checked })
              }
            />
            <span>Automatically generate monthly invoices</span>
          </label>

          <label className="flex items-center gap-sm">
            <input
              type="checkbox"
              checked={settings.reminder_automation_enabled}
              onChange={(e) =>
                update({ reminder_automation_enabled: e.target.checked })
              }
            />
            <span>Automatically remind tenants with pending payments</span>
          </label>
        </div>

        <div className="flex gap-sm flex-wrap mt-md">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving…" : "Save settings"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => runNow("invoice_generation")}
            disabled={running === "invoice_generation"}
          >
            {running === "invoice_generation" ? "Running…" : "Run invoicing now"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => runNow("payment_reminder")}
            disabled={running === "payment_reminder"}
          >
            {running === "payment_reminder" ? "Running…" : "Run reminders now"}
          </button>
        </div>
      </form>

      <h3 className="mt-lg">Recent automation runs</h3>
      {historyLoading ? (
        <TableSkeleton rows={4} columns={5} />
      ) : history.length === 0 ? (
        <EmptyState
          title="No automation runs yet"
          description="Runs appear here once the scheduled job first executes, or after you use “Run now”."
        />
      ) : (
        <div className="properties-table-wrapper">
          <table className="properties-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Job</th>
                <th>Status</th>
                <th>Created</th>
                <th>Notified</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {history.map((run) => (
                <tr key={run.id}>
                  <td>{run.run_date}</td>
                  <td>{run.job === "invoice_generation" ? "Invoicing" : "Reminders"}</td>
                  <td>
                    <span className={`status-pill ${run.status === "success" ? "status-ok" : "status-owed"}`}>
                      {run.status}
                    </span>
                  </td>
                  <td>{run.created_count}</td>
                  <td>{run.notified_count}</td>
                  <td className="text-sm text-muted">
                    {run.message || "—"}
                    <div className="text-muted" style={{ fontSize: 11 }}>
                      finished {fmtDateTime(run.finished_at)}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
