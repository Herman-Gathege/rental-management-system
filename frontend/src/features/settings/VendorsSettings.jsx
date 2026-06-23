//frontend\src\features\settings\VendorsSettings.jsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getVendors,
  createVendor,
  updateVendor,
  deleteVendor,
} from "../../api/vendors";
import { useAuth } from "../../context/AuthContext";

const EMPTY = {
  vendor_name: "",
  contact_person: "",
  phone: "",
  email: "",
  kra_pin: "",
  address: "",
  notes: "",
};

export default function VendorsSettings() {
  const { user } = useAuth();
  const base = user?.role?.toLowerCase() === "finance" ? "/finance" : "/owner";

  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // The form doubles as add (editingId null) and edit (editingId set).
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);

  const fetchVendors = async () => {
    try {
      setLoading(true);
      setVendors(await getVendors());
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load vendors");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const resetForm = () => {
    setForm(EMPTY);
    setEditingId(null);
  };

  const startEdit = (v) => {
    setEditingId(v.id);
    setForm({
      vendor_name: v.vendor_name || "",
      contact_person: v.contact_person || "",
      phone: v.phone || "",
      email: v.email || "",
      kra_pin: v.kra_pin || "",
      address: v.address || "",
      notes: v.notes || "",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSave = async () => {
    if (!form.vendor_name.trim()) return;
    setSaving(true);
    try {
      const payload = { ...form, vendor_name: form.vendor_name.trim() };
      if (editingId) {
        const updated = await updateVendor(editingId, payload);
        setVendors((prev) => prev.map((v) => (v.id === editingId ? updated : v)));
      } else {
        const created = await createVendor(payload);
        setVendors((prev) => [...prev, created]);
      }
      resetForm();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to save vendor");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (v) => {
    if (!confirm(`Delete vendor "${v.vendor_name}"? Past expenses keep their record but lose the vendor link.`))
      return;
    try {
      await deleteVendor(v.id);
      setVendors((prev) => prev.filter((x) => x.id !== v.id));
      if (editingId === v.id) resetForm();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete vendor");
    }
  };

  return (
    <section className="properties-page">
      {/* Back link */}
      <div className="flex items-center gap-sm mb-sm">
        <Link to={`${base}/settings`} className="text-sm checklist-back-link">
          ← Settings
        </Link>
      </div>

      <div className="properties-header">
        <div>
          <h2 className="mb-xs">Vendors</h2>
          <p className="text-sm text-muted">
            Suppliers and service providers you record expenses against (e.g.
            KPLC, plumbers, security firms).
          </p>
        </div>
      </div>

      {error && <div className="error-text">{error}</div>}

      {/* Add / Edit form */}
      <div className="card checklist-add-card">
        <h3>{editingId ? "Edit Vendor" : "Add a Vendor"}</h3>

        <div className="form-group">
          <label htmlFor="vendor_name">Vendor Name</label>
          <input
            id="vendor_name"
            name="vendor_name"
            className="input"
            value={form.vendor_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="contact_person">Contact Person</label>
            <input
              id="contact_person"
              name="contact_person"
              className="input"
              value={form.contact_person}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="phone">Phone</label>
            <input
              id="phone"
              name="phone"
              className="input"
              value={form.phone}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="two-col">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              className="input"
              type="email"
              value={form.email}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="kra_pin">KRA PIN</label>
            <input
              id="kra_pin"
              name="kra_pin"
              className="input"
              value={form.kra_pin}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="address">Address</label>
          <input
            id="address"
            name="address"
            className="input"
            value={form.address}
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

        <div className="flex gap-sm">
          <button
            className="btn btn-primary btn-sm"
            onClick={handleSave}
            disabled={!form.vendor_name.trim() || saving}
          >
            {saving ? "Saving..." : editingId ? "Save Changes" : "+ Add Vendor"}
          </button>
          {editingId && (
            <button className="btn btn-secondary btn-sm" onClick={resetForm}>
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* List */}
      {loading ? (
        <p>Loading...</p>
      ) : vendors.length === 0 ? (
        <div className="empty-state">
          <p>No vendors yet.</p>
          <p className="text-muted">Add a vendor above to start tracking who you pay.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-sm">
          {vendors.map((v) => (
            <div key={v.id} className="doc-upload-row">
              <div className="doc-upload-row-info">
                <div className="text-bold">{v.vendor_name}</div>
                <div className="text-xs text-muted">
                  {[v.contact_person, v.phone, v.email].filter(Boolean).join(" · ") || "No contact info"}
                </div>
              </div>
              <div className="flex gap-sm">
                <button className="btn btn-secondary btn-sm" onClick={() => startEdit(v)}>
                  Edit
                </button>
                <button className="btn btn-danger btn-sm" onClick={() => handleDelete(v)}>
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
