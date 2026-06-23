//frontend\src\features\expenses\EditExpense.jsx
import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getExpense, updateExpense } from "../../api/expenses";
import { getProperties } from "../../api/properties";
import { getUnits } from "../../api/units";
import { getExpenseCategories } from "../../api/expenseCategories";
import { getVendors } from "../../api/vendors";
import { useAuth } from "../../context/AuthContext";
import CollapsibleSection from "../../components/CollapsibleSection";

const PAYMENT_METHODS = ["Cash", "M-Pesa", "Bank Transfer", "Cheque", "Card", "Other"];

// The backend only allows edits while an expense is draft or submitted.
const EDITABLE_STATUSES = ["draft", "submitted"];

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

export default function EditExpense() {
  const { expenseId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const base = dashboardBase(user?.role?.toLowerCase());

  const [properties, setProperties] = useState([]);
  const [units, setUnits] = useState([]);
  const [categories, setCategories] = useState([]);
  const [vendors, setVendors] = useState([]);

  const [status, setStatus] = useState(null);
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const editable = status ? EDITABLE_STATUSES.includes(status) : true;

  /* Load the expense + dropdown data */
  useEffect(() => {
    const load = async () => {
      try {
        const [expense, props, cats, vens] = await Promise.all([
          getExpense(expenseId),
          getProperties(),
          getExpenseCategories(),
          getVendors(),
        ]);
        setProperties(props);
        setCategories(cats);
        setVendors(vens);
        setStatus(expense.status);
        setForm({
          property_id: expense.property_id || "",
          unit_id: expense.unit_id || "",
          category_id: expense.category_id || "",
          vendor_id: expense.vendor_id || "",
          title: expense.title || "",
          amount: expense.amount != null ? String(expense.amount) : "",
          expense_date: expense.expense_date || "",
          payment_method: expense.payment_method || "",
          reference_number: expense.reference_number || "",
          receipt_number: expense.receipt_number || "",
          description: expense.description || "",
          notes: expense.notes || "",
        });
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load expense");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [expenseId]);

  /* Load units for the selected property */
  useEffect(() => {
    if (!form?.property_id) {
      setUnits([]);
      return;
    }
    getUnits(form.property_id)
      .then(setUnits)
      .catch(() => setUnits([]));
  }, [form?.property_id]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handlePropertyChange = (e) => {
    setForm({ ...form, property_id: e.target.value, unit_id: "" });
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
      await updateExpense(expenseId, payload);
      navigate(`${base}/expenses`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update expense");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <p>Loading...</p>;
  if (!form) return <p className="error-text">{error || "Expense not found"}</p>;

  return (
    <section className="properties-page">
      <h2>Edit Expense</h2>

      {error && <div className="error-text">{error}</div>}

      {!editable && (
        <div className="card info-banner-warning">
          <p className="text-sm">
            This expense is <strong>{status}</strong> and can no longer be
            edited. Reject it back to draft first if you need to make changes.
          </p>
        </div>
      )}

      <div className="property-form card">
        <div className="form-group">
          <label htmlFor="property_id">Property</label>
          <select
            id="property_id"
            name="property_id"
            className="input"
            value={form.property_id}
            onChange={handlePropertyChange}
            disabled={!editable}
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
            disabled={!editable || !form.property_id}
          >
            <option value="">Whole property / no specific unit</option>
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
            disabled={!editable}
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
            disabled={!editable}
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
            value={form.title}
            onChange={handleChange}
            disabled={!editable}
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
              disabled={!editable}
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
              disabled={!editable}
              required
            />
          </div>
        </div>

        <CollapsibleSection
          title="More Details"
          summary={form.payment_method || null}
          defaultOpen={
            !!(form.payment_method || form.reference_number || form.description || form.notes)
          }
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
                disabled={!editable}
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
                disabled={!editable}
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
              disabled={!editable}
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
              disabled={!editable}
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
              disabled={!editable}
            />
          </div>
        </CollapsibleSection>

        <div className="flex gap-sm mt-md">
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={
              !editable ||
              submitting ||
              !form.property_id ||
              !form.category_id ||
              !form.title ||
              !form.amount ||
              !form.expense_date
            }
          >
            {submitting ? "Saving..." : "Save Changes"}
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
