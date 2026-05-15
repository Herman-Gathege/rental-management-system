//frontend\src\features\settings\ChecklistTemplate.jsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getChecklistItems,
  createChecklistItem,
  updateChecklistItem,
  deleteChecklistItem,
  resetChecklistToDefaults,
} from "../../api/checklistTemplate";

export default function ChecklistTemplate() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // New item form
  const [newItemName, setNewItemName] = useState("");
  const [adding, setAdding] = useState(false);

  // Inline edit state
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");

  /* Load items */
  const fetchItems = async () => {
    try {
      setLoading(true);
      const data = await getChecklistItems();
      setItems(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load checklist");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  /* Add new item */
  const handleAdd = async () => {
    if (!newItemName.trim()) return;
    setAdding(true);
    try {
      const newItem = await createChecklistItem({ item_name: newItemName.trim() });
      setItems((prev) => [...prev, newItem]);
      setNewItemName("");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to add item");
    } finally {
      setAdding(false);
    }
  };

  /* Start inline edit */
  const startEdit = (item) => {
    setEditingId(item.id);
    setEditValue(item.item_name);
  };

  /* Save inline edit */
  const saveEdit = async (itemId) => {
    if (!editValue.trim()) return;
    try {
      const updated = await updateChecklistItem(itemId, { item_name: editValue.trim() });
      setItems((prev) => prev.map((i) => (i.id === itemId ? updated : i)));
      setEditingId(null);
      setEditValue("");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update item");
    }
  };

  /* Toggle active status */
  const toggleActive = async (item) => {
    try {
      const updated = await updateChecklistItem(item.id, { is_active: !item.is_active });
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to toggle item");
    }
  };

  /* Delete item */
  const handleDelete = async (item) => {
    if (!confirm(`Delete "${item.item_name}"? This cannot be undone.`)) return;
    try {
      await deleteChecklistItem(item.id);
      setItems((prev) => prev.filter((i) => i.id !== item.id));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete item");
    }
  };

  /* Reset to defaults */
  const handleReset = async () => {
    if (
      !confirm(
        "Reset to default checklist? This will delete ALL current items and restore the 13 default items from the lease form. This cannot be undone."
      )
    )
      return;
    try {
      await resetChecklistToDefaults();
      await fetchItems();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to reset");
    }
  };

  return (
    <section className="properties-page">
      {/* Back link */}
      <div className="flex items-center gap-sm mb-sm">
        <Link to="/owner/settings" className="text-sm checklist-back-link">
          ← Settings
        </Link>
      </div>

      {/* Header */}
      <div className="properties-header">
        <div>
          <h2 className="mb-xs">Inspection Checklist</h2>
          <p className="text-sm text-muted">
            Items inspectors check during move-in and move-out. Used to compare the state of a unit
            before and after a tenancy so damage deductions can be assessed against the deposit.
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={handleReset}>
          Reset to Defaults
        </button>
      </div>

      {error && <div className="error-text">{error}</div>}

      {/* Add new item */}
      <div className="card checklist-add-card">
        <h3>Add a New Item</h3>
        <div className="flex gap-sm items-center">
          <input
            className="input flex-1"
            placeholder="e.g. Swimming pool, Garden, Generator..."
            value={newItemName}
            onChange={(e) => setNewItemName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleAdd();
            }}
          />
          <button
            className="btn btn-primary btn-sm"
            onClick={handleAdd}
            disabled={!newItemName.trim() || adding}
          >
            {adding ? "Adding..." : "+ Add"}
          </button>
        </div>
      </div>

      {/* Items list */}
      {loading ? (
        <p>Loading...</p>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <p>No checklist items yet.</p>
          <button className="btn btn-primary" onClick={handleReset}>
            Load Default Items
          </button>
        </div>
      ) : (
        <div className="card checklist-items-card">
          {items.map((item, idx) => (
            <div
              key={item.id}
              className={`checklist-row ${!item.is_active ? "disabled" : ""}`}
            >
              {/* Order number */}
              <div className="checklist-row-number">{idx + 1}</div>

              {/* Item name (or edit input) */}
              <div className="checklist-row-name">
                {editingId === item.id ? (
                  <input
                    className="input"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter") saveEdit(item.id);
                      if (e.key === "Escape") {
                        setEditingId(null);
                        setEditValue("");
                      }
                    }}
                  />
                ) : (
                  <div>
                    <span>{item.item_name}</span>
                    {item.is_default && (
                      <span className="checklist-row-tag">(default)</span>
                    )}
                    {!item.is_active && (
                      <span className="checklist-row-tag tag-disabled">(disabled)</span>
                    )}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-sm">
                {editingId === item.id ? (
                  <>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => saveEdit(item.id)}
                    >
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
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => startEdit(item)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => toggleActive(item)}
                      title={item.is_active ? "Disable item" : "Enable item"}
                    >
                      {item.is_active ? "Disable" : "Enable"}
                    </button>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDelete(item)}
                    >
                      Delete
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
