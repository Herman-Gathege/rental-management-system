// // frontend/src/features/home/Home.jsx



import { useNavigate } from "react-router-dom";
import SEO from "../components/SEO";

export default function Home() {
  const navigate = useNavigate();

  const features = [
    {
      title: "Track Rent Payments",
      desc: "Monitor paid rent, overdue balances, and monthly income from one dashboard.",
      icon: "💰",
      color: "#2563eb",
    },
    {
      title: "Manage Tenants Easily",
      desc: "Store tenant records, lease details, documents, and occupancy history securely.",
      icon: "👥",
      color: "#24a5fb",
    },
    {
      title: "Organize Properties",
      desc: "Manage apartments, units, and multiple properties without spreadsheets.",
      icon: "🏢",
      color: "#16a34a",
    },
    {
      title: "Handle Operations Faster",
      desc: "Track inspections, maintenance, and property activity in one place.",
      icon: "🛠️",
      color: "#ef4444",
    },
  ];

  const stats = [
    { value: "2.4M+", label: "Rent Collected", icon: "💰" },
    { value: "94%", label: "Occupancy Rate", icon: "📈" },
    { value: "12K+", label: "Active Tenants", icon: "👥" },
    { value: "4.8★", label: "User Rating", icon: "⭐" },
  ];

  const benefits = [
    { icon: "⏱️", title: "Save Hours", desc: "Automate rent collection and reporting" },
    { icon: "🔒", title: "Secure Data", desc: "Bank-grade encryption for your records" },
    { icon: "⚡", title: "Lightning Fast", desc: "Real-time updates and insights" },
    { icon: "📦", title: "All-in-One", desc: "Everything you need in one place" },
  ];

  return (
    <>
      <SEO
        title="AlphaOne — Rental Property Management Platform for Kenya & East Africa"
        description="Streamline rent collection, tenant management, and property operations across Kenya and East Africa. The smart rental property management platform built for landlords, property managers, and tenants."
        canonical="https://alphaone.africa"
      />
      <div className="home">
      {/* ================= HERO ================= */}
      <section className="home-hero-modern">
        <div className="page-container home-hero-grid-modern">
          {/* LEFT */}
          <div className="home-hero-content-modern">
            <div className="hero-badge-modern">
              ✨ AI-Powered Rental Management
            </div>

            <h1 className="hero-title">
              The Modern Way to Manage
              <span className="gradient-text"> Rental Properties</span>
            </h1>

            <p className="hero-description-modern">
              Track rent, manage tenants, organize leases, and monitor property
              operations from one intelligent dashboard.
            </p>

            <div className="hero-actions">
              <button
                className="btn btn-primary hero-btn"
                onClick={() => navigate("/register")}
              >
                Start Free Trial →
              </button>

              <button
                className="btn btn-secondary hero-btn-secondary"
                onClick={() => navigate("/login")}
              >
                Sign In
              </button>
            </div>

            {/* QUICK STATS */}
            <div className="hero-stats">
              {stats.map((stat, idx) => (
                <div key={idx} className="hero-stat">
                  <div className="hero-stat-icon">{stat.icon}</div>
                  <div>
                    <div className="hero-stat-value">{stat.value}</div>
                    <div className="hero-stat-label">{stat.label}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT - DASHBOARD PREVIEW */}
          <div className="home-hero-visual">
            <div className="dashboard-preview-modern">
              <div className="dashboard-preview-header">
                <div className="dashboard-preview-title">
                  📊 <span>Dashboard Overview</span>
                </div>
                <div className="dashboard-preview-dots">
                  <span className="dot red"></span>
                  <span className="dot yellow"></span>
                  <span className="dot green"></span>
                </div>
              </div>

              <div className="dashboard-preview-body">
                <div className="dashboard-preview-grid">
                  <div className="preview-card">
                    <span className="preview-label">Total Rent</span>
                    <strong className="preview-value">KES 2.4M</strong>
                    <span className="preview-change positive">↑ 12.5%</span>
                  </div>
                  <div className="preview-card">
                    <span className="preview-label">Occupancy</span>
                    <strong className="preview-value">94%</strong>
                    <span className="preview-change positive">↑ 3.2%</span>
                  </div>
                  <div className="preview-card">
                    <span className="preview-label">Properties</span>
                    <strong className="preview-value">48</strong>
                    <span className="preview-change neutral">Active</span>
                  </div>
                  <div className="preview-card">
                    <span className="preview-label">Tenants</span>
                    <strong className="preview-value">156</strong>
                    <span className="preview-change positive">+12</span>
                  </div>
                </div>

                <div className="preview-chart">
                  <div className="chart-bar-container">
                    <div className="chart-bar" style={{ height: "65%" }}></div>
                    <div className="chart-bar" style={{ height: "45%" }}></div>
                    <div className="chart-bar" style={{ height: "80%" }}></div>
                    <div className="chart-bar" style={{ height: "55%" }}></div>
                    <div className="chart-bar" style={{ height: "90%" }}></div>
                    <div className="chart-bar" style={{ height: "70%" }}></div>
                    <div className="chart-bar" style={{ height: "50%" }}></div>
                  </div>
                  <div className="chart-labels">
                    <span>Mon</span>
                    <span>Tue</span>
                    <span>Wed</span>
                    <span>Thu</span>
                    <span>Fri</span>
                    <span>Sat</span>
                    <span>Sun</span>
                  </div>
                </div>

                <div className="preview-recent">
                  <div className="recent-item">
                    <span className="recent-dot paid"></span>
                    <span className="recent-text">Rent paid - Unit 4B</span>
                    <span className="recent-time">2 min ago</span>
                  </div>
                  <div className="recent-item">
                    <span className="recent-dot alert"></span>
                    <span className="recent-text">Maintenance request</span>
                    <span className="recent-time">15 min ago</span>
                  </div>
                  <div className="recent-item">
                    <span className="recent-dot paid"></span>
                    <span className="recent-text">New tenant signed</span>
                    <span className="recent-time">1 hour ago</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= BENEFITS STRIP ================= */}
      <section className="benefits-strip">
        <div className="page-container">
          <div className="benefits-grid">
            {benefits.map((benefit, idx) => (
              <div key={idx} className="benefit-item">
                <div className="benefit-icon">{benefit.icon}</div>
                <div>
                  <h4>{benefit.title}</h4>
                  <p className="text-muted">{benefit.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= FEATURES ================= */}
      <section className="home-features-modern">
        <div className="page-container">
          <div className="section-header-modern text-center">
            <span className="section-tag">Features</span>
            <h2>Everything you need to manage rental properties</h2>
            <p className="text-muted">
              No spreadsheets. No scattered records. No manual chaos.
            </p>
          </div>

          <div className="home-feature-grid-modern">
            {features.map((feature) => (
              <div className="feature-card-modern" key={feature.title}>
                <div className="feature-icon-modern" style={{ color: feature.color }}>
                  {feature.icon}
                </div>
                <h3>{feature.title}</h3>
                <p className="text-muted">{feature.desc}</p>
                <div className="feature-link">
                  Learn more →
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= HOW IT WORKS ================= */}
      <section className="how-it-works">
        <div className="page-container">
          <div className="section-header-modern text-center">
            <span className="section-tag">Simple Setup</span>
            <h2>Get started in 3 easy steps</h2>
            <p className="text-muted">Start managing your properties in minutes.</p>
          </div>

          <div className="steps-grid">
            <div className="step-card">
              <div className="step-number-modern">1</div>
              <div className="step-icon">🏠</div>
              <h3>Add Your Properties</h3>
              <p className="text-muted">Create properties, units, and organize your portfolio.</p>
            </div>

            <div className="step-connector">
              <div className="connector-line"></div>
            </div>

            <div className="step-card">
              <div className="step-number-modern">2</div>
              <div className="step-icon">📄</div>
              <h3>Add Tenants & Leases</h3>
              <p className="text-muted">Store tenant records, lease agreements, and occupancy details.</p>
            </div>

            <div className="step-connector">
              <div className="connector-line"></div>
            </div>

            <div className="step-card">
              <div className="step-number-modern">3</div>
              <div className="step-icon">📊</div>
              <h3>Track & Optimize</h3>
              <p className="text-muted">Monitor payments, inspections, and property performance easily.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ================= TRUST SECTION ================= */}
      <section className="trust-section">
        <div className="page-container">
          <div className="trust-content">
            <div className="trust-left">
              <span className="section-tag">Trusted by landlords</span>
              <h2>Why property managers choose us</h2>
              <p className="text-muted">
                Join thousands of landlords who have transformed their property management workflow.
              </p>

              <div className="trust-checklist">
                {[
                  "Automated rent collection",
                  "Real-time financial insights",
                  "Secure document storage",
                  "24/7 customer support",
                ].map((item, idx) => (
                  <div key={idx} className="trust-check">
                    <span style={{ color: "#2563eb", fontSize: "20px" }}>✓</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>

              <button
                className="btn btn-primary"
                onClick={() => navigate("/register")}
              >
                Start Free Trial
              </button>
            </div>

            <div className="trust-right">
              <div className="testimonial-card">
                <div className="testimonial-quote">"</div>
                <p className="testimonial-text">
                  This platform has completely revolutionized how we manage our properties.
                  The dashboard gives us real-time insights we never had before.
                </p>
                <div className="testimonial-author">
                  <div className="testimonial-avatar">JD</div>
                  <div>
                    <div className="testimonial-name">John Doe</div>
                    <div className="testimonial-role">Portfolio Manager</div>
                  </div>
                </div>
              </div>

              <div className="trust-badge-grid">
                <div className="trust-badge">
                  <span style={{ fontSize: "24px" }}>🔒</span>
                  <span>Bank-grade security</span>
                </div>
                <div className="trust-badge">
                  <span style={{ fontSize: "24px" }}>☁️</span>
                  <span>Cloud-based</span>
                </div>
                <div className="trust-badge">
                  <span style={{ fontSize: "24px" }}>📱</span>
                  <span>Mobile ready</span>
                </div>
                <div className="trust-badge">
                  <span style={{ fontSize: "24px" }}>🎧</span>
                  <span>Dedicated support</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section className="home-cta-modern">
        <div className="page-container">
          <div className="cta-content">
            <div className="cta-text">
              <span className="section-tag" style={{ color: "#dbeafe" }}>Get Started</span>
              <h2>Ready to transform your property management?</h2>
              <p className="cta-description">
                Join thousands of landlords who are already using our platform to save time and grow their portfolio.
              </p>
            </div>
            <div className="cta-actions">
              <button
                className="btn btn-primary cta-btn-primary"
                onClick={() => navigate("/register")}
              >
                Start Free Trial →
              </button>
              <button
                className="btn cta-btn-secondary"
                onClick={() => navigate("/login")}
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="home-footer-modern">
        <div className="page-container">
          <div className="footer-grid">
            <div>
              <h3 className="footer-brand">Rental Property Management</h3>
              <p className="text-muted text-sm">
                Built for landlords and property managers who want to work smarter.
              </p>
            </div>

            <div>
              <h4>Product</h4>
              <ul>
                <li><a href="#">Features</a></li>
                <li><a href="#">Pricing</a></li>
                <li><a href="#">Integrations</a></li>
              </ul>
            </div>

            <div>
              <h4>Company</h4>
              <ul>
                <li><a href="#">About</a></li>
                <li><a href="#">Blog</a></li>
                <li><a href="#">Careers</a></li>
              </ul>
            </div>

            <div>
              <h4>Support</h4>
              <ul>
                <li><a href="#">Help Center</a></li>
                <li><a href="#">Contact</a></li>
                <li><a href="#">Privacy Policy</a></li>
              </ul>
            </div>
          </div>

          <div className="footer-bottom">
            <p className="text-sm text-muted">
              © {new Date().getFullYear()} Rental Property Management Platform. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
    </>
  );
}