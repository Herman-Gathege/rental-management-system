//frontend\src\features\finance\FinancialDashboard.jsx
import { useEffect, useState } from "react";
import { getDashboardSummary } from "../../api/finance";

export default function FinancialDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await getDashboardSummary();
        setSummary(data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load summary");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  if (loading) return <p>Loading financial summary...</p>;
  if (error) return <p className="error-text">{error}</p>;
  if (!summary) return null;

  const cards = [
    { label: "Expected Monthly Rent", value: `KES ${Number(summary.total_expected_rent).toLocaleString()}`, color: "#2563eb" },
    { label: "Total Collected", value: `KES ${Number(summary.total_collected).toLocaleString()}`, color: "#16a34a" },
    { label: "Outstanding / Overdue", value: `KES ${Number(summary.total_overdue).toLocaleString()}`, color: "#ef4444" },
    { label: "Occupancy Rate", value: `${summary.occupancy_rate}%`, color: "#8b5cf6" },
    { label: "Occupied Units", value: `${summary.occupied_units} / ${summary.total_units}`, color: "#0891b2" },
  ];

  return (
    <section className="properties-page">
      <h2>Financial Overview</h2>

      <div className="grid-summary">
        {cards.map((card) => (
          <div key={card.label} className="stat-card-r">
            <span className="text-sm text-muted">{card.label}</span>
            <span className="text-lg text-bold" style={{ color: card.color }}>
              {card.value}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
