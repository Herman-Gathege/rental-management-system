import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="home">
      {/* ================= NAVBAR ================= */}
      {/* <header className="navbar">
        <div className="page-container flex justify-between items-center h-full hidden-on-mobile">
          <div className="home-nav-logo " onClick={() => navigate("/")}>
            <img src="/assets/azani-logo 1.png" alt="Azani SmartDuka Logo" />
          </div>

          <div className="flex gap-md">
            <button
              className="btn btn-secondary"
              onClick={() => navigate("/login")}
            >
              Sign In
            </button>

            
          </div>
        </div>
      </header> */}

      {/* ================= HERO ================= */}
      <section className="home-hero">
        <div className="page-container home-hero-grid">
          {/* LEFT */}
          <div className="home-hero-content">
            <h1>
              Run your business with{" "}
              <span className="company-blue">clarity</span> and confidence
            </h1>

            <p className="text-muted">
              Azani SmartDuka helps small and medium businesses track stock,
              sales, and staff activity — without complexity or guesswork.
            </p>

            <div className="flex gap-md mt-md">
              {/* <button
                className="btn btn-primary"
                onClick={() => navigate("/register")}
              >
                Get Started Free
              </button> */}
              <button
                className="btn btn-secondary"
                onClick={() => navigate("/login")}
              >
                Sign In
              </button>
            </div>
          </div>

          {/* RIGHT */}
          <div className="home-hero-image hidden-on-mobile">
            <img src="/assets/hero.jpeg" alt="Dashboard preview" />
          </div>
        </div>
      </section>

      {/* ================= TRUST / PROOF ================= */}
<section className="home-trust">
  <div className="page-container home-trust-content">

    <p className="trust-text text-center">
      Trusted by <strong>shops, marts, hardware stores</strong>, and
      sales-driven SMEs that need visibility — not complexity.
    </p>

    <div className="home-trust-image">
      <img
        src="/assets/demo-dash.png"
        alt="Azani SmartDuka dashboard overview"
      />
    </div>

  </div>
</section>


      {/* ================= FEATURES ================= */}
      <section className="home-features">
        <div className="page-container">
          <h2 className="text-center">
            Everything you need to stay in control
          </h2>
          <p className="text-center text-muted mb-lg">
            A clear picture of your business — in seconds.
          </p>

          <div className="home-feature-grid">
            <div className="card">
              <h3>Stock Management</h3>
              <p className="text-muted">
                Track inventory, spot low stock early, and reduce losses.
              </p>
            </div>

            <div className="card">
              <h3>Sales Tracking</h3>
              <p className="text-muted">
                See daily sales and performance at a glance.
              </p>
            </div>

            <div className="card">
              <h3>Staff Accountability</h3>
              <p className="text-muted">
                Assign roles and ensure every sale is recorded.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ================= HOW IT WORKS ================= */}
      <section className="home-steps">
        <h2 className="text-center mb-md">Simple to start. Easy to use.</h2>

        <div className="home-step-grid">
          <div className="card text-center">
            <strong>1</strong>
            <p>Create your business account</p>
          </div>
          <div className="card text-center">
            <strong>2</strong>
            <p>Add stock and staff</p>
          </div>
          <div className="card text-center">
            <strong>3</strong>
            <p>Track sales and stay in control</p>
          </div>
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section className="home-cta text-center">
        <h2>Start managing your business with confidence</h2>
        <p className="text-muted mb-md">
          Join business owners replacing guesswork with clarity.
        </p>

        <button
          className="btn btn-primary"
          onClick={() => navigate("/register")}
        >
          Create Your Account
        </button>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="home-footer text-center">
        <p className="text-sm">
          © {new Date().getFullYear()} Azani SmartDuka. Built for growing
          businesses.
        </p>
        <p className="text-sm">
          A product by{" "}
          <a
            href="https://webloom-tech.onrender.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="company-blue"
          >
            Webloom Tech
          </a>
        </p>
      </footer>
    </div>
  );
}
