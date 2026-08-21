import { useNavigate } from "react-router-dom";
import SEO from "../../components/SEO";
import PublicNavbar from "../../components/public/PublicNavbar";
import PublicFooter from "../../components/public/PublicFooter";
import logo from "../../assets/aplha1_logo_.png";
import styles from "./PublicHome.module.css";

const features = [
  {
    title: "Property Management",
    desc: "Organize apartments, units, and multiple properties from a single intelligent dashboard.",
    icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
  },
  {
    title: "Tenant Management",
    desc: "Store tenant records, lease details, documents, and occupancy history securely.",
    icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
  },
  {
    title: "Rent & Payments",
    desc: "Automate rent collection, track payments, and reconcile finances with full transparency.",
    icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  },
  {
    title: "Lease Management",
    desc: "Create, track, and manage lease agreements with automated renewals and document storage.",
    icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  },
  {
    title: "Maintenance & Tickets",
    desc: "Track inspections, maintenance requests, and property activity in one organized place.",
    icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
  },
  {
    title: "Reports & Insights",
    desc: "Get real-time financial insights, occupancy rates, and performance analytics.",
    icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  },
];

const stats = [
  { value: "2.4M+", label: "Rent Collected", suffix: "KES" },
  { value: "94%", label: "Occupancy Rate" },
  { value: "12K+", label: "Active Tenants" },
  { value: "4.8/5", label: "User Rating" },
];

const steps = [
  {
    num: "01",
    title: "Add Your Properties",
    desc: "Create properties, units, and organize your portfolio in minutes.",
  },
  {
    num: "02",
    title: "Add Tenants & Leases",
    desc: "Store tenant records, lease agreements, and occupancy details.",
  },
  {
    num: "03",
    title: "Track & Optimize",
    desc: "Monitor payments, inspections, and property performance effortlessly.",
  },
];

const roles = [
  { title: "Landlords", desc: "Manage your entire portfolio, collect rent, and track performance." },
  { title: "Property Managers", desc: "Oversee assigned properties, tenants, and maintenance operations." },
  { title: "Finance Teams", desc: "Reconcile payments, manage expenses, and generate financial reports." },
  { title: "Tenants", desc: "Pay rent, submit maintenance requests, and access lease documents." },
];

export default function PublicHome() {
  const navigate = useNavigate();

  return (
    <div className={styles.alphaPublicRoot}>
      <SEO
        title="AlphaOne | Rental Property Management Platform for Kenya & East Africa"
        description="AlphaOne is the rental property management platform for landlords, property managers, and tenants across Kenya and East Africa. Streamline rent collection, tenant management, and property operations."
        canonical="https://alphaone.africa/"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "WebPage",
          "@id": "https://alphaone.africa/#webpage",
          "url": "https://alphaone.africa/",
          "name": "AlphaOne | Rental Property Management Platform for Kenya & East Africa",
          "description": "Streamline rent collection, tenant management, and property operations across Kenya and East Africa. The smart rental property management platform built for landlords, property managers, and tenants.",
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
              }
            ]
          }
        }}
      />

      <PublicNavbar />

      {/* ================= HERO ================= */}
      <section className={styles.alphaPublicHero}>
        <div className={styles.alphaPublicHeroInner}>
          <div className={styles.alphaPublicHeroContent}>
            {/* <img src={logo} alt="AlphaOne" className={styles.alphaPublicHeroLogo} /> */}

            <div className={styles.alphaPublicHeroBadge}>
              Built for Kenya & East Africa
            </div>

            <h1 className={styles.alphaPublicHeroTitle}>
              The modern way to manage{" "}
              <span className={styles.alphaPublicHeroTitleAccent}>rental properties</span>
            </h1>

            <p className={styles.alphaPublicHeroDesc}>
              Track rent, manage tenants, organize leases, and monitor property
              operations from one intelligent platform. No spreadsheets. No chaos.
            </p>

            <div className={styles.alphaPublicHeroActions}>
              <button className={styles.alphaPublicBtnPrimary} onClick={() => navigate("/register")}>
                Get Started
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
              <button className={styles.alphaPublicBtnSecondary} onClick={() => navigate("/login")}>
                Sign In
              </button>
            </div>

            <div className={styles.alphaPublicHeroStats}>
              {stats.map((stat, idx) => (
                <div key={idx} className={styles.alphaPublicHeroStat}>
                  <div className={styles.alphaPublicHeroStatValue}>
                    {stat.suffix && <span className={styles.alphaPublicHeroStatSuffix}>{stat.suffix}</span>}
                    {stat.value}
                  </div>
                  <div className={styles.alphaPublicHeroStatLabel}>{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.alphaPublicHeroVisual}>
            <div className={styles.alphaPublicDashboard}>
              <div className={styles.alphaPublicDashboardHeader}>
                <div className={styles.alphaPublicDashboardTitle}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 3v18h18" />
                    <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3" />
                  </svg>
                  Dashboard Overview
                </div>
                <div className={styles.alphaPublicDashboardDots}>
                  <span className={`${styles.alphaPublicDot} ${styles.alphaPublicDotRed}`}></span>
                  <span className={`${styles.alphaPublicDot} ${styles.alphaPublicDotYellow}`}></span>
                  <span className={`${styles.alphaPublicDot} ${styles.alphaPublicDotGreen}`}></span>
                </div>
              </div>
              <div className={styles.alphaPublicDashboardBody}>
                <div className={styles.alphaPublicDashboardGrid}>
                  <div className={styles.alphaPublicPreviewCard}>
                    <span className={styles.alphaPublicPreviewLabel}>Total Rent</span>
                    <strong className={styles.alphaPublicPreviewValue}>KES 2.4M</strong>
                    <span className={`${styles.alphaPublicPreviewChange} ${styles.alphaPublicPreviewChangePositive}`}>+12.5%</span>
                  </div>
                  <div className={styles.alphaPublicPreviewCard}>
                    <span className={styles.alphaPublicPreviewLabel}>Occupancy</span>
                    <strong className={styles.alphaPublicPreviewValue}>94%</strong>
                    <span className={`${styles.alphaPublicPreviewChange} ${styles.alphaPublicPreviewChangePositive}`}>+3.2%</span>
                  </div>
                  <div className={styles.alphaPublicPreviewCard}>
                    <span className={styles.alphaPublicPreviewLabel}>Properties</span>
                    <strong className={styles.alphaPublicPreviewValue}>48</strong>
                    <span className={styles.alphaPublicPreviewChange}>Active</span>
                  </div>
                  <div className={styles.alphaPublicPreviewCard}>
                    <span className={styles.alphaPublicPreviewLabel}>Tenants</span>
                    <strong className={styles.alphaPublicPreviewValue}>156</strong>
                    <span className={`${styles.alphaPublicPreviewChange} ${styles.alphaPublicPreviewChangePositive}`}>+12</span>
                  </div>
                </div>

                <div className={styles.alphaPublicPreviewChart}>
                  <div className={styles.alphaPublicChartBars}>
                    {[65, 45, 80, 55, 90, 70, 50].map((h, i) => (
                      <div key={i} className={styles.alphaPublicChartBar} style={{ height: `${h}%` }} />
                    ))}
                  </div>
                  <div className={styles.alphaPublicChartLabels}>
                    {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => (
                      <span key={d}>{d}</span>
                    ))}
                  </div>
                </div>

                <div className={styles.alphaPublicPreviewActivity}>
                  <div className={styles.alphaPublicActivityItem}>
                    <span className={`${styles.alphaPublicActivityDot} ${styles.alphaPublicActivityDotPaid}`} />
                    <span className={styles.alphaPublicActivityText}>Rent paid — Unit 4B</span>
                    <span className={styles.alphaPublicActivityTime}>2 min ago</span>
                  </div>
                  <div className={styles.alphaPublicActivityItem}>
                    <span className={`${styles.alphaPublicActivityDot} ${styles.alphaPublicActivityDotAlert}`} />
                    <span className={styles.alphaPublicActivityText}>Maintenance request</span>
                    <span className={styles.alphaPublicActivityTime}>15 min ago</span>
                  </div>
                  <div className={styles.alphaPublicActivityItem}>
                    <span className={`${styles.alphaPublicActivityDot} ${styles.alphaPublicActivityDotPaid}`} />
                    <span className={styles.alphaPublicActivityText}>New tenant signed</span>
                    <span className={styles.alphaPublicActivityTime}>1 hour ago</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= TRUST / POSITIONING ================= */}
      <section className={styles.alphaPublicTrust}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicTrustGrid}>
            <div>
              <span className={styles.alphaPublicSectionTag}>Trusted Platform</span>
              <h2 className={styles.alphaPublicSectionTitle}>
                Built for the African property market
              </h2>
              <p className={styles.alphaPublicSectionDesc}>
                Property management in Kenya and East Africa comes with unique challenges — informal payments, scattered records, and fragmented communication. AlphaOne was designed from the ground up to solve these problems.
              </p>
            </div>
            <div className={styles.alphaPublicTrustRight}>
              <div className={styles.alphaPublicTrustCard}>
                <div className={styles.alphaPublicTrustCardIcon}>M</div>
                <div>
                  <strong>Mobile-First</strong>
                  <p className={styles.alphaPublicTrustCardDesc}>Works perfectly on any device, anywhere.</p>
                </div>
              </div>
              <div className={styles.alphaPublicTrustCard}>
                <div className={styles.alphaPublicTrustCardIcon}>K</div>
                <div>
                  <strong>Kenya-Ready</strong>
                  <p className={styles.alphaPublicTrustCardDesc}>M-Pesa, KRA, and local compliance built in.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= FEATURES ================= */}
      <section className={styles.alphaPublicFeatures}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicSectionHeader}>
            <span className={styles.alphaPublicSectionTag}>Capabilities</span>
            <h2 className={styles.alphaPublicSectionTitle}>
              Everything you need to manage rental properties
            </h2>
            <p className={styles.alphaPublicSectionDesc}>
              One platform for properties, tenants, payments, finances, and operations.
            </p>
          </div>

          <div className={styles.alphaPublicFeatureGrid}>
            {features.map((feature) => (
              <div key={feature.title} className={styles.alphaPublicFeatureCard}>
                <div className={styles.alphaPublicFeatureIcon}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d={feature.icon} />
                  </svg>
                </div>
                <h3 className={styles.alphaPublicFeatureTitle}>{feature.title}</h3>
                <p className={styles.alphaPublicFeatureDesc}>{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= HOW IT WORKS ================= */}
      <section className={styles.alphaPublicHow}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicSectionHeader}>
            <span className={styles.alphaPublicSectionTag}>How It Works</span>
            <h2 className={styles.alphaPublicSectionTitle}>
              Get started in three simple steps
            </h2>
            <p className={styles.alphaPublicSectionDesc}>
              Launch your property management workflow in minutes.
            </p>
          </div>

          <div className={styles.alphaPublicStepsGrid}>
            {steps.map((step, idx) => (
              <div key={step.num} className={styles.alphaPublicStepCard}>
                <div className={styles.alphaPublicStepNum}>{step.num}</div>
                <h3 className={styles.alphaPublicStepTitle}>{step.title}</h3>
                <p className={styles.alphaPublicStepDesc}>{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= WHO IT'S FOR ================= */}
      <section className={styles.alphaPublicRoles}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicSectionHeader}>
            <span className={styles.alphaPublicSectionTag}>Who It&apos;s For</span>
            <h2 className={styles.alphaPublicSectionTitle}>
              Built for every role in property management
            </h2>
            <p className={styles.alphaPublicSectionDesc}>
              Whether you own, manage, finance, or occupy properties, AlphaOne has a tailored experience.
            </p>
          </div>

          <div className={styles.alphaPublicRolesGrid}>
            {roles.map((role) => (
              <div key={role.title} className={styles.alphaPublicRoleCard}>
                <h3 className={styles.alphaPublicRoleTitle}>{role.title}</h3>
                <p className={styles.alphaPublicRoleDesc}>{role.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section className={styles.alphaPublicCta}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicCtaContent}>
            <h2 className={styles.alphaPublicCtaTitle}>
              Ready to transform your property management?
            </h2>
            <p className={styles.alphaPublicCtaDesc}>
              Join landlords and property managers across Kenya who are already using AlphaOne.
            </p>
            <div className={styles.alphaPublicCtaActions}>
              <button className={styles.alphaPublicBtnPrimary} onClick={() => navigate("/register")}>
                Start Free Trial
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
              <button className={styles.alphaPublicBtnSecondary} onClick={() => navigate("/login")}>
                Sign In
              </button>
            </div>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
