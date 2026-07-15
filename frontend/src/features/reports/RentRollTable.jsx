import React from "react";

const money = (n) =>
  "KES " +
  Number(n || 0).toLocaleString("en-US", {
    maximumFractionDigits: 0,
  });

function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

function StatusBadge({ status }) {
  const value = String(status || "").toLowerCase();

  let background = "#f3f4f6";
  let color = "#374151";

  if (value === "active") {
    background = "#dcfce7";
    color = "#166534";
  }

  if (value === "terminated") {
    background = "#fee2e2";
    color = "#991b1b";
  }

  if (value === "pending") {
    background = "#fef3c7";
    color = "#92400e";
  }

  return (
    <span
      style={{
        padding: ".35rem .75rem",
        borderRadius: "999px",
        fontWeight: 600,
        fontSize: ".82rem",
        background,
        color,
      }}
    >
      {status}
    </span>
  );
}

function BalanceBadge({ balance }) {
  const value = Number(balance || 0);

  let label = "Settled";
  let background = "#dcfce7";
  let color = "#166534";

  if (value > 0) {
    label = "Outstanding";
    background = "#fee2e2";
    color = "#991b1b";
  }

  if (value < 0) {
    label = "Credit";
    background = "#dbeafe";
    color = "#1d4ed8";
  }

  return (
    <div>
      <div
        style={{
          display: "inline-block",
          padding: ".3rem .65rem",
          borderRadius: "999px",
          fontSize: ".75rem",
          fontWeight: 600,
          marginBottom: ".35rem",
          background,
          color,
        }}
      >
        {label}
      </div>

      <div className="text-bold">
        {money(Math.abs(value))}
      </div>
    </div>
  );
}

export default function RentRollTable({ rows }) {
  return (
    <table className="staff-table">
      <thead>
        <tr>
          <th>Tenant</th>
          <th>Property</th>
          <th>Monthly Rent</th>
          <th>Deposit Held</th>
          <th>Balance</th>
          <th>Lease</th>
        </tr>
      </thead>

      <tbody>
        {rows.map((row) => (
          <tr key={row.lease_id}>
            {/* Tenant */}
            <td>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: ".75rem",
                }}
              >
                <div
                  style={{
                    width: 42,
                    height: 42,
                    borderRadius: "50%",
                    background: "#2563eb",
                    color: "#fff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: ".9rem",
                  }}
                >
                  {initials(row.tenant_name || "")}
                </div>

                <div>
                  <div className="text-bold">
                    {row.tenant_name || "Unknown"}
                  </div>

                  <div className="text-muted">
                    Lease Tenant
                  </div>
                </div>
              </div>
            </td>

            {/* Property */}
            <td>
              <div className="text-bold">
                {row.property_name}
              </div>

              <div className="text-muted">
                Unit {row.unit_name}
              </div>
            </td>

            {/* Rent */}
            <td>
              <div className="text-bold">
                {money(row.monthly_rent)}
              </div>

              <div className="text-muted">
                Monthly
              </div>
            </td>

            {/* Deposit */}
            <td>
              <div className="text-bold">
                {money(row.deposit_held)}
              </div>

              <div className="text-muted">
                Held
              </div>
            </td>

            {/* Balance */}
            <td>
              <BalanceBadge
                balance={row.balance}
              />
            </td>

            {/* Lease */}
            <td>
              <StatusBadge
                status={row.status}
              />

              <div
                className="text-muted"
                style={{
                  marginTop: ".6rem",
                  fontSize: ".8rem",
                }}
              >
                {row.start_date || "-"}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}