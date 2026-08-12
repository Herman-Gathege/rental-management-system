import SEO from "../components/SEO";
import logo from "../assets/aplha1_logo_.png";

export default function About() {
  return (
    <>
      <SEO
        title="About AlphaOne — Built for Kenya & East Africa"
        description="AlphaOne is a modern rental property management platform built for landlords, property managers, and tenants across Kenya and East Africa."
        canonical="https://alphaone.africa/about"
      />

      <section className="about-hero">
        <div className="container">
          <h1>We're on a mission to make property management simple</h1>
          <p>
            AlphaOne was born from a simple observation: too many landlords and property managers spend hours on tasks that should take minutes.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-header">
            <span className="section-tag">Our Story</span>
            <h2>Built by people who understand property management</h2>
            <p>
              We started AlphaOne after spending years working alongside landlords and property managers in Nairobi. We saw the same frustrations everywhere — messy spreadsheets, late-night phone calls about rent, lost lease documents, and the constant struggle to keep up.
            </p>
            <p style={{ marginTop: "1rem" }}>
              So we built a platform that handles the heavy lifting: automated rent tracking, digital lease management, real-time financial reports, and a mobile experience that works on the road. AlphaOne is designed for the way African property teams actually work.
            </p>
          </div>
          <div className="mission-grid">
            <div className="mission-card">
              <h3><i className="fa-solid fa-bullseye"></i> Our Mission</h3>
              <p>
                To give every landlord, property manager, and tenant the tools they need to manage properties with confidence — no expensive consultants, no complicated software, no guesswork.
              </p>
            </div>
            <div className="mission-card">
              <h3><i className="fa-solid fa-eye"></i> Our Vision</h3>
              <p>
                A future where property management across Africa is digitized, transparent, and accessible to everyone — from small-time landlords to large management firms.
              </p>
            </div>
            <div className="mission-card">
              <h3><i className="fa-solid fa-heart"></i> Our Values</h3>
              <p>
                Clarity over complexity. Speed over bureaucracy. Trust over shortcuts. We build software that respects your time and protects your data.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section" style={{ background: "#fff" }}>
        <div className="container">
          <div className="section-header">
            <span className="section-tag">What Drives Us</span>
            <h2>The principles that guide every decision we make</h2>
          </div>
          <div className="values-grid">
            <div className="value-card">
              <div className="value-icon"><i className="fa-solid fa-handshake"></i></div>
              <h3>Local First</h3>
              <p>Built in Kenya, for Kenya. We understand local payment methods, tenancy laws, and the unique challenges of East African property management.</p>
            </div>
            <div className="value-card">
              <div className="value-icon"><i className="fa-solid fa-lock"></i></div>
              <h3>Trust & Privacy</h3>
              <p>Your data stays yours. We use bank-grade encryption, regular backups, and strict access controls to keep your information safe.</p>
            </div>
            <div className="value-card">
              <div className="value-icon"><i className="fa-solid fa-graduation-cap"></i></div>
              <h3>Simplicity</h3>
              <p>Powerful software doesn't have to be complicated. AlphaOne is designed to be learned in minutes, not weeks of training.</p>
            </div>
            <div className="value-card">
              <div className="value-icon"><i className="fa-solid fa-headset"></i></div>
              <h3>Real Support</h3>
              <p>We don't hide behind chatbots. Our support team is based in East Africa and available when you need us most.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-header">
            <span className="section-tag">Leadership</span>
            <h2>Meet the team behind AlphaOne</h2>
            <p>A small, focused team passionate about modernizing property management in Africa.</p>
          </div>
          <div className="team-grid">
            <div className="team-card">
              <div className="team-avatar"><i className="fa-solid fa-user"></i></div>
              <div className="team-info">
                <h3>Remington</h3>
                <p className="team-role">Creative Director</p>
              </div>
            </div>
            <div className="team-card">
              <div className="team-avatar"><i className="fa-solid fa-user"></i></div>
              <div className="team-info">
                <h3>Anne</h3>
                <p className="team-role">Creative Director</p>
              </div>
            </div>
            <div className="team-card">
              <div className="team-avatar"><i className="fa-solid fa-user"></i></div>
              <div className="team-info">
                <h3>Development Team</h3>
                <p className="team-role">Engineering</p>
              </div>
            </div>
            <div className="team-card">
              <div className="team-avatar"><i className="fa-solid fa-user"></i></div>
              <div className="team-info">
                <h3>Operations Team</h3>
                <p className="team-role">Customer Success</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="container">
          <span className="section-tag" style={{ color: "var(--light-accent)", background: "rgba(255,255,255,0.1)" }}>Join Us</span>
          <h2>Ready to see AlphaOne in action?</h2>
          <p>Start your free trial today and discover a better way to manage properties.</p>
          <div className="cta-actions">
            <a href="/register" className="btn btn-white">Start Free Trial <i className="fa-solid fa-arrow-right"></i></a>
            <a href="/contact" className="btn btn-outline" style={{ borderColor: "rgba(255,255,255,0.4)", color: "#fff" }}>Contact Sales</a>
          </div>
        </div>
      </section>
    </>
  );
}
