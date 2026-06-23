//frontend\src\features\expenses\CreateExpense.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createExpense, uploadExpenseAttachment } from "../../api/expenses";
import { getProperties } from "../../api/properties";
import { getUnits } from "../../api/units";
import { getExpenseCategories } from "../../api/expenseCategories";
import { getVendors } from "../../api/vendors";
import { useAuth } from "../../context/AuthContext";
import CollapsibleSection from "../../components/CollapsibleSection";

const PAYMENT_METHODS = ["Cash", "M-Pesa", "Bank Transfer", "Cheque", "Card", "Other"];

function dashboardBase(role) {
  switch (role) {
    case "property_manager":
      return "/manager";
    case "finance":
      return "/finance";
    default:
      return "/owner";
  }
}

const today = () => new Date().toISOString().slice(0, 10);

export default function CreateExpense() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const base = dashboardBase(user?.role?.toLowerCase());

  const [properties, setProperties] = useState([]);
  const [units, setUnits] = useState([]);
  const [categories, setCategories] = useState([]);
  const [vendors, setVendors] = useState([]);

  const [form, setForm] = useState({
    property_id: "",
    unit_id: "",
    category_id: "",
    vendor_id: "",
    title: "",
    amount: "",
    expense_date: today(),
    payment_method: "",
    reference_number: "",
    receipt_number: "",
    description: "",
    notes: "",
  });

  const [receiptFile, setReceiptFile] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  /* Load dropdown data on mount */
  useEffect(() => {
    const load = async () => {
      try {
        const [props, cats, vens] = await Promise.all([
          getProperties(),
          getExpenseCategories(),
          getVendors(),
        ]);
        setProperties(props);
        setCategories(cats);
        setVendors(vens);
      } catch (err) {
        console.error(err);
      }
    };
    load();
  }, []);

  /* Load units whenever the chosen property changes */
  useEffect(() => {
    if (!form.property_id) {
      setUnits([]);
      return;
    }
    getUnits(form.property_id)
      .then(setUnits)
      .catch(() => setUnits([]));
  }, [form.property_id]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handlePropertyChange = (e) => {
    // Switching property invalidates the previously chosen unit.
    setForm({ ...form, property_id: e.target.value, unit_id: "" });
  };

  const handleFileSelect = (e) => {
    setReceiptFile(e.target.files[0] || null);
  };

  const handleSubmit = async () => {
    setError("");
    setSubmitting(true);
    try {
      const payload = {
        property_id: form.property_id,
        unit_id: form.unit_id || null,
        category_id: form.category_id,
        vendor_id: form.vendor_id || null,
        title: form.title,
        amount: parseFloat(form.amount),
        expense_date: form.expense_date,
        payment_method: form.payment_method || null,
        reference_number: form.reference_number || null,
        receipt_number: form.receipt_number || null,
        description: form.description || null,
        notes: form.notes || null,
      };

      const expense = await createExpense(payload);

      // Optional receipt upload after creation.
      if (receiptFile) {
        try {
          await uploadExpenseAttachment(expense.id, receiptFile);
        } catch (err) {
          console.error("Receipt upload failed:", err);
        }
      }

      navigate(`${base}/expenses`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create expense");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="properties-page">
      <h2>Record New Expense</h2>

      {error && <div className="error-text">{error}</div>}

      <div className="property-form card">
        {/* ─── Core details ─── */}
        <div className="form-group">
          <label htmlFor="property_id">Property</label>
          <select
            id="property_id"
            name="property_id"
            className="input"
            value={form.property_id}
            onChange={handlePropertyChange}
            required
          >
            <option value="">Select property...</option>
            {properties.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="unit_id">
            Unit <span className="text-sm text-muted">(optional)</span>
          </label>
          <select
            id="unit_id"
            name="unit_id"
            className="input"
            value={form.unit_id}
            onChange={handleChange}
            disabled={!form.property_id}
          >
            <option value="">
              {form.property_id ? "Whole property / no specific unit" : "Select a property first"}
            </option>
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="category_id">Category</label>
          <select
            id="category_id"
            name="category_id"
            className="input"
            value={form.category_id}
            onChange={handleChange}
            required
          >
            <option value="">Select category...</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="vendor_id">
            Vendor <span className="text-sm text-muted">(optional)</span>
          </label>
          <select
            id="vendor_id"
            name="vendor_id"
            className="input"
            value={form.vendor_id}
            onChange={handleChange}
          >
            <option value="">No vendor</option>
            {vendors.map((v) => (
              <option key={v.id} value={v.id}>
                {v.vendor_name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="title">Title / Description</label>
          <input
            id="title"
            name="title"
            className="input"
            type="text"
            placeholder="e.g. Plumbing repair — Block A"
            value={form.title}
            onChange={handleChange}
            required
          />
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="amount">Amount (KES)</label>
            <input
              id="amount"
              name="amount"
              className="input"
              type="number"
              min="0"
              step="0.01"
              value={form.amount}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="expense_date">Expense Date</label>
            <input
              id="expense_date"
              name="expense_date"
              className="input"
              type="date"
              value={form.expense_date}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        {/* ─── More details (collapsible) ─── */}
        <CollapsibleSection
          title="More Details"
          summary={form.payment_method || (receiptFile ? "Receipt attached" : null)}
        >
          <div className="two-col">
            <div className="form-group">
              <label htmlFor="payment_method">Payment Method</label>
              <select
                id="payment_method"
                name="payment_method"
                className="input"
                value={form.payment_method}
                onChange={handleChange}
              >
                <option value="">Not specified</option>
                {PAYMENT_METHODS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="reference_number">Reference / Transaction No.</label>
              <input
                id="reference_number"
                name="reference_number"
                className="input"
                type="text"
                value={form.reference_number}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="receipt_number">Receipt Number</label>
            <input
              id="receipt_number"
              name="receipt_number"
              className="input"
              type="text"
              value={form.receipt_number}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              className="input"
              rows={2}
              value={form.description}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              name="notes"
              className="input"
              rows={2}
              value={form.notes}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>Receipt (optional)</label>
            <div className="doc-upload-row">
              <div className="doc-upload-row-info">
                <div className="text-sm">
                  {receiptFile ? receiptFile.name : "No file selected"}
                </div>
              </div>
              <div className="flex gap-sm">
                {receiptFile ? (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setReceiptFile(null)}
                  >
                    Remove
                  </button>
                ) : (
                  <label className="btn btn-secondary btn-sm doc-upload-label">
                    Choose file
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
              You can also add receipts later from the expense's detail page.
            </p>
          </div>
        </CollapsibleSection>

        {/* ─── Submit ─── */}
        <div className="flex gap-sm mt-md">
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={
              submitting ||
              !form.property_id ||
              !form.category_id ||
              !form.title ||
              !form.amount ||
              !form.expense_date
            }
          >
            {submitting ? "Saving..." : "Save Expense"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => navigate(`${base}/expenses`)}
            type="button"
          >
            Cancel
          </button>
        </div>
      </div>
    </section>
  );
}
