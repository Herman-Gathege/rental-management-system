import React from "react";

const money = (n) =>
  "KES " +
  Number(n || 0).toLocaleString("en-US", {
    maximumFractionDigits: 0,
  });

function RateBadge({ rate }) {
  const value = Number(rate || 0);

  let background = "#fee2e2";
  let color = "#991b1b";

  if (value >= 90) {
    background = "#dcfce7";
    color = "#166534";
  } else if (value >= 75) {
    background = "#fef3c7";
    color = "#92400e";
  }

  return (
    <span
      style={{
        display: "inline-block",
        padding: ".35rem .75rem",
        borderRadius: "999px",
        fontWeight: 600,
        fontSize: ".8rem",
        background,
        color,
      }}
    >
      {value.toFixed(1)}%
    </span>
  );
}

export default function CollectionTable({ rows }) {
  return (
    <table className="staff-table">
      <thead>
        <tr>
          <th>Property</th>
          <th>Expected Rent</th>
          <th>Collected</th>
          <th>Outstanding</th>
          <th>Collection Rate</th>
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

            {/* Expected */}
            <td>
              <div className="text-bold">
                {money(row.expected_rent)}
              </div>

              <div className="text-muted">
                Expected Income
              </div>
            </td>

            {/* Collected */}
            <td>
              <div
                className="text-bold"
                style={{
                  color: "#16a34a",
                }}
              >
                {money(row.collected)}
              </div>

              <div className="text-muted">
                Received
              </div>
            </td>

            {/* Outstanding */}
            <td>
              <div
                className="text-bold"
                style={{
                  color:
                    Number(row.outstanding) > 0
                      ? "#dc2626"
                      : "#16a34a",
                }}
              >
                {money(row.outstanding)}
              </div>

              <div className="text-muted">
                Pending Collection
              </div>
            </td>

            {/* Collection Rate */}
            <td>
              <RateBadge
                rate={row.collection_rate}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}