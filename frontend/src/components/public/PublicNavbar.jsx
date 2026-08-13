import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import logo from "../../assets/aplha1_logo_.png";
import styles from "./PublicNavbar.module.css";

const navLinks = [
  { to: "/", label: "Home" },
  { to: "/featured", label: "Featured" },
  { to: "/about", label: "About" },
  { to: "/contact", label: "Contact" },
];

export default function PublicNavbar() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  return (
    <nav className={styles.alphaPublicNav}>
      <div className={styles.alphaPublicNavInner}>
        <Link to="/" className={styles.alphaPublicNavLogo}>
          <img src={logo} alt="AlphaOne" className={styles.alphaPublicNavLogoImg} />
        </Link>

        <div className={styles.alphaPublicNavDesktop}>
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`${styles.alphaPublicNavLink} ${location.pathname === link.to ? styles.alphaPublicNavLinkActive : ""}`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className={styles.alphaPublicNavDesktopActions}>
          <Link to="/login" className={styles.alphaPublicNavLogin}>
            Login
          </Link>
          <Link to="/register" className={styles.alphaPublicNavCta}>
            Get Started
          </Link>
        </div>

        <button
          className={`${styles.alphaPublicNavHamburger} ${open ? styles.alphaPublicNavHamburgerOpen : ""}`}
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
          aria-expanded={open}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>

      {open && (
        <div className={styles.alphaPublicNavMobile}>
          <div className={styles.alphaPublicNavMobileInner}>
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={styles.alphaPublicNavMobileLink}
                onClick={() => setOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <div className={styles.alphaPublicNavMobileActions}>
              <Link to="/login" className={styles.alphaPublicNavLogin} onClick={() => setOpen(false)}>
                Login
              </Link>
              <Link to="/register" className={styles.alphaPublicNavCta} onClick={() => setOpen(false)}>
                Get Started
              </Link>
            </div>
          </div>
        </div>
      )}

      {open && <div className={styles.alphaPublicNavOverlay} onClick={() => setOpen(false)} />}
    </nav>
  );
}
