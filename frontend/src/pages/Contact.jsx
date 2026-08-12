import { useState } from "react";
import SEO from "../components/SEO";

export default function Contact() {
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 5000);
  };

  return (
    <>
      <SEO
        title="Contact AlphaOne — Get in Touch"
        description="Contact AlphaOne for property management solutions across Kenya and East Africa. Email, phone, or send us a message directly."
        canonical="https://alphaone.africa/contact"
      />

      <section className="contact-hero">
        <div className="container">
          <h1>Get in Touch</h1>
          <p>Have a question about AlphaOne? Need a demo? Want to discuss your property management needs? We would love to hear from you.</p>
        </div>
      </section>

      <section className="section" id="contact">
        <div className="container">
          <div className="contact-grid">
            <div className="contact-text">
              <h2 className="section-title" style={{ textAlign: "left" }}>Let&apos;s start a conversation</h2>
              <p>
                Whether you are a single landlord or managing hundreds of units, we can help you find the right plan and get up and running quickly.
              </p>
              <div className="contact-info-item">
                <i className="fa-solid fa-envelope"></i>
                <div>
                  <strong>Email</strong><br />
                  <a href="mailto:webloom.techies@gmail.com">webloom.techies@gmail.com</a>
                </div>
              </div>
              <div className="contact-info-item">
                <i className="fa-solid fa-phone"></i>
                <div>
                  <strong>Phone</strong><br />
                  <a href="tel:+254704072784">+254 704 072 784</a>
                </div>
              </div>
              <div className="contact-info-item">
                <i className="fa-solid fa-location-dot"></i>
                <div>
                  <strong>Office</strong><br />
                  Ngong Road, Nairobi, Kenya
                </div>
              </div>
              <div className="contact-info-item">
                <i className="fa-solid fa-clock"></i>
                <div>
                  <strong>Support Hours</strong><br />
                  Monday – Friday, 8:00 AM – 6:00 PM EAT
                </div>
              </div>
            </div>
            <form id="contactForm" action="https://formspree.io/f/mldnbeby" method="POST" className="contact-form" onSubmit={handleSubmit}>
              <input type="text" name="name" placeholder="Your Full Name" required />
              <input type="email" name="email" placeholder="Your Email Address" required />
              <input type="text" name="company" placeholder="Company / Property Name (optional)" />
              <select name="interest" className="contact-select">
                <option value="">What are you interested in?</option>
                <option value="landlord">I am a Landlord</option>
                <option value="manager">I am a Property Manager</option>
                <option value="tenant">I am a Tenant</option>
                <option value="enterprise">Enterprise / Partnership</option>
                <option value="other">Other</option>
              </select>
              <textarea name="message" rows="5" placeholder="Tell us about your property management needs..." required></textarea>
              <button type="submit" className="btn btn-primary">
                Send Message <i className="fa-solid fa-paper-plane"></i>
              </button>
              {submitted && (
                <p style={{ color: "var(--primary)", fontWeight: 600, marginTop: "0.5rem" }}>
                  <i className="fa-solid fa-check-circle"></i> Thank you! We will get back to you within 24 hours.
                </p>
              )}
            </form>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="container">
          <span className="section-tag" style={{ color: "var(--light-accent)", background: "rgba(255,255,255,0.1)" }}>Get Started</span>
          <h2>Prefer to try it yourself?</h2>
          <p>Create a free account and explore AlphaOne with sample data. No credit card required.</p>
          <div className="cta-actions">
            <a href="/register" className="btn btn-white">Start Free Trial <i className="fa-solid fa-arrow-right"></i></a>
          </div>
        </div>
      </section>
    </>
  );
}
