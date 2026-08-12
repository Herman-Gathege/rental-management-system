import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import landingLogo from "../../assets/aplha1_logo_.png";
import "./LandingLayout.css";

export default function LandingLayout({ children }) {
  const [landingScrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [location]);

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/about", label: "About" },
    { href: "/features", label: "Features" },
    { href: "/contact", label: "Contact" },
  ];

  return (
    <div className="landing-root">
      <nav className={`landing-navbar ${landingScrolled ? "landing-scrolled" : ""}`} aria-label="Primary navigation">
        <div className="container landing-navbar-container">
          <div className="landing-logo">
            <Link to="/" className="landing-logo-link">
              <img src={landingLogo} alt="AlphaOne" className="landing-logo-img" />
              <span className="landing-logo-text">AlphaOne</span>
            </Link>
          </div>
          <ul className="landing-nav-links" id="main-navigation">
            {navLinks.map((link) => (
              <li key={link.href}>
                <Link
                  to={link.href}
                  className={location.pathname === link.href ? "landing-active" : ""}
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
          <div className="landing-nav-actions">
            <Link to="/login" className="btn btn-outline landing-nav-cta">
              Sign In
            </Link>
            <Link to="/register" className="btn btn-primary landing-nav-cta">
              Get Started
            </Link>
          </div>
          <button
            type="button"
            className={`landing-burger ${mobileOpen ? "landing-toggle" : ""}`}
            aria-label="Toggle navigation"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>
        {mobileOpen && (
          <div className="landing-mobile-menu">
            <ul>
              {navLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    className={location.pathname === link.href ? "landing-active" : ""}
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
              <li>
                <Link to="/login" className="btn btn-outline" style={{ width: "100%", marginTop: "1rem" }}>
                  Sign In
                </Link>
              </li>
              <li>
                <Link to="/register" className="btn btn-primary" style={{ width: "100%", marginTop: "0.5rem" }}>
                  Get Started
                </Link>
              </li>
            </ul>
          </div>
        )}
      </nav>

      <main>{children}</main>

      <footer className="footer">
        <div className="container">
          <div className="footer-grid">
            <div className="footer-brand">
              <Link to="/" className="landing-logo-link" style={{ marginBottom: "1rem" }}>
                <img src={landingLogo} alt="AlphaOne" className="landing-logo-img" />
                <span className="landing-logo-text">AlphaOne</span>
              </Link>
              <p>
                The modern property management platform built for landlords, property managers, and tenants across Kenya and East Africa.
              </p>
              <div className="footer-social">
                <a href="#" aria-label="LinkedIn"><i className="fab fa-linkedin-in"></i></a>
                <a href="#" aria-label="Twitter"><i className="fab fa-twitter"></i></a>
                <a href="#" aria-label="Instagram"><i className="fab fa-instagram"></i></a>
                <a href="#" aria-label="Facebook"><i className="fab fa-facebook-f"></i></a>
              </div>
            </div>
            <div>
              <h4>Product</h4>
              <ul>
                <li><Link to="/features">Features</Link></li>
                <li><Link to="/about">About Us</Link></li>
                <li><Link to="/contact">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4>Solutions</h4>
              <ul>
                <li><a href="#">Landlords</a></li>
                <li><a href="#">Property Managers</a></li>
                <li><a href="#">Tenants</a></li>
              </ul>
            </div>
            <div>
              <h4>Support</h4>
              <ul>
                <li><a href="mailto:webloom.techies@gmail.com">webloom.techies@gmail.com</a></li>
                <li><a href="tel:+254704072784">+254 704 072 784</a></li>
                <li><Link to="/contact">Help Center</Link></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; {new Date().getFullYear()} AlphaOne. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
