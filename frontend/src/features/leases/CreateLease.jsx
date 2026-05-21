//frontend\src\features\leases\CreateLease.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createLease, uploadSignedLease } from "../../api/leases";
import { getUnits } from "../../api/units";
import { getTenants } from "../../api/tenants";
import CollapsibleSection from "../../components/CollapsibleSection";

export default function CreateLease() {
  const navigate = useNavigate();

  const [units, setUnits] = useState([]);
  const [tenants, setTenants] = useState([]);

  const [form, setForm] = useState({
    unit_id: "",
    tenant_id: "",
    start_date: "",
    end_date: "",
    move_in_date: "",
    rent_amount: "",
    deposit_amount: "",
    billing_day: "1",
    signed_on_behalf_of: "",
    custom_fields: [],
  });

  // Optional signed lease PDF — uploaded after the lease is created
  const [signedLeaseFile, setSignedLeaseFile] = useState(null);

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  /* Load units + tenants on mount */
  useEffect(() => {
    const fetch = async () => {
      try {
        const [unitData, tenantData] = await Promise.all([
          getUnits(),
          getTenants(),
        ]);
        // Only show vacant active units
        setUnits(
          unitData.filter(
            (u) => u.occupancy_status === "vacant" && u.is_active,
          ),
        );
        setTenants(tenantData);
      } catch (err) {
        console.error(err);
      }
    };
    fetch();
  }, []);

  /* Auto-fill rent when unit is selected */
  useEffect(() => {
    if (form.unit_id) {
      const unit = units.find((u) => u.id === form.unit_id);
      if (unit) {
        setForm((prev) => ({ ...prev, rent_amount: String(unit.rent_amount) }));
      }
    }
  }, [form.unit_id, units]);

  /* Compute term in years from dates (display only) */
  const computeTermYears = () => {
    if (!form.start_date || !form.end_date) return null;
    const start = new Date(form.start_date);
    const end = new Date(form.end_date);
    const diffMs = end - start;
    if (diffMs <= 0) return null;
    const years = diffMs / (1000 * 60 * 60 * 24 * 365.25);
    return years.toFixed(1);
  };

  const termYears = computeTermYears();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    setSignedLeaseFile(file || null);
  };

  const addCustomField = (type) => {
    const newField = {
      id: crypto.randomUUID(),
      type,
      label: "",
      placeholder: "",
      required: false,
      options: [],
      value: "",
    };

    setForm((prev) => ({
      ...prev,
      custom_fields: [...prev.custom_fields, newField],
    }));
  };

  const updateCustomField = (fieldId, key, value) => {
    setForm((prev) => ({
      ...prev,
      custom_fields: prev.custom_fields.map((field) =>
        field.id === fieldId ? { ...field, [key]: value } : field,
      ),
    }));
  };

  const removeCustomField = (fieldId) => {
    setForm((prev) => ({
      ...prev,
      custom_fields: prev.custom_fields.filter((field) => field.id !== fieldId),
    }));
  };

  const handleSubmit = async () => {
    setError("");
    setSubmitting(true);

    try {
      const payload = {
        unit_id: form.unit_id,
        tenant_id: form.tenant_id,
        start_date: form.start_date,
        end_date: form.end_date || null,
        move_in_date: form.move_in_date || form.start_date,
        rent_amount: parseFloat(form.rent_amount),
        deposit_amount: form.deposit_amount
          ? parseFloat(form.deposit_amount)
          : 0,
        billing_day: parseInt(form.billing_day),
        signed_on_behalf_of: form.signed_on_behalf_of || null,
        custom_fields: form.custom_fields,
      };

      // Step 1: create the lease
      const lease = await createLease(payload);

      // Step 2: upload signed lease PDF if provided
      if (signedLeaseFile) {
        try {
          await uploadSignedLease(lease.id, signedLeaseFile);
        } catch (err) {
          console.error("Signed lease upload failed:", err);
        }
      }

      navigate("/owner/leases");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create lease");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="properties-page">
      <h2>Create New Lease</h2>

      {error && <div className="error-text">{error}</div>}

      <div className="property-form card">
        {/* ─── Core lease details ─── */}
        <div className="form-group">
          <label htmlFor="unit_id">Unit (vacant only)</label>
          <select
            id="unit_id"
            name="unit_id"
            className="input"
            value={form.unit_id}
            onChange={handleChange}
            required
          >
            <option value="">Select unit...</option>
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name} — {u.property_name} (KES{" "}
                {Number(u.rent_amount).toLocaleString()})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="tenant_id">Tenant</label>
          <select
            id="tenant_id"
            name="tenant_id"
            className="input"
            value={form.tenant_id}
            onChange={handleChange}
            required
          >
            <option value="">Select tenant...</option>
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>
                {t.full_name} — {t.phone}
              </option>
            ))}
          </select>
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="start_date">Start Date</label>
            <input
              id="start_date"
              name="start_date"
              className="input"
              type="date"
              value={form.start_date}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="end_date">
              End Date{" "}
              {termYears && (
                <span className="text-sm text-muted">
                  ({termYears} year term)
                </span>
              )}
            </label>
            <input
              id="end_date"
              name="end_date"
              className="input"
              type="date"
              value={form.end_date}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="rent_amount">Monthly Rent (KES)</label>
            <input
              id="rent_amount"
              name="rent_amount"
              className="input"
              type="number"
              value={form.rent_amount}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="deposit_amount">Security Deposit (KES)</label>
            <input
              id="deposit_amount"
              name="deposit_amount"
              className="input"
              type="number"
              placeholder="0"
              value={form.deposit_amount}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="billing_day">Billing Day (day of month)</label>
          <input
            id="billing_day"
            name="billing_day"
            className="input"
            type="number"
            min="1"
            max="28"
            value={form.billing_day}
            onChange={handleChange}
          />
        </div>

        {/* ─── Additional Details (collapsible) ─── */}
        <CollapsibleSection
          title="Additional Lease Details"
          summary={
            form.signed_on_behalf_of ||
            (signedLeaseFile ? "PDF attached" : null)
          }
        >
          <div className="form-group">
            <label htmlFor="move_in_date">
              Move-in / Possession Date
              <span className="text-sm text-muted">
                {" "}
                (defaults to start date)
              </span>
            </label>
            <input
              id="move_in_date"
              name="move_in_date"
              className="input"
              type="date"
              value={form.move_in_date}
              onChange={handleChange}
            />
            <p className="text-sm text-muted">
              Date when keys are issued to the tenant. May be after the lease
              start date if subject to payment of rent and deposit.
            </p>
          </div>

          <div className="form-group">
            <label htmlFor="signed_on_behalf_of">
              Signed on behalf of (optional)
            </label>
            <input
              id="signed_on_behalf_of"
              name="signed_on_behalf_of"
              className="input"
              type="text"
              placeholder='e.g. "John Doe acting for Jane Doe"'
              value={form.signed_on_behalf_of}
              onChange={handleChange}
            />
            <p className="text-sm text-muted">
              Use this if someone is signing the lease on behalf of the actual
              landlord.
            </p>
          </div>

          <div className="form-group">
            <label>Signed Lease Document (optional)</label>
            <div className="doc-upload-row">
              <div className="doc-upload-row-info">
                <div className="text-sm">
                  {signedLeaseFile ? signedLeaseFile.name : "No file selected"}
                </div>
              </div>
              <div className="flex gap-sm">
                {signedLeaseFile ? (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setSignedLeaseFile(null)}
                  >
                    Remove
                  </button>
                ) : (
                  <label className="btn btn-secondary btn-sm doc-upload-label">
                    Choose PDF
                    <input
                      type="file"
                      accept="application/pdf,image/*"
                      onChange={handleFileSelect}
                      className="doc-upload-hidden-input"
                    />
                  </label>
                )}
              </div>
            </div>
            <p className="text-sm text-muted">
              Upload a scan of the signed paper lease agreement.
            </p>
          </div>
        </CollapsibleSection>

        {/* ─── Custom Fields ─── */}
        <div className="card mt-md">
          <div className="flex justify-between items-center mb-md">
            <div>
              <h3>Add Fields</h3>
              <p className="text-sm text-muted">
                Add extra lease-specific fields (optional).
              </p>
            </div>

            <select
              className="input"
              defaultValue=""
              onChange={(e) => {
                if (e.target.value) {
                  addCustomField(e.target.value);
                  e.target.value = "";
                }
              }}
            >
              <option value="">+ Add Field</option>
              <option value="text">Text</option>
              <option value="textarea">Textarea</option>
              <option value="number">Number</option>
              <option value="date">Date</option>
              <option value="select">Select</option>
            </select>
          </div>

          {form.custom_fields.length === 0 ? (
            <p className="text-sm text-muted">No custom fields added yet.</p>
          ) : (
            form.custom_fields.map((field) => (
              <div key={field.id} className="card mt-sm">
                <div className="form-group">
                  <label>Field Label</label>

                  <input
                    type="text"
                    className="input"
                    placeholder="e.g. Employer Name"
                    value={field.label}
                    onChange={(e) =>
                      updateCustomField(field.id, "label", e.target.value)
                    }
                  />
                </div>

                <div className="form-group">
                  <label>Placeholder</label>

                  <input
                    type="text"
                    className="input"
                    placeholder="Optional placeholder"
                    value={field.placeholder}
                    onChange={(e) =>
                      updateCustomField(field.id, "placeholder", e.target.value)
                    }
                  />
                </div>

                <div className="form-group">
                  <label className="flex gap-sm items-center">
                    <input
                      type="checkbox"
                      checked={field.required}
                      onChange={(e) =>
                        updateCustomField(
                          field.id,
                          "required",
                          e.target.checked,
                        )
                      }
                    />
                    Required field
                  </label>
                </div>

                {field.type === "select" && (
                  <div className="form-group">
                    <label>Options (comma separated)</label>

                    <input
                      type="text"
                      className="input"
                      placeholder="Monthly, Quarterly, Annual"
                      value={field.options.join(", ")}
                      onChange={(e) =>
                        updateCustomField(
                          field.id,
                          "options",
                          e.target.value
                            .split(",")
                            .map((o) => o.trim())
                            .filter(Boolean),
                        )
                      }
                    />
                  </div>
                )}

                <div className="mt-sm">
                  <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    onClick={() => removeCustomField(field.id)}
                  >
                    Remove Field
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* ─── Info note about auto-inspection ─── */}
        <div className="card info-banner mt-md">
          <p className="text-sm">
            <strong>Note:</strong> A move-in inspection will be automatically
            created for this lease. You can conduct the inspection from the
            lease detail page after creation.
          </p>
        </div>

        {/* ─── Submit ─── */}
        <div className="flex gap-sm mt-md">
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={
              submitting ||
              !form.unit_id ||
              !form.tenant_id ||
              !form.start_date ||
              !form.rent_amount
            }
          >
            {submitting ? "Creating..." : "Create Lease"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => navigate("/owner/leases")}
            type="button"
          >
            Cancel
          </button>
        </div>
      </div>
    </section>
  );
}
