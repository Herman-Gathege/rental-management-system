//frontend\src\features\settings\ExpenseCategoriesSettings.jsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getExpenseCategories,
  createExpenseCategory,
  updateExpenseCategory,
} from "../../api/expenseCategories";
import { useAuth } from "../../context/AuthContext";

export default function ExpenseCategoriesSettings() {
  const { user } = useAuth();
  // Back-link is role-aware so this page works under /owner or /finance.
  const base = user?.role?.toLowerCase() === "finance" ? "/finance" : "/owner";

  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [newName, setNewName] = useState("");
  const [adding, setAdding] = useState(false);

  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");

  const fetchCategories = async () => {
    try {
      setLoading(true);
      // include inactive so they can be managed/re-enabled here
      const data = await getExpenseCategories(true);
      setCategories(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load categories");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  const handleAdd = async () => {
    if (!newName.trim()) return;
    setAdding(true);
    try {
      const created = await createExpenseCategory({ name: newName.trim() });
      setCategories((prev) => [...prev, created]);
      setNewName("");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to add category");
    } finally {
      setAdding(false);
    }
  };

  const startEdit = (cat) => {
    setEditingId(cat.id);
    setEditValue(cat.name);
  };

  const saveEdit = async (catId) => {
    if (!editValue.trim()) return;
    try {
      const updated = await updateExpenseCategory(catId, { name: editValue.trim() });
      setCategories((prev) => prev.map((c) => (c.id === catId ? updated : c)));
      setEditingId(null);
      setEditValue("");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to rename category");
    }
  };

  const toggleActive = async (cat) => {
    try {
      const updated = await updateExpenseCategory(cat.id, { is_active: !cat.is_active });
      setCategories((prev) => prev.map((c) => (c.id === cat.id ? updated : c)));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to toggle category");
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
          <h2 className="mb-xs">Expense Categories</h2>
          <p className="text-sm text-muted">
            Standard categories used when recording expenses. Categories can't be
            deleted (they're attached to past expenses) — disable one to hide it
            from new expenses while keeping its history.
          </p>
        </div>
      </div>

      {error && <div className="error-text">{error}</div>}

      {/* Add */}
      <div className="card checklist-add-card">
        <h3>Add a Category</h3>
        <div className="flex gap-sm items-center">
          <input
            className="input flex-1"
            placeholder="e.g. Pest Control, Service Charge..."
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleAdd();
            }}
          />
          <button
            className="btn btn-primary btn-sm"
            onClick={handleAdd}
            disabled={!newName.trim() || adding}
          >
            {adding ? "Adding..." : "+ Add"}
          </button>
        </div>
      </div>

      {/* List */}
      {loading ? (
        <p>Loading...</p>
      ) : categories.length === 0 ? (
        <div className="empty-state">
          <p>No categories yet.</p>
        </div>
      ) : (
        <div className="card checklist-items-card">
          {categories.map((cat, idx) => (
            <div
              key={cat.id}
              className={`checklist-row ${!cat.is_active ? "disabled" : ""}`}
            >
              <div className="checklist-row-number">{idx + 1}</div>

              <div className="checklist-row-name">
                {editingId === cat.id ? (
                  <input
                    className="input"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter") saveEdit(cat.id);
                      if (e.key === "Escape") {
                        setEditingId(null);
                        setEditValue("");
                      }
                    }}
                  />
                ) : (
                  <div>
                    <span>{cat.name}</span>
                    {!cat.is_active && (
                      <span className="checklist-row-tag tag-disabled">(disabled)</span>
                    )}
                  </div>
                )}
              </div>

              <div className="flex gap-sm">
                {editingId === cat.id ? (
                  <>
                    <button className="btn btn-primary btn-sm" onClick={() => saveEdit(cat.id)}>
                      Save
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => {
                        setEditingId(null);
                        setEditValue("");
                      }}
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button className="btn btn-secondary btn-sm" onClick={() => startEdit(cat)}>
                      Edit
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => toggleActive(cat)}
                      title={cat.is_active ? "Disable category" : "Enable category"}
                    >
                      {cat.is_active ? "Disable" : "Enable"}
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
