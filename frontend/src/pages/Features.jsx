import SEO from "../components/SEO";

export default function Features() {
  const categories = [
    {
      title: "Property & Unit Management",
      icon: "fa-solid fa-building",
      items: [
        { title: "Multi-Property Portfolios", desc: "Manage apartments, hostels, commercial units, and mixed portfolios from one dashboard." },
        { title: "Unit Tracking", desc: "Track unit types, sizes, rent amounts, and occupancy status in real time." },
        { title: "Bulk Import", desc: "Upload properties, units, and tenants via CSV to save hours of manual data entry." },
        { title: "Property Details", desc: "Store addresses, photos, amenities, and notes for every property." },
      ],
    },
    {
      title: "Tenant & Lease Management",
      icon: "fa-solid fa-users",
      items: [
        { title: "Tenant Profiles", desc: "Full tenant records including contact info, ID numbers, emergency contacts, and next of kin." },
        { title: "Lease Agreements", desc: "Create leases with start/end dates, rent, deposits, and billing cycles. Upload signed documents." },
        { title: "Move-In & Move-Out", desc: "Linked inspections with checklist-based condition reports and photo uploads." },
        { title: "Lease Renewals", desc: "Track upcoming expiries and send reminders before leases end." },
      ],
    },
    {
      title: "Rent & Payment Collection",
      icon: "fa-solid fa-credit-card",
      items: [
        { title: "M-Pesa Integration", desc: "Collect rent directly through M-Pesa with automatic reconciliation and receipts." },
        { title: "Payment Tracking", desc: "See who paid, who is behind, and how much is outstanding at a glance." },
        { title: "Batch Payments", desc: "Record multiple payments at once for faster month-end closing." },
        { title: "Payment Reconciliation", desc: "Review and confirm payments with a simple queue-based workflow." },
      ],
    },
    {
      title: "Financial & Expense Management",
      icon: "fa-solid fa-chart-pie",
      items: [
        { title: "Financial Dashboard", desc: "Real-time view of expected rent, collections, deposits, and occupancy rates." },
        { title: "Expense Tracking", desc: "Record maintenance, repairs, and operating expenses with receipts." },
        { title: "Profit & Loss", desc: "Generate property-level P&L reports to understand true portfolio performance." },
        { title: "Vendor Management", desc: "Track vendors, contractors, and service providers per property." },
      ],
    },
    {
      title: "Maintenance & Inspections",
      icon: "fa-solid fa-clipboard-check",
      items: [
        { title: "Maintenance Tickets", desc: "Tenants and managers can submit requests with photos, priorities, and status tracking." },
        { title: "Inspection Checklists", desc: "Standardized move-in and move-out inspections with condition scoring." },
        { title: "Ticket History", desc: "Full audit trail of every maintenance request from creation to resolution." },
        { title: "Assignment & Alerts", desc: "Assign tickets to staff and get notified when work is completed." },
      ],
    },
    {
      title: "Reports & Analytics",
      icon: "fa-solid fa-chart-column",
      items: [
        { title: "Rent Roll Reports", desc: "Detailed rent roll showing all units, tenants, balances, and lease terms." },
        { title: "Collection Reports", desc: "Expected vs. collected analysis by property, unit, or date range." },
        { title: "Occupancy Analytics", desc: "Track vacancy rates, average lease lengths, and turnover trends." },
        { title: "Exportable Data", desc: "Download reports as PDFs or spreadsheets for accounting and tax purposes." },
      ],
    },
    {
      title: "Communication & Notifications",
      icon: "fa-solid fa-bell",
      items: [
        { title: "In-App Notifications", desc: "Stay updated on payments, expiring leases, and maintenance requests." },
        { title: "Read Receipts", desc: "Know when messages have been seen by tenants or team members." },
        { title: "Team Messaging", desc: "Internal communication between landlords, managers, and finance teams." },
        { title: "Bulk Announcements", desc: "Send updates to all tenants or specific property groups at once." },
      ],
    },
    {
      title: "Security & Access Control",
      icon: "fa-solid fa-shield-halved",
      items: [
        { title: "Role-Based Access", desc: "Landlord, manager, finance, tenant, and system roles with scoped permissions." },
        { title: "Audit Logs", desc: "Full history of every change made across the platform." },
        { title: "Secure Authentication", desc: "JWT-based login with refresh tokens, password policies, and brute-force protection." },
        { title: "Data Backups", desc: "Automated daily backups with 7-day retention for peace of mind." },
      ],
    },
  ];

  return (
    <>
      <SEO
        title="Features — AlphaOne Rental Property Management"
        description="Explore AlphaOne features: property management, tenant tracking, rent collection, financial reports, maintenance tickets, and more."
        canonical="https://alphaone.africa/features"
      />

      <section className="features-hero">
        <div className="container">
          <h1>Powerful features, simple experience</h1>
          <p>
            Every tool you need to run a modern property business — from rent collection to financial reporting — designed for East African landlords and managers.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container">
          {categories.map((cat, idx) => (
            <div className="feature-category" key={idx}>
              <h3><i className={cat.icon}></i> {cat.title}</h3>
              <div className="feature-list">
                {cat.items.map((item, i) => (
                  <div className="feature-item" key={i}>
                    <i className="fa-solid fa-check" style={{ color: "var(--accent)" }}></i>
                    <div>
                      <h4>{item.title}</h4>
                      <p>{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="cta-section">
        <div className="container">
          <span className="section-tag" style={{ color: "var(--light-accent)", background: "rgba(255,255,255,0.1)" }}>Get Started</span>
          <h2>See AlphaOne in action</h2>
          <p>Start your free trial today and explore every feature with sample data.</p>
          <div className="cta-actions">
            <a href="/register" className="btn btn-white">Start Free Trial <i className="fa-solid fa-arrow-right"></i></a>
            <a href="/contact" className="btn btn-outline" style={{ borderColor: "rgba(255,255,255,0.4)", color: "#fff" }}>Book a Demo</a>
          </div>
        </div>
      </section>
    </>
  );
}
