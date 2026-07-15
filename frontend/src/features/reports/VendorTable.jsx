import React from "react";

const money = (n) =>
  "KES " +
  Number(n || 0).toLocaleString("en-US", {
    maximumFractionDigits: 0,
  });

function OutstandingBadge({ outstanding }) {
  const value = Number(outstanding || 0);

  const settled = value <= 0;

  return (
    <span
      style={{
        display: "inline-block",
        padding: ".35rem .75rem",
        borderRadius: "999px",
        fontWeight: 600,
        fontSize: ".8rem",
        background: settled ? "#dcfce7" : "#fee2e2",
        color: settled ? "#166534" : "#991b1b",
      }}
    >
      {settled ? "Settled" : "Outstanding"}
    </span>
  );
}

export default function VendorTable({ rows }) {
  return (
    <table className="staff-table">
      <thead>
        <tr>
          <th>Vendor</th>
          <th>Invoices</th>
          <th>Total Billed</th>
          <th>Total Paid</th>
          <th>Outstanding</th>
          <th>Average Cost</th>
        </tr>
      </thead>

      <tbody>
        {rows.map((row) => (
          <tr key={row.vendor_id}>
            {/* Vendor */}
            <td>
              <div className="text-bold">
                {row.vendor_name}
              </div>

              <div className="text-muted">
                Service Provider
              </div>
            </td>

            {/* Invoices */}
            <td>
              <div
                className="text-bold"
                style={{
                  fontSize: "1.1rem",
                }}
              >
                {row.invoices}
              </div>

              <div className="text-muted">
                Total Invoices
              </div>
            </td>

            {/* Total Billed */}
            <td>
              <div className="text-bold">
                {money(row.total_billed)}
              </div>

              <div className="text-muted">
                Amount Billed
              </div>
            </td>

            {/* Total Paid */}
            <td>
              <div
                className="text-bold"
                style={{
                  color: "#16a34a",
                }}
              >
                {money(row.total_paid)}
              </div>

              <div className="text-muted">
                Paid to Vendor
              </div>
            </td>

            {/* Outstanding */}
            <td>
              <OutstandingBadge
                outstanding={row.outstanding}
              />

              <div
                className="text-bold"
                style={{
                  marginTop: ".5rem",
                  color:
                    Number(row.outstanding) > 0
                      ? "#dc2626"
                      : "#16a34a",
                }}
              >
                {money(row.outstanding)}
              </div>
            </td>

            {/* Average Cost */}
            <td>
              <div className="text-bold">
                {money(row.average_cost)}
              </div>

              <div className="text-muted">
                Per Invoice
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}