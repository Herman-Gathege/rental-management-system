import { useNavigate } from "react-router-dom";
import SEO from "../components/SEO";
import logo from "../assets/hero-1.png";

export default function Home() {
  const navigate = useNavigate();

  const features = [
    {
      title: "Track Rent Payments",
      desc: "Monitor paid rent, overdue balances, and monthly income from one AlphaOne dashboard.",
      icon: "fa-solid fa-money-bill-wave",
    },
    {
      title: "Manage Tenants Easily",
      desc: "Store tenant records, lease details, documents, and occupancy history securely.",
      icon: "fa-solid fa-users",
    },
    {
      title: "Organize Properties",
      desc: "Manage apartments, units, and multiple properties without spreadsheets.",
      icon: "fa-solid fa-building",
    },
    {
      title: "Handle Operations Faster",
      desc: "Track inspections, maintenance, and property activity in one place.",
      icon: "fa-solid fa-clipboard-check",
    },
  ];

  const stats = [
    { value: "2.4M+", label: "Rent Collected" },
    { value: "94%", label: "Occupancy Rate" },
    { value: "12K+", label: "Active Tenants" },
    { value: "4.8/5", label: "User Rating" },
  ];

  const benefits = [
    { icon: "fa-solid fa-clock", title: "Save Hours Every Week", desc: "Automate rent collection, invoicing, and follow-ups so your team can focus on what matters." },
    { icon: "fa-solid fa-shield-halved", title: "Bank-Grade Security", desc: "Your data is encrypted and protected with the same standards used by leading financial institutions." },
    { icon: "fa-solid fa-bolt", title: "Real-Time Insights", desc: "See collections, occupancy, and cash flow update instantly across your portfolio." },
    { icon: "fa-solid fa-layer-group", title: "All-in-One Platform", desc: "Properties, tenants, leases, payments, expenses, and reports in one connected system." },
  ];

  return (
    <>
      <SEO
        title="AlphaOne — Rental Property Management Platform for Kenya & East Africa"
        description="Streamline rent collection, tenant management, and property operations across Kenya and East Africa. The smart rental property management platform built for landlords, property managers, and tenants."
        canonical="https://alphaone.africa"
      />

      {/* HERO */}
      <section className="parallax-hero">
        <div className="hero-overlay"></div>
        <div className="container">
          <div className="hero-grid">
            <div className="hero-content">
              <div className="hero-badge">
                <i className="fa-solid fa-star"></i> Trusted by 12,000+ tenants
              </div>
              <h1>Property Management That Actually Works</h1>
              <p>
                From rent collection to lease renewals, AlphaOne gives landlords and property managers the tools to run a tighter, more profitable portfolio.
              </p>
              <div className="hero-buttons">
                <button className="btn btn-primary" onClick={() => navigate("/register")}>
                  Start Free Trial <i className="fa-solid fa-arrow-right"></i>
                </button>
                <button className="btn btn-outline" onClick={() => navigate("/features")}>
                  Explore Features
                </button>
              </div>
              {/* <div className="hero-stats">
                {stats.map((stat, idx) => (
                  <div className="stat" key={idx}>
                    <div className="count">{stat.value}</div>
                    <p>{stat.label}</p>
                  </div>
                ))}
              </div> */}
            </div>
            <div className="hero-image">
              <img src={logo} alt="AlphaOne Dashboard Preview" />
            </div>
          </div>
        </div>
      </section>

      {/* BENEFITS STRIP */}
      <section className="section" style={{ background: "#fff", borderBottom: "1px solid var(--border)" }}>
        <div className="container">
          <div className="benefits-grid">
            {benefits.map((benefit, idx) => (
              <div className="benefit-item" key={idx}>
                <div className="benefit-icon">
                  <i className={benefit.icon}></i>
                </div>
                <div>
                  <h4>{benefit.title}</h4>
                  <p>{benefit.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="section">
        <div className="container">
          <div className="section-header">
            <span className="section-tag">Features</span>
            <h2>Everything you need to manage rental properties</h2>
            <p>No spreadsheets. No scattered records. No manual chaos. One platform built for how you actually work.</p>
          </div>
          <div className="services-grid">
            {features.map((feature) => (
              <div className="service-card" key={feature.title}>
                <div className="card-icon">
                  <i className={feature.icon}></i>
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.desc}</p>
                <span className="card-link">Learn more <i className="fa-solid fa-arrow-right"></i></span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="section" style={{ background: "#fff" }}>
        <div className="container">
          <div className="section-header">
            <span className="section-tag">Simple Setup</span>
            <h2>Get started with AlphaOne in 3 easy steps</h2>
            <p>Start managing your properties in minutes, not months.</p>
          </div>
          <div className="steps-grid">
            <div className="step-card">
              <div className="step-number">1</div>
              <div className="step-icon"><i className="fa-solid fa-plus"></i></div>
              <h3>Add Your Properties</h3>
              <p>Create properties, add units, and organize your portfolio in a few clicks.</p>
            </div>
            <div className="step-card">
              <div className="step-number">2</div>
              <div className="step-icon"><i className="fa-solid fa-file-signature"></i></div>
              <h3>Add Tenants & Leases</h3>
              <p>Store tenant records, lease agreements, and occupancy details in one place.</p>
            </div>
            <div className="step-card">
              <div className="step-number">3</div>
              <div className="step-icon"><i className="fa-solid fa-chart-line"></i></div>
              <h3>Track & Optimize</h3>
              <p>Monitor payments, inspections, and property performance with real-time reports.</p>
            </div>
          </div>
        </div>
      </section>

      {/* TRUST / TESTIMONIALS */}
      <section className="testimonials">
        <div className="container">
          <div className="section-header">
            <span className="section-tag">Testimonials</span>
            <h2>Trusted by property managers across Kenya</h2>
            <p>See why landlords and managers are switching to AlphaOne.</p>
          </div>
          <div className="testimonials-grid">
            <div className="testimonial-card">
              <p className="testimonial-text">
                "AlphaOne has completely revolutionized how we manage our properties. The dashboard gives us real-time insights we never had before."
              </p>
              <div className="testimonial-author">
                <strong>James Mwangi</strong> &mdash; Portfolio Manager, Nairobi
              </div>
            </div>
            <div className="testimonial-card">
              <p className="testimonial-text">
                "We cut our rent collection follow-up time by 70%. The payment tracking and automated reminders are a game changer."
              </p>
              <div className="testimonial-author">
                <strong>Sarah Kimani</strong> &mdash; Property Manager, Karen
              </div>
            </div>
            <div className="testimonial-card">
              <p className="testimonial-text">
                "Finally, a system that works for East African landlords. M-Pesa integration and local support make all the difference."
              </p>
              <div className="testimonial-author">
                <strong>David Ochieng</strong> &mdash; Landlord, Kisumu
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <div className="container">
          <span className="section-tag" style={{ color: "var(--light-accent)", background: "rgba(255,255,255,0.1)" }}>Get Started</span>
          <h2>Ready to transform your property management?</h2>
          <p>Join thousands of landlords and property managers who are already using AlphaOne to save time and grow their portfolio.</p>
          <div className="cta-actions">
            <button className="btn btn-white" onClick={() => navigate("/register")}>
              Start Free Trial <i className="fa-solid fa-arrow-right"></i>
            </button>
            <button className="btn btn-outline" style={{ borderColor: "rgba(255,255,255,0.4)", color: "#fff" }} onClick={() => navigate("/contact")}>
              Talk to Sales
            </button>
          </div>
        </div>
      </section>
    </>
  );
}
