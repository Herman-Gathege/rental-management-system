// frontend/src/features/home/Home.jsx

import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  const features = [
    {
      title: "Track Rent Payments",
      desc: "Monitor paid rent, overdue balances, and monthly income from one dashboard.",
      icon: "💰",
    },
    {
      title: "Manage Tenants Easily",
      desc: "Store tenant records, lease details, documents, and occupancy history securely.",
      icon: "👥",
    },
    {
      title: "Organize Properties",
      desc: "Manage apartments, units, and multiple properties without spreadsheets.",
      icon: "🏢",
    },
    {
      title: "Handle Operations Faster",
      desc: "Track inspections, maintenance, and property activity in one place.",
      icon: "🛠️",
    },
  ];

  const reasons = [
    "Reduce manual paperwork",
    "Track rent arrears instantly",
    "Centralize property operations",
    "Improve team coordination",
  ];

  const highlights = [
    "Rent Tracking",
    "Tenant Records",
    "Lease Management",
    "Property Insights",
  ];

  return (
    <div className="home">
      {/* ================= HERO ================= */}
      <section className="home-hero">
        <div className="page-container home-hero-grid">
          {/* LEFT */}
          <div className="home-hero-content">
            <div className="hero-badge">
              Modern Rental Property Management Platform
            </div>

            <h1>
              Everything landlords need to manage{" "}
              <span className="company-blue">rental properties</span>
            </h1>

            <p className="text-muted hero-description">
              Track rent, manage tenants, organize leases, and monitor property
              operations from one simple dashboard.
            </p>

            <div className="flex gap-md mt-lg flex-mobile-col">
              {/* <button
                className="btn btn-primary"
                onClick={() => navigate("/register")}
              >
                Get Started
              </button> */}

              <button
                className="btn btn-secondary"
                onClick={() => navigate("/login")}
              >
                Sign In
              </button>
            </div>

            {/* QUICK VALUE POINTS */}
            <div className="hero-highlights mt-lg">
              {highlights.map((item) => (
                <div key={item} className="highlight-pill">
                  ✔ {item}
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT */}
          <div className="hidden-mobile">
            <div className="card dashboard-preview">
              <div className="dashboard-preview-header">
                <div className="dashboard-dot red"></div>
                <div className="dashboard-dot yellow"></div>
                <div className="dashboard-dot green"></div>
              </div>

              <div className="dashboard-preview-body">
                <div className="dashboard-cards">
                  <div className="mini-card">
                    <span>Collected Rent</span>
                    <strong>KES 2.4M</strong>
                  </div>

                  <div className="mini-card">
                    <span>Occupied Units</span>
                    <strong>84%</strong>
                  </div>
                </div>

                <div className="dashboard-chart"></div>

                <div className="dashboard-table">
                  <div className="table-row"></div>
                  <div className="table-row"></div>
                  <div className="table-row"></div>
                  <div className="table-row"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= WHY LANDLORDS LOVE IT ================= */}
      <section className="home-trust">
        <div className="page-container">
          <div className="section-header text-center">
            <h2>Why landlords choose our platform</h2>

            <p className="text-muted">
              Built to simplify daily rental property operations.
            </p>
          </div>

          <div className="home-feature-grid">
            {reasons.map((reason) => (
              <div className="card card-w text-center" key={reason}>
                <h3>{reason}</h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= FEATURES ================= */}
      <section className="home-features">
        <div className="page-container">
          <div className="section-header text-center">
            <h2>Manage your entire rental business from one place</h2>

            <p className="text-muted">
              No spreadsheets. No scattered records. No manual chaos.
            </p>
          </div>

          <div className="home-feature-grid">
            {features.map((feature) => (
              <div className="card card-w" key={feature.title}>
                <div className="feature-icon">{feature.icon}</div>

                <h3>{feature.title}</h3>

                <p className="text-muted">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= SIMPLE WORKFLOW ================= */}
      <section className="home-steps">
        <div className="page-container">
          <div className="section-header text-center">
            <h2>Simple setup. Powerful management.</h2>

            <p className="text-muted">
              Start managing your properties in minutes.
            </p>
          </div>

          <div className="home-step-grid">
            <div className="card text-center card-w">
              <div className="step-number">1</div>

              <h3>Add Your Properties</h3>

              <p className="text-muted">
                Create properties, units, and organize your portfolio.
              </p>
            </div>

            <div className="card text-center card-w">
              <div className="step-number">2</div>

              <h3>Add Tenants & Leases</h3>

              <p className="text-muted">
                Store tenant records, lease agreements, and occupancy details.
              </p>
            </div>

            <div className="card text-center card-w">
              <div className="step-number">3</div>

              <h3>Track Rent & Operations</h3>

              <p className="text-muted">
                Monitor payments, inspections, and property performance easily.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section className="home-cta">
        <div className="page-container">
          <div className="text-center">
            <h2>Run your rental business from one dashboard</h2>

            <p className="text-muted mb-lg">
              Replace spreadsheets and manual processes with a modern rental
              management platform built for landlords.
            </p>

            <div className="flex justify-center gap-md flex-mobile-col">
              <button
                className="btn btn-primary"
                onClick={() => navigate("/register")}
              >
                Create Account
              </button>

              {/* <button
                className="btn btn-secondary"
                onClick={() => navigate("/login")}
              >
                Sign In
              </button> */}
            </div>
          </div>
        </div>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="home-footer">
        <div className="page-container flex justify-between items-center flex-mobile-col gap-md">
          <div>
            <h3>Rental Property Management Platform</h3>

            <p className="text-sm text-muted">
              Built for landlords and property managers.
            </p>
          </div>

          <div className="flex gap-md">
            {/* <button
              className="btn btn-secondary"
              onClick={() => navigate("/login")}
            >
              Sign In
            </button> */}

            {/* <button
              className="btn btn-primary"
              onClick={() => navigate("/register")}
            >
              Register
            </button> */}
          </div>
        </div>

        <div className="text-center mt-lg">
          <p className="text-sm text-muted">
            © {new Date().getFullYear()} Rental Property Management Platform
          </p>
        </div>
      </footer>
    </div>
  );
}