import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SEO from "../../components/SEO";
import PublicNavbar from "../../components/public/PublicNavbar";
import PublicFooter from "../../components/public/PublicFooter";
import styles from "./Contact.module.css";

export default function Contact() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
    type: "general",
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    alert("Thank you for reaching out. This is a demo form — no backend is connected yet. The AlphaOne team will integrate the contact endpoint shortly.");
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className={styles.alphaPublicRoot}>
      <SEO
        title="Contact AlphaOne — Rental Property Management Support"
        description="Contact AlphaOne for rental property management software support and enquiries. Reach our team in Kenya for sales, support, or general questions."
        canonical="https://alphaone.africa/contact"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "ContactPage",
          "@id": "https://alphaone.africa/contact/#contactpage",
          "url": "https://alphaone.africa/contact",
          "name": "Contact AlphaOne — Rental Property Management Support",
          "description": "Contact AlphaOne for enquiries about rental property management software. Reach our team for support, partnerships, or general questions.",
          "isPartOf": {
            "@id": "https://alphaone.africa/#website"
          },
          "about": {
            "@id": "https://alphaone.africa/#organization"
          },
          "breadcrumb": {
            "@type": "BreadcrumbList",
            "itemListElement": [
              {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": "https://alphaone.africa/"
              },
              {
                "@type": "ListItem",
                "position": 2,
                "name": "Contact",
                "item": "https://alphaone.africa/contact"
              }
            ]
          }
        }}
      />

      <PublicNavbar />

      {/* HERO */}
      <section className={styles.alphaPublicHero}>
        <div className={styles.alphaPublicSectionInner}>
          <span className={styles.alphaPublicSectionTag}>Contact Us</span>
          <h1 className={styles.alphaPublicHeroTitle}>
            Let&apos;s start a conversation
          </h1>
          <p className={styles.alphaPublicHeroDesc}>
            Have a question, need support, or want to explore how AlphaOne can help your property business? We would love to hear from you.
          </p>
        </div>
      </section>

      {/* CONTENT */}
      <section className={styles.alphaPublicContent}>
        <div className={styles.alphaPublicSectionInner}>
          <div className={styles.alphaPublicContactGrid}>
            {/* FORM */}
            <div className={styles.alphaPublicContactFormWrap}>
              <form className={styles.alphaPublicForm} onSubmit={handleSubmit}>
                <div className={styles.alphaPublicFormGroup}>
                  <label className={styles.alphaPublicLabel} htmlFor="name">Full Name</label>
                  <input
                    id="name"
                    name="name"
                    type="text"
                    className={styles.alphaPublicInput}
                    placeholder="Your full name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className={styles.alphaPublicFormGroup}>
                  <label className={styles.alphaPublicLabel} htmlFor="email">Email Address</label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    className={styles.alphaPublicInput}
                    placeholder="you@company.com"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className={styles.alphaPublicFormGroup}>
                  <label className={styles.alphaPublicLabel} htmlFor="type">Enquiry Type</label>
                  <select
                    id="type"
                    name="type"
                    className={styles.alphaPublicSelect}
                    value={formData.type}
                    onChange={handleChange}
                  >
                    <option value="general">General Enquiry</option>
                    <option value="support">Technical Support</option>
                    <option value="sales">Sales / Partnership</option>
                    <option value="billing">Billing Question</option>
                  </select>
                </div>

                <div className={styles.alphaPublicFormGroup}>
                  <label className={styles.alphaPublicLabel} htmlFor="subject">Subject</label>
                  <input
                    id="subject"
                    name="subject"
                    type="text"
                    className={styles.alphaPublicInput}
                    placeholder="How can we help?"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className={styles.alphaPublicFormGroup}>
                  <label className={styles.alphaPublicLabel} htmlFor="message">Message</label>
                  <textarea
                    id="message"
                    name="message"
                    className={styles.alphaPublicTextarea}
                    placeholder="Tell us more about your enquiry..."
                    rows="5"
                    value={formData.message}
                    onChange={handleChange}
                    required
                  />
                </div>

                <button type="submit" className={styles.alphaPublicBtnPrimary}>
                  Send Message
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                  </svg>
                </button>
              </form>
            </div>

            {/* INFO */}
            <div className={styles.alphaPublicContactInfo}>
              <div className={styles.alphaPublicInfoCard}>
                <div className={styles.alphaPublicInfoIcon}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                    <polyline points="22,6 12,13 2,6" />
                  </svg>
                </div>
                <div>
                  <strong>Email</strong>
                  <p className={styles.alphaPublicInfoText}>hello@alphaone.africa</p>
                </div>
              </div>

              <div className={styles.alphaPublicInfoCard}>
                <div className={styles.alphaPublicInfoIcon}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z" />
                  </svg>
                </div>
                <div>
                  <strong>Phone</strong>
                  <p className={styles.alphaPublicInfoText}>+254 (0) 700 000 000</p>
                </div>
              </div>

              <div className={styles.alphaPublicInfoCard}>
                <div className={styles.alphaPublicInfoIcon}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                </div>
                <div>
                  <strong>Location</strong>
                  <p className={styles.alphaPublicInfoText}>Nairobi, Kenya</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
