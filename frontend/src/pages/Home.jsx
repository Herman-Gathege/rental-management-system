// // frontend/src/features/home/Home.jsx

// import { useNavigate } from "react-router-dom";

// export default function Home() {
//   const navigate = useNavigate();

//   const features = [
//     {
//       title: "Track Rent Payments",
//       desc: "Monitor paid rent, overdue balances, and monthly income from one dashboard.",
//       icon: "💰",
//     },
//     {
//       title: "Manage Tenants Easily",
//       desc: "Store tenant records, lease details, documents, and occupancy history securely.",
//       icon: "👥",
//     },
//     {
//       title: "Organize Properties",
//       desc: "Manage apartments, units, and multiple properties without spreadsheets.",
//       icon: "🏢",
//     },
//     {
//       title: "Handle Operations Faster",
//       desc: "Track inspections, maintenance, and property activity in one place.",
//       icon: "🛠️",
//     },
//   ];

//   const reasons = [
//     "Reduce manual paperwork",
//     "Track rent arrears instantly",
//     "Centralize property operations",
//     "Improve team coordination",
//   ];

//   const highlights = [
//     "Rent Tracking",
//     "Tenant Records",
//     "Lease Management",
//     "Property Insights",
//   ];

//   return (
//     <div className="home">
//       {/* ================= HERO ================= */}
//       <section className="home-hero">
//         <div className="page-container home-hero-grid">
//           {/* LEFT */}
//           <div className="home-hero-content">
//             <div className="hero-badge">
//               Modern Rental Property Management Platform
//             </div>

//             <h1>
//               Everything landlords need to manage{" "}
//               <span className="company-blue">rental properties</span>
//             </h1>

//             <p className="text-muted hero-description">
//               Track rent, manage tenants, organize leases, and monitor property
//               operations from one simple dashboard.
//             </p>

//             <div className="flex gap-md mt-lg flex-mobile-col">
//               {/* <button
//                 className="btn btn-primary"
//                 onClick={() => navigate("/register")}
//               >
//                 Get Started
//               </button> */}

//               <button
//                 className="btn btn-secondary"
//                 onClick={() => navigate("/login")}
//               >
//                 Sign In
//               </button>
//             </div>

//             {/* QUICK VALUE POINTS */}
//             <div className="hero-highlights mt-lg">
//               {highlights.map((item) => (
//                 <div key={item} className="highlight-pill">
//                   ✔ {item}
//                 </div>
//               ))}
//             </div>
//           </div>

//           {/* RIGHT */}
//           <div className="hidden-mobile">
//             <div className="card dashboard-preview">
//               <div className="dashboard-preview-header">
//                 <div className="dashboard-dot red"></div>
//                 <div className="dashboard-dot yellow"></div>
//                 <div className="dashboard-dot green"></div>
//               </div>

//               <div className="dashboard-preview-body">
//                 <div className="dashboard-cards">
//                   <div className="mini-card">
//                     <span>Collected Rent</span>
//                     <strong>KES 2.4M</strong>
//                   </div>

//                   <div className="mini-card">
//                     <span>Occupied Units</span>
//                     <strong>84%</strong>
//                   </div>
//                 </div>

//                 <div className="dashboard-chart"></div>

//                 <div className="dashboard-table">
//                   <div className="table-row"></div>
//                   <div className="table-row"></div>
//                   <div className="table-row"></div>
//                   <div className="table-row"></div>
//                 </div>
//               </div>
//             </div>
//           </div>
//         </div>
//       </section>

//       {/* ================= WHY LANDLORDS LOVE IT ================= */}
//       <section className="home-trust">
//         <div className="page-container">
//           <div className="section-header text-center">
//             <h2>Why landlords choose our platform</h2>

//             <p className="text-muted">
//               Built to simplify daily rental property operations.
//             </p>
//           </div>

//           <div className="home-feature-grid">
//             {reasons.map((reason) => (
//               <div className="card card-w text-center" key={reason}>
//                 <h3>{reason}</h3>
//               </div>
//             ))}
//           </div>
//         </div>
//       </section>

//       {/* ================= FEATURES ================= */}
//       <section className="home-features">
//         <div className="page-container">
//           <div className="section-header text-center">
//             <h2>Manage your entire rental business from one place</h2>

//             <p className="text-muted">
//               No spreadsheets. No scattered records. No manual chaos.
//             </p>
//           </div>

//           <div className="home-feature-grid">
//             {features.map((feature) => (
//               <div className="card card-w" key={feature.title}>
//                 <div className="feature-icon">{feature.icon}</div>

//                 <h3>{feature.title}</h3>

//                 <p className="text-muted">{feature.desc}</p>
//               </div>
//             ))}
//           </div>
//         </div>
//       </section>

//       {/* ================= SIMPLE WORKFLOW ================= */}
//       <section className="home-steps">
//         <div className="page-container">
//           <div className="section-header text-center">
//             <h2>Simple setup. Powerful management.</h2>

//             <p className="text-muted">
//               Start managing your properties in minutes.
//             </p>
//           </div>

//           <div className="home-step-grid">
//             <div className="card text-center card-w">
//               <div className="step-number">1</div>

//               <h3>Add Your Properties</h3>

//               <p className="text-muted">
//                 Create properties, units, and organize your portfolio.
//               </p>
//             </div>

//             <div className="card text-center card-w">
//               <div className="step-number">2</div>

//               <h3>Add Tenants & Leases</h3>

//               <p className="text-muted">
//                 Store tenant records, lease agreements, and occupancy details.
//               </p>
//             </div>

//             <div className="card text-center card-w">
//               <div className="step-number">3</div>

//               <h3>Track Rent & Operations</h3>

//               <p className="text-muted">
//                 Monitor payments, inspections, and property performance easily.
//               </p>
//             </div>
//           </div>
//         </div>
//       </section>

//       {/* ================= CTA ================= */}
//       <section className="home-cta">
//         <div className="page-container">
//           <div className="text-center">
//             <h2>Run your rental business from one dashboard</h2>

//             <p className="text-muted mb-lg">
//               Replace spreadsheets and manual processes with a modern rental
//               management platform built for landlords.
//             </p>

//             <div className="flex justify-center gap-md flex-mobile-col">
//               <button
//                 className="btn btn-primary"
//                 onClick={() => navigate("/register")}
//               >
//                 Create Account
//               </button>

//               {/* <button
//                 className="btn btn-secondary"
//                 onClick={() => navigate("/login")}
//               >
//                 Sign In
//               </button> */}
//             </div>
//           </div>
//         </div>
//       </section>

//       {/* ================= FOOTER ================= */}
//       <footer className="home-footer">
//         <div className="page-container flex justify-between items-center flex-mobile-col gap-md">
//           <div>
//             <h3>Rental Property Management Platform</h3>

//             <p className="text-sm text-muted">
//               Built for landlords and property managers.
//             </p>
//           </div>

//           <div className="flex gap-md">
//             {/* <button
//               className="btn btn-secondary"
//               onClick={() => navigate("/login")}
//             >
//               Sign In
//             </button> */}

//             {/* <button
//               className="btn btn-primary"
//               onClick={() => navigate("/register")}
//             >
//               Register
//             </button> */}
//           </div>
//         </div>

//         <div className="text-center mt-lg">
//           <p className="text-sm text-muted">
//             © {new Date().getFullYear()} Rental Property Management Platform
//           </p>
//         </div>
//       </footer>
//     </div>
//   );
// }

// frontend/src/features/home/Home.jsx

import { useNavigate } from "react-router-dom";

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
  );
}