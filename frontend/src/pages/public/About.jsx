import { useNavigate } from "react-router-dom";
import SEO from "../../components/SEO";
import PublicNavbar from "../../components/public/PublicNavbar";
import PublicFooter from "../../components/public/PublicFooter";
import styles from "./About.module.css";

const values = [
  {
    title: "Built for Africa",
    desc: "We understand the Kenyan and East African property market. AlphaOne is designed around local payment methods, workflows, and business realities.",
  },
  {
    title: "Simplicity First",
    desc: "Property management is complex enough. Our platform removes friction so you can focus on growing your portfolio, not fighting with software.",
  },
  {
    title: "Trust & Security",
    desc: "Your property and tenant data is sensitive. We use bank-grade encryption and industry-standard security to keep your information safe.",
  },
  {
    title: "Transparent Pricing",
    desc: "No hidden fees. No surprise charges. Clear, straightforward pricing that scales with your portfolio.",
  },
];

export default function About() {
  const navigate = useNavigate();

  return (
    <div className={styles.alphaPublicRoot}>
      <SEO
        title="About AlphaOne — Rental Property Management Platform"
        description="Learn about AlphaOne, the modern rental property management platform built for landlords, property managers, and tenants across Kenya and East Africa."
        canonical="https://alphaone.africa/about"
      />

      <PublicNavbar />

      {/* HERO */}
      <section className={styles.alphaPublicHero}>
        <div className={styles.alphaPublicSectionInner}>
          <span className={styles.alphaPublicSectionTag}>About Us</span>
          <h1 className={styles.alphaPublicHeroTitle}>
            Making property management <span className={styles.alphaPublicHeroAccent}>effortless</span>
          </h1>
          <p className={styles.alphaPublicHeroDesc}>
            AlphaOne was founded with a simple belief: managing rental properties in Africa should not require spreadsheets, dozens of phone calls, and sleepless nights.
          </p>
        </div>
      </section>

      {/* MISSION */}
      <section className={styles.alphaPublicMission}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicMissionGrid}>
            <div>
              <span className={styles.alphaPublicSectionTag}>Our Mission</span>
              <h2 className={styles.alphaPublicSectionTitle}>
                Empowering property professionals across Africa
              </h2>
            </div>
            <div>
              <p className={styles.alphaPublicMissionText}>
                We are on a mission to digitize property management across Kenya and East Africa. Too many landlords and property managers still rely on paper records, WhatsApp groups, and manual ledgers to run their businesses.
              </p>
              <p className={styles.alphaPublicMissionText}>
                AlphaOne replaces that chaos with a single, intelligent platform that handles properties, tenants, payments, leases, finances, and operations — all in one place.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* PROBLEM */}
      <section className={styles.alphaPublicProblem}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicProblemGrid}>
            <div>
              <span className={styles.alphaPublicSectionTag}>The Problem</span>
              <h2 className={styles.alphaPublicSectionTitle}>
                Property management is broken
              </h2>
              <p className={styles.alphaPublicProblemDesc}>
                Across Africa, property management is still largely manual. Landlords juggle multiple spreadsheets, property managers struggle with communication gaps, and tenants wait days for maintenance responses.
              </p>
              <ul className={styles.alphaPublicProblemList}>
                <li>Scattered records across phones, laptops, and paper</li>
                <li>Late payments and unclear financial visibility</li>
                <li>Communication breakdowns between owners, managers, and tenants</li>
                <li>No standardized way to track inspections or maintenance</li>
                <li>Time wasted on tasks that should be automated</li>
              </ul>
            </div>
            <div className={styles.alphaPublicProblemVisual}>
              <div className={styles.alphaPublicProblemCard}>
                <div className={styles.alphaPublicProblemCardIcon}>!</div>
                <div>
                  <strong>60% of property managers</strong>
                  <p className={styles.alphaPublicProblemCardDesc}>
                    still use spreadsheets as their primary management tool.
                  </p>
                </div>
              </div>
              <div className={styles.alphaPublicProblemCard}>
                <div className={styles.alphaPublicProblemCardIcon}>$</div>
                <div>
                  <strong>15-20% revenue loss</strong>
                  <p className={styles.alphaPublicProblemCardDesc}>
                    from uncollected rent and operational inefficiencies.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* VISION */}
      <section className={styles.alphaPublicVision}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicVisionContent}>
            <span className={styles.alphaPublicSectionTag}>Our Vision</span>
            <h2 className={styles.alphaPublicSectionTitle}>
              A connected, transparent, and efficient African property ecosystem
            </h2>
            <p className={styles.alphaPublicVisionText}>
              We envision a future where every landlord, property manager, and tenant in Africa has access to world-class property management tools. Where rent collection is seamless, records are always accurate, and communication is instant.
            </p>
            <p className={styles.alphaPublicVisionText}>
              AlphaOne is just the beginning. We are building the infrastructure for a modern African real estate industry.
            </p>
          </div>
        </div>
      </section>

      {/* VALUES */}
      <section className={styles.alphaPublicValues}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicSectionHeader}>
            <span className={styles.alphaPublicSectionTag}>Our Values</span>
            <h2 className={styles.alphaPublicSectionTitle}>
              The principles that guide us
            </h2>
          </div>

          <div className={styles.alphaPublicValuesGrid}>
            {values.map((value) => (
              <div key={value.title} className={styles.alphaPublicValueCard}>
                <h3 className={styles.alphaPublicValueTitle}>{value.title}</h3>
                <p className={styles.alphaPublicValueDesc}>{value.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className={styles.alphaPublicCta}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicCtaContent}>
            <h2 className={styles.alphaPublicCtaTitle}>Experience the AlphaOne difference</h2>
            <p className={styles.alphaPublicCtaDesc}>
              Join the forward-thinking property professionals already using our platform.
            </p>
            <div className={styles.alphaPublicCtaActions}>
              <button className={styles.alphaPublicBtnPrimary} onClick={() => navigate("/register")}>
                Get Started
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
              <button className={styles.alphaPublicBtnSecondary} onClick={() => navigate("/contact")}>
                Contact Us
              </button>
            </div>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
