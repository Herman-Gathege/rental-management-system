//frontend\src\features\settings\Settings.jsx
import { Link } from "react-router-dom";
import { FiCheckSquare, FiClock, FiTag, FiTruck } from "react-icons/fi";

export default function Settings() {
  const settingsTiles = [
    {
      title: "Inspection Checklist",
      description: "Customize the items inspectors check during move-in and move-out.",
      icon: <FiCheckSquare size={28} />,
      link: "/owner/settings/checklist",
      colorClass: "", // default blue
    },
    {
      title: "Expense Categories",
      description: "Manage the categories used when recording expenses.",
      icon: <FiTag size={28} />,
      link: "/owner/settings/expense-categories",
      colorClass: "",
    },
    {
      title: "Vendors",
      description: "Manage suppliers and service providers you record expenses against.",
      icon: <FiTruck size={28} />,
      link: "/owner/settings/vendors",
      colorClass: "",
    },
    {
      title: "Activity History",
      description: "View a log of all changes made across the system.",
      icon: <FiClock size={28} />,
      link: "/owner/history",
      colorClass: "tile-purple",
    },
    // Future tiles can be added here: billing defaults, notifications, etc.
  ];

  return (
    <section className="properties-page">
      <h2>Settings</h2>
      <p className="text-muted">
        Manage organization-level configuration for your property portfolio.
      </p>

      <div className="settings-tiles">
        {settingsTiles.map((tile) => (
          <Link
            key={tile.link}
            to={tile.link}
            className={`card settings-tile ${tile.colorClass}`}
          >
            <div className="settings-tile-icon">{tile.icon}</div>
            <h3 className="settings-tile-title">{tile.title}</h3>
            <p className="text-sm settings-tile-desc">{tile.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
