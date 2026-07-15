import React from "react";

const money = (n) =>
  "KES " +
  Number(n || 0).toLocaleString("en-US", {
    maximumFractionDigits: 0,
  });

function ProfitBadge({ profit }) {
  const positive = Number(profit || 0) >= 0;

  return (
    <span
      style={{
        display: "inline-block",
        padding: ".35rem .75rem",
        borderRadius: "999px",
        fontWeight: 600,
        fontSize: ".8rem",
        background: positive ? "#dcfce7" : "#fee2e2",
        color: positive ? "#166534" : "#991b1b",
      }}
    >
      {positive ? "Profitable" : "Loss"}
    </span>
  );
}

export default function ProfitTable({ rows }) {
  return (
    <table className="staff-table">
      <thead>
        <tr>
          <th>Property</th>
          <th>Income</th>
          <th>Expenses</th>
          <th>Net Operating Income (NOI)</th>
        </tr>
      </thead>

      <tbody>
        {rows.map((row) => (
          <tr key={row.property_id}>
            {/* Property */}
            <td>
              <div className="text-bold">
                {row.property_name}
              </div>

              <div className="text-muted">
                Rental Property
              </div>
            </td>

            {/* Income */}
            <td>
              <div
                className="text-bold"
                style={{
                  color: "#16a34a",
                  fontSize: "1rem",
                }}
              >
                {money(row.income)}
              </div>

              <div className="text-muted">
                Rental Income
              </div>
            </td>

            {/* Expenses */}
            <td>
              <div
                className="text-bold"
                style={{
                  color: "#dc2626",
                  fontSize: "1rem",
                }}
              >
                {money(row.expenses)}
              </div>

              <div className="text-muted">
                Operating Costs
              </div>
            </td>

            {/* Profit */}
            <td>
              <ProfitBadge profit={row.profit} />

              <div
                className="text-bold"
                style={{
                  marginTop: ".5rem",
                  fontSize: "1.05rem",
                  color:
                    Number(row.profit) >= 0
                      ? "#16a34a"
                      : "#dc2626",
                }}
              >
                {money(row.profit)}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}