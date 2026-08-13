import { Link } from "react-router-dom";
import logo from "../../assets/aplha1_logo_.png";
import styles from "./PublicFooter.module.css";

export default function PublicFooter() {
  return (
    <footer className={styles.alphaPublicFooter}>
      <div className={styles.alphaPublicFooterInner}>
        <div className={styles.alphaPublicFooterGrid}>
          <div className={styles.alphaPublicFooterBrand}>
            <img src={logo} alt="AlphaOne" className={styles.alphaPublicFooterLogo} />
            <p className={styles.alphaPublicFooterDesc}>
              The modern rental property management platform built for landlords, property managers, and tenants across Kenya and East Africa.
            </p>
          </div>

          <div className={styles.alphaPublicFooterCol}>
            <h4 className={styles.alphaPublicFooterHeading}>Product</h4>
            <ul className={styles.alphaPublicFooterList}>
              <li><Link to="/featured" className={styles.alphaPublicFooterLink}>Features</Link></li>
              <li><Link to="/" className={styles.alphaPublicFooterLink}>Property Management</Link></li>
              <li><Link to="/" className={styles.alphaPublicFooterLink}>Tenant Management</Link></li>
              <li><Link to="/" className={styles.alphaPublicFooterLink}>Payments</Link></li>
            </ul>
          </div>

          <div className={styles.alphaPublicFooterCol}>
            <h4 className={styles.alphaPublicFooterHeading}>Company</h4>
            <ul className={styles.alphaPublicFooterList}>
              <li><Link to="/about" className={styles.alphaPublicFooterLink}>About</Link></li>
              <li><Link to="/contact" className={styles.alphaPublicFooterLink}>Contact</Link></li>
              <li><Link to="/" className={styles.alphaPublicFooterLink}>Careers</Link></li>
            </ul>
          </div>

          <div className={styles.alphaPublicFooterCol}>
            <h4 className={styles.alphaPublicFooterHeading}>Support</h4>
            <ul className={styles.alphaPublicFooterList}>
              <li><Link to="/contact" className={styles.alphaPublicFooterLink}>Help Center</Link></li>
              <li><Link to="/contact" className={styles.alphaPublicFooterLink}>Contact Us</Link></li>
              <li><Link to="/" className={styles.alphaPublicFooterLink}>Privacy Policy</Link></li>
            </ul>
          </div>
        </div>

        <div className={styles.alphaPublicFooterBottom}>
          <p className={styles.alphaPublicFooterCopy}>
            &copy; {new Date().getFullYear()} AlphaOne. All rights reserved.
          </p>

          <p className={styles.alphaPublicFooterCopy}>
  created by <a href="https://webloom-tech.onrender.com/" target="_blank" rel="noopener noreferrer">webloom tech kenya</a>
</p>

        </div>
      </div>
    </footer>
  );
}
