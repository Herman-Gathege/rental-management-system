import { useNavigate } from "react-router-dom";
import SEO from "../../components/SEO";
import PublicNavbar from "../../components/public/PublicNavbar";
import PublicFooter from "../../components/public/PublicFooter";
import styles from "./Featured.module.css";

const capabilities = [
  {
    title: "Dashboard",
    desc: "Role-based dashboards with real-time metrics, rent summaries, occupancy rates, and actionable insights tailored to landlords, managers, finance teams, and tenants.",
    icon: "M3 3v18h18",
  },
  {
    title: "Property & Unit Management",
    desc: "Create and organize properties, add units, track vacancies, and manage amenities. All property data in one searchable, filterable interface.",
    icon: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
  },
  {
    title: "Tenant Management",
    desc: "Centralized tenant records, document storage, lease history, communication logs, and occupancy tracking per unit and property.",
    icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z",
  },
  {
    title: "Lease Management",
    desc: "Create leases, track terms, manage renewals, store agreements, and maintain a complete audit trail for every tenancy.",
    icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  },
  {
    title: "Rent & Payments",
    desc: "Automated payment tracking, receipt generation, late payment alerts, batch processing, and reconciliation tools for finance teams.",
    icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  },
  {
    title: "Finance & Expenses",
    desc: "Track income, manage expenses, categorize costs, and generate financial reports. Full visibility into property-level profitability.",
    icon: "M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z",
  },
  {
    title: "Maintenance & Tickets",
    desc: "Log maintenance requests, assign tasks, track status, and ensure timely resolution. Keep tenants and owners informed at every step.",
    icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
  },
  {
    title: "Reports & Analytics",
    desc: "Generate comprehensive reports on occupancy, revenue, expenses, and tenant activity. Export data for accounting and decision-making.",
    icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  },
  {
    title: "Team & Permissions",
    desc: "Invite staff, assign roles, and control access with granular permissions. Landlords, managers, and finance staff each see only what they need.",
    icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z",
  },
  {
    title: "Inspections",
    desc: "Schedule and conduct property inspections, record findings, attach photos, and track follow-up actions for each unit.",
    icon: "M15 12a3 3 0 11-6 0 3 3 0 016 0z",
  },
  {
    title: "Bulk Uploads",
    desc: "Import properties, units, and tenants in bulk using spreadsheets. Save hours of manual data entry during onboarding.",
    icon: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12",
  },
  {
    title: "Notifications",
    desc: "Stay informed with real-time alerts for rent due, maintenance updates, lease expirations, and payment confirmations.",
    icon: "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9",
  },
];

const dashboardCards = [
  { label: "Total Rent", value: "KES 2.4M", change: "+12.5%" },
  { label: "Occupancy", value: "94%", change: "+3.2%" },
  { label: "Properties", value: "48", change: "Active" },
  { label: "Tenants", value: "156", change: "+12" },
];

