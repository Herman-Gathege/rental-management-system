import React from "react";

const money = (n) =>
  "KES " + Number(n || 0).toLocaleString("en-US", {
    maximumFractionDigits: 0,
  });

export default function ReportSummary({ activeReport, rows }) {
  if (!rows || rows.length === 0) return null;

  let cards = [];

  switch (activeReport) {
    case "rent-roll": {
      const activeLeases = rows.filter(
        (r) => String(r.status).toLowerCase() === "active"
      ).length;

      const terminatedLeases = rows.filter(
        (r) => String(r.status).toLowerCase() === "terminated"
      ).length;

      const depositsHeld = rows.reduce(
        (sum, r) => sum + Number(r.deposit_held || 0),
        0
      );

      const outstandingRent = rows.reduce((sum, r) => {
        const balance = Number(r.balance || 0);
        return balance > 0 ? sum + balance : sum;
      }, 0);

      cards = [
        {
          title: "Active Leases",
          value: activeLeases,
        },
        {
          title: "Terminated",
          value: terminatedLeases,
        },
        {
          title: "Deposits Held",
          value: money(depositsHeld),
        },
        {
          title: "Outstanding Rent",
          value: money(outstandingRent),
        },
      ];

      break;
    }

    case "collection": {
      const expected = rows.reduce(
        (sum, r) => sum + Number(r.expected_rent || 0),
        0
      );

      const collected = rows.reduce(
        (sum, r) => sum + Number(r.collected || 0),
        0
      );

      const outstanding = rows.reduce(
        (sum, r) => sum + Number(r.outstanding || 0),
        0
      );

      const avgRate =
        rows.length === 0
          ? 0
          : (
              rows.reduce(
                (sum, r) => sum + Number(r.collection_rate || 0),
                0
              ) / rows.length
            ).toFixed(1);

      cards = [
        {
          title: "Expected",
          value: money(expected),
        },
        {
          title: "Collected",
          value: money(collected),
        },
        {
          title: "Outstanding",
          value: money(outstanding),
        },
        {
          title: "Average Collection",
          value: `${avgRate}%`,
        },
      ];

      break;
    }

    case "vendor": {
      const invoices = rows.reduce(
        (sum, r) => sum + Number(r.invoices || 0),
        0
      );

      const billed = rows.reduce(
        (sum, r) => sum + Number(r.total_billed || 0),
        0
      );

      const paid = rows.reduce(
        (sum, r) => sum + Number(r.total_paid || 0),
        0
      );

      const outstanding = rows.reduce(
        (sum, r) => sum + Number(r.outstanding || 0),
        0
      );

      cards = [
        {
          title: "Invoices",
          value: invoices,
        },
        {
          title: "Total Billed",
          value: money(billed),
        },
        {
          title: "Total Paid",
          value: money(paid),
        },
        {
          title: "Outstanding",
          value: money(outstanding),
        },
      ];

      break;
    }

    case "profit": {
      const income = rows.reduce(
        (sum, r) => sum + Number(r.income || 0),
        0
      );

      const expenses = rows.reduce(
        (sum, r) => sum + Number(r.expenses || 0),
        0
      );

      const profit = rows.reduce(
        (sum, r) => sum + Number(r.profit || 0),
        0
      );

      cards = [
        {
          title: "Income",
          value: money(income),
        },
        {
          title: "Expenses",
          value: money(expenses),
        },
        {
          title: "Net Profit",
          value: money(profit),
        },
        {
          title: "Properties",
          value: rows.length,
        },
      ];

      break;
    }

    default:
      return null;
  }

  return (
    <div
      className="grid gap-md mb-md"
      style={{
        gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))",
      }}
    >
      {cards.map((card) => (
        <div key={card.title} className="card">
          <div
            className="text-muted"
            style={{
              fontSize: ".85rem",
              marginBottom: ".4rem",
            }}
          >
            {card.title}
          </div>

          <div
            className="text-bold"
            style={{
              fontSize: "1.6rem",
            }}
          >
            {card.value}
          </div>
        </div>
      ))}
    </div>
  );
}