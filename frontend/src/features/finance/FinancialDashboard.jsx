//frontend\src\features\finance\FinancialDashboard.jsx
import { useEffect, useState } from "react";
import { getDashboardSummary } from "../../api/finance";
import {
  getExpenseSummary,
  getNOI,
  getExpensesByCategory,
  getMonthlyExpenses,
} from "../../api/expenses";

const money = (n) => `KES ${Number(n || 0).toLocaleString()}`;

// "2026-03" -> "Mar 2026"
const monthLabel = (m) => {
  if (!m) return "";
  const [y, mm] = m.split("-");
  const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${names[parseInt(mm, 10) - 1] || mm} ${y}`;
};

// Year-to-date window.
const ytd = () => {
  const year = new Date().getFullYear();
  return { start_date: `${year}-01-01`, end_date: new Date().toISOString().slice(0, 10) };
};

const BAR_TRACK = {
  background: "#eef2f7",
  borderRadius: 4,
  height: 10,
  flex: 1,
  overflow: "hidden",
};

function Bar({ label, amount, max, color }) {
  const pct = max > 0 ? Math.max(2, Math.round((amount / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-sm mb-sm">
      <div className="text-sm" style={{ width: 130 }}>{label}</div>
      <div style={BAR_TRACK}>
        <div style={{ width: `${pct}%`, background: color, height: "100%" }} />
      </div>
      <div className="text-sm text-bold" style={{ width: 120, textAlign: "right" }}>
        {money(amount)}
      </div>
    </div>
  );
}

export default function FinancialDashboard() {
  const [summary, setSummary] = useState(null);
  const [expenseSummary, setExpenseSummary] = useState(null);
  const [noi, setNoi] = useState(null);
  const [byCategory, setByCategory] = useState([]);
  const [byMonth, setByMonth] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const params = ytd();
        const [sum, exp, noiData, cats, months] = await Promise.all([
          getDashboardSummary(),
          getExpenseSummary(params),
          getNOI(params),
          getExpensesByCategory(params),
          getMonthlyExpenses(params),
        ]);
        setSummary(sum);
        setExpenseSummary(exp);
        setNoi(noiData);
        setByCategory(cats);
        setByMonth(months);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load financial summary");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <p>Loading financial summary...</p>;
  if (error) return <p className="error-text">{error}</p>;
  if (!summary) return null;

  const cards = [
    { label: "Expected Monthly Rent", value: money(summary.total_expected_rent), color: "#2563eb" },
    { label: "Total Collected", value: money(summary.total_collected), color: "#16a34a" },
    { label: "Outstanding / Overdue", value: money(summary.total_overdue), color: "#ef4444" },
    { label: "Occupancy Rate", value: `${summary.occupancy_rate}%`, color: "#8b5cf6" },
    { label: "Occupied Units", value: `${summary.occupied_units} / ${summary.total_units}`, color: "#0891b2" },
  ];

  const noiValue = noi?.noi ?? 0;
  const expenseCards = [
    { label: "Expenses Paid (YTD)", value: money(expenseSummary?.total_paid), color: "#ef4444" },
    { label: "Approved — Pending Payment", value: money(expenseSummary?.total_approved), color: "#f59e0b" },
    {
      label: "Net Operating Income (YTD)",
      value: money(noiValue),
      color: noiValue >= 0 ? "#16a34a" : "#ef4444",
    },
  ];

  const maxCategory = Math.max(0, ...byCategory.map((c) => c.total));
  const maxMonth = Math.max(0, ...byMonth.map((m) => m.total));
  const byProperty = noi?.by_property || [];

  return (
    <section className="properties-page">
      <h2>Financial Overview</h2>

      {/* Existing rent/occupancy cards */}
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

      {/* ─── Expenses & Profitability (Sprint 5) ─── */}
      <h2 className="mt-md">Expenses & Profitability</h2>
      <p className="text-sm text-muted">Year to date. Income is collected payments; expenses are those marked paid.</p>

      <div className="grid-summary">
        {expenseCards.map((card) => (
          <div key={card.label} className="stat-card-r">
            <span className="text-sm text-muted">{card.label}</span>
            <span className="text-lg text-bold" style={{ color: card.color }}>
              {card.value}
            </span>
          </div>
        ))}
      </div>

      {/* Expenses by category */}
      <div className="card dash-panel mt-md">
        <div className="dash-panel-title">Expenses by Category (paid, YTD)</div>
        {byCategory.length === 0 ? (
          <p className="text-sm text-muted">No paid expenses yet this year.</p>
        ) : (
          byCategory.map((c) => (
            <Bar key={c.category_id} label={c.category_name} amount={c.total} max={maxCategory} color="#2563eb" />
          ))
        )}
      </div>

      {/* Monthly expenses */}
      <div className="card dash-panel mt-md">
        <div className="dash-panel-title">Monthly Expenses (paid)</div>
        {byMonth.length === 0 ? (
          <p className="text-sm text-muted">No paid expenses yet this year.</p>
        ) : (
          byMonth.map((m) => (
            <Bar key={m.month} label={monthLabel(m.month)} amount={m.total} max={maxMonth} color="#8b5cf6" />
          ))
        )}
      </div>

      {/* Profit by property */}
      <div className="card dash-panel mt-md">
        <div className="dash-panel-title">Profit by Property (YTD)</div>
        {byProperty.length === 0 ? (
          <p className="text-sm text-muted">No property data yet.</p>
        ) : (
          <div className="properties-table-wrapper">
            <table className="properties-table">
              <thead>
                <tr>
                  <th>Property</th>
                  <th>Income</th>
                  <th>Expenses</th>
                  <th>Profit (NOI)</th>
                </tr>
              </thead>
              <tbody>
                {byProperty.map((p) => (
                  <tr key={p.property_id}>
                    <td className="prop-name">{p.property_name}</td>
                    <td>{money(p.income)}</td>
                    <td>{money(p.expenses)}</td>
                    <td
                      className="text-bold"
                      style={{ color: p.noi >= 0 ? "#16a34a" : "#ef4444" }}
                    >
                      {money(p.noi)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