export default function Featured() {
  const navigate = useNavigate();

  return (
    <div className={styles.alphaPublicRoot}>
      <SEO
        title="AlphaOne Features — Rental Property Management Capabilities for Kenya & East Africa"
        description="Explore AlphaOne's rental property management capabilities: properties, tenants, leases, payments, finance, reports, tickets, inspections, and team management."
        canonical="https://alphaone.africa/featured"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          "@id": "https://alphaone.africa/featured/#collectionpage",
          "url": "https://alphaone.africa/featured",
          "name": "AlphaOne Features — Rental Property Management Capabilities for Kenya & East Africa",
          "description": "Explore AlphaOne's full suite of property management capabilities: properties, tenants, leases, payments, finance, reports, tickets, inspections, and team management.",
          "isPartOf": {
            "@id": "https://alphaone.africa/#website"
          },
          "about": {
            "@id": "https://alphaone.africa/#organization"
          },
          "breadcrumb": {
            "@type": "BreadcrumbList",
            "itemListElement": [
              {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": "https://alphaone.africa/"
              },
              {
                "@type": "ListItem",
                "position": 2,
                "name": "Features",
                "item": "https://alphaone.africa/featured"
              }
            ]
          }
        }}
      />

      <PublicNavbar />

      {/* HERO */}
      <section className={styles.alphaPublicHero}>
        <div className={styles.alphaPublicSectionInner}>
          <span className={styles.alphaPublicSectionTag}>Product Showcase</span>
          <h1 className={styles.alphaPublicHeroTitle}>
            A platform built for <span className={styles.alphaPublicHeroAccent}>serious</span> property operations
          </h1>
          <p className={styles.alphaPublicHeroDesc}>
            Every capability you need to manage properties, tenants, payments, and teams unified in one powerful platform.
          </p>
        </div>
      </section>

      {/* DASHBOARD SHOWCASE */}
      <section className={styles.alphaPublicShowcase}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicShowcaseHeader}>
            <span className={styles.alphaPublicSectionTag}>Dashboard</span>
            <h2 className={styles.alphaPublicSectionTitle}>Your command center</h2>
            <p className={styles.alphaPublicSectionDesc}>
              A role-aware dashboard that surfaces the metrics that matter most to you.
            </p>
          </div>

          <div className={styles.alphaPublicShowcaseVisual}>
            <div className={styles.alphaPublicShowcaseCard}>
              <div className={styles.alphaPublicShowcaseCardHeader}>
                <div className={styles.alphaPublicShowcaseCardTitle}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 3v18h18" />
                    <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3" />
                  </svg>
                  Dashboard Overview
                </div>
                <div className={styles.alphaPublicShowcaseCardDots}>
                  <span className={`${styles.alphaPublicDot} ${styles.alphaPublicDotRed}`}></span>
                  <span className={`${styles.alphaPublicDot} ${styles.alphaPublicDotYellow}`}></span>
                  <span className={`${styles.alphaPublicDot} ${styles.alphaPublicDotGreen}`}></span>
                </div>
              </div>
              <div className={styles.alphaPublicShowcaseCardBody}>
                <div className={styles.alphaPublicShowcaseGrid}>
                  {dashboardCards.map((card) => (
                    <div key={card.label} className={styles.alphaPublicShowcaseStatCard}>
                      <span className={styles.alphaPublicShowcaseStatLabel}>{card.label}</span>
                      <strong className={styles.alphaPublicShowcaseStatValue}>{card.value}</strong>
                      <span className={`${styles.alphaPublicShowcaseStatChange} ${card.change.startsWith("+") || card.change === "Active" ? styles.alphaPublicShowcaseStatChangePositive : ""}`}>{card.change}</span>
                    </div>
                  ))}
                </div>
                <div className={styles.alphaPublicShowcaseChart}>
                  <div className={styles.alphaPublicShowcaseChartBars}>
                    {[65, 45, 80, 55, 90, 70, 50].map((h, i) => (
                      <div key={i} className={styles.alphaPublicShowcaseChartBar} style={{ height: `${h}%` }} />
                    ))}
                  </div>
                  <div className={styles.alphaPublicShowcaseChartLabels}>
                    {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => (
                      <span key={d}>{d}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CAPABILITIES */}
      <section className={styles.alphaPublicCapabilities}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicSectionHeader}>
            <span className={styles.alphaPublicSectionTag}>Capabilities</span>
            <h2 className={styles.alphaPublicSectionTitle}>
              Everything in one platform
            </h2>
            <p className={styles.alphaPublicSectionDesc}>
              From properties to payments, AlphaOne covers the full property management lifecycle.
            </p>
          </div>

          <div className={styles.alphaPublicCapabilitiesGrid}>
            {capabilities.map((cap) => (
              <div key={cap.title} className={styles.alphaPublicCapabilityCard}>
                <div className={styles.alphaPublicCapabilityIcon}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d={cap.icon} />
                  </svg>
                </div>
                <h3 className={styles.alphaPublicCapabilityTitle}>{cap.title}</h3>
                <p className={styles.alphaPublicCapabilityDesc}>{cap.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className={styles.alphaPublicCta}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicCtaContent}>
            <h2 className={styles.alphaPublicCtaTitle}>See AlphaOne in action</h2>
            <p className={styles.alphaPublicCtaDesc}>
              Experience the platform trusted by property professionals across Kenya and East Africa.
            </p>
            <div className={styles.alphaPublicCtaActions}>
              <button className={styles.alphaPublicBtnPrimary} onClick={() => navigate("/register")}>
                Start Free Trial
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
              <button className={styles.alphaPublicBtnSecondary} onClick={() => navigate("/contact")}>
                Contact Sales
              </button>
            </div>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
