# AlphaOne Public Website Redesign — Strict Isolation & Implementation Instructions

## 0. ROLE AND OBJECTIVE

You are working on the **AlphaOne Rental Property Management Tool**, a React/Vite application containing both:

1. A public-facing marketing website
2. A production SaaS application with authenticated dashboards and role-based interfaces

Your task is to **redesign and rebuild ONLY the public-facing website experience** while keeping the existing SaaS application completely stable.

The public website should feel modern, polished, premium, trustworthy, and product-focused.

The final public-facing website should contain:

* Landing / Home page
* About Us page
* Contact Us page
* Featured / Product Features page

The SaaS application already contains substantial styling and functionality. **DO NOT redesign, refactor, rewrite, simplify, or "clean up" the existing SaaS UI.**

The public website must have its own isolated styling system.

---

# 1. ABSOLUTE SAFETY RULES

These rules have the highest priority.

## DO NOT modify existing SaaS styling

Do NOT modify or rewrite existing styles merely to make the public website easier to build.

Treat the following files as PROTECTED:

```text
frontend/src/index.css
frontend/src/App.css

frontend/src/styles/
├── base.css
├── components.css
├── customers.css
├── dashboard.css
├── home.css
├── inspection.css
├── layout.css
├── pos.css
├── properties.css
├── team.css
└── utilities.css
```

Also treat existing dashboard/component CSS and CSS modules as protected unless a change is absolutely required to correctly route/render the public website.

Examples include:

```text
components/PropertySwitcher/PropertySwitcher.css
components/ui/*
features/auth/AuthForm.module.css
features/dashboard/layout/DashboardLayout.module.css
features/dashboard/widgets/*
```

Do NOT alter these files to solve public website styling problems.

---

# 2. NEVER USE GLOBAL CSS FOR THE PUBLIC WEBSITE

This is extremely important.

The new public website MUST NOT introduce styling such as:

```css
body {}
html {}
h1 {}
h2 {}
h3 {}
p {}
a {}
button {}
img {}
section {}
header {}
nav {}
```

Do NOT create global selectors that could affect the SaaS.

Do NOT reset the entire document globally.

Do NOT add:

```css
* {}
```

unless it is strictly scoped beneath a public website root selector.

Even then, prefer component-level styling.

---

# 3. PUBLIC WEBSITE STYLE ISOLATION

Create a completely isolated public website styling namespace.

Use a unique namespace such as:

```text
alpha-public
```

Every public page should have a root wrapper similar to:

```jsx
<div className="alpha-public">
```

or preferably a more structured unique class such as:

```jsx
<div className="alpha-public-page">
```

All public website classes must be uniquely prefixed.

Examples:

```text
alpha-public
alpha-public-page
alpha-public-nav
alpha-public-hero
alpha-public-hero-content
alpha-public-hero-title
alpha-public-hero-subtitle
alpha-public-feature
alpha-public-feature-grid
alpha-public-feature-card
alpha-public-contact
alpha-public-contact-form
alpha-public-footer
```

DO NOT create generic classes such as:

```text
.container
.header
.nav
.hero
.card
.button
.title
.section
.footer
.content
```

These are forbidden for the new public website because they can collide with existing SaaS styling.

---

# 4. PREFER CSS MODULES

Where practical, use CSS Modules for the new public website.

For example:

```text
frontend/src/pages/public/
├── PublicHome.jsx
├── PublicHome.module.css
├── About.jsx
├── About.module.css
├── Contact.jsx
├── Contact.module.css
├── Featured.jsx
└── Featured.module.css
```

Shared public components can use:

```text
frontend/src/components/public/
├── PublicNavbar.jsx
├── PublicNavbar.module.css
├── PublicFooter.jsx
├── PublicFooter.module.css
├── PublicButton.jsx
├── PublicButton.module.css
├── PublicSection.jsx
└── PublicSection.module.css
```

CSS Modules are preferred because they provide another layer of protection against collisions.

If ordinary CSS must be used, every selector MUST be scoped under the unique public namespace.

---

# 5. DO NOT TOUCH THE SAAS LOGIC

The following must remain functionally untouched unless there is an unavoidable routing integration requirement:

```text
frontend/src/api/
frontend/src/context/
frontend/src/hooks/
frontend/src/features/
frontend/src/components/
frontend/src/utils/
```

Do NOT modify:

* authentication
* login
* registration
* password handling
* JWT handling
* API clients
* API endpoints
* dashboards
* role-based access control
* tenant functionality
* landlord functionality
* property management functionality
* finance functionality
* payments
* reports
* inspections
* tickets
* settings
* notifications
* backend communication

The public website is a presentation layer only.

---

# 6. NO GIT OPERATIONS

You MUST NOT perform any Git operation autonomously.

Do NOT run:

```bash
git status
git add
git commit
git push
git pull
git checkout
git switch
git merge
git rebase
git reset
git restore
git stash
git branch
```

Do not create branches.

Do not switch branches.

Do not commit.

Do not push.

Do not pull.

The human developer will handle all Git operations.

---

# 7. NO SUDO

You MUST NEVER autonomously run:

```bash
sudo ...
```

Do not install system packages.

Do not modify system configuration.

Do not modify Docker/system services.

Do not modify permissions unless explicitly instructed by the developer.

---

# 8. DO NOT CHANGE INFRASTRUCTURE

Do not modify:

```text
docker-compose.yml
Dockerfile
Caddyfile
nginx.conf
.env
.env.*
```

unless the developer explicitly requests an infrastructure change.

The current deployment environment is considered stable.

---

# 9. DO NOT "FIX" UNRELATED PROBLEMS

While inspecting the project you may discover:

* old CSS
* duplicated CSS
* inconsistent naming
* unused imports
* old components
* unrelated warnings
* technical debt
* existing styling inconsistencies

DO NOT fix them.

Do not refactor unrelated code.

Do not improve unrelated components.

Do not rename existing classes.

Do not reorganize the project simply because you prefer another structure.

Only make changes directly necessary for the public website redesign.

---

# 10. FIRST PHASE — STUDY BEFORE MODIFYING

Before writing or modifying code, you MUST first study the existing implementation.

Do not immediately start coding.

Inspect:

```text
frontend/src/pages/Home.jsx
frontend/src/pages/Home.module.css
frontend/src/App.jsx
frontend/src/routes/AppRoutes.jsx
frontend/src/routes/ProtectedRoute.jsx
frontend/src/main.jsx
frontend/src/components/SEO.jsx
frontend/src/utils/seo.js
```

Also inspect the relevant existing public-page styling and the existing application layout.

Study:

* current landing page structure
* current navigation
* current footer
* current typography
* current colors
* current branding
* existing responsive behavior
* existing routes
* how Home is currently rendered
* how authentication routes are protected
* how public routes differ from protected routes
* how assets are currently imported
* existing logo usage
* existing SEO implementation

You are not studying this so that you can reuse its CSS blindly.

You are studying it so you understand the existing architecture and can safely replace the public presentation layer without damaging the SaaS.

---

# 11. STUDY THE EXISTING CSS

Before creating new styling, inspect:

```text
frontend/src/index.css
frontend/src/App.css
frontend/src/styles/
```

Understand:

* existing CSS architecture
* global selectors
* CSS variables
* typography
* spacing
* colors
* layout patterns
* responsive breakpoints
* naming conventions
* potential collision risks

Do NOT modify these files.

The purpose is to understand what must be avoided.

---

# 12. STUDY THE EXISTING ASSETS

Inspect:

```text
frontend/src/assets/
```

There may be:

* AlphaOne logo
* SaaS screenshots
* dashboard screenshots
* product screenshots
* promotional images
* other PNG/JPG/SVG assets

Use the existing assets where appropriate.

Do not duplicate assets unnecessarily.

Do not delete existing assets.

Do not rename existing assets unless explicitly instructed.

The SaaS screenshots should be treated as valuable product marketing assets.

Use them to communicate what AlphaOne actually does.

---

# 13. CURRENT PROJECT STRUCTURE

The frontend currently contains approximately:

```text
frontend/src/
├── api/
├── assets/
├── components/
├── config/
├── context/
├── features/
├── hooks/
├── pages/
├── routes/
├── styles/
└── utils/
```

The application already contains a substantial SaaS implementation.

Do NOT reorganize this entire structure.

Add the new public website cleanly alongside the existing application.

---

# 14. PROPOSED PUBLIC WEBSITE STRUCTURE

Create an isolated public website structure.

Preferred approach:

```text
frontend/src/
├── pages/
│   ├── public/
│   │   ├── PublicHome.jsx
│   │   ├── PublicHome.module.css
│   │   ├── About.jsx
│   │   ├── About.module.css
│   │   ├── Contact.jsx
│   │   ├── Contact.module.css
│   │   ├── Featured.jsx
│   │   └── Featured.module.css
│   │
│   └── existing SaaS/public files...
│
└── components/
    └── public/
        ├── PublicNavbar.jsx
        ├── PublicNavbar.module.css
        ├── PublicFooter.jsx
        ├── PublicFooter.module.css
        ├── PublicButton.jsx
        └── PublicButton.module.css
```

You may slightly adjust this structure if the existing routing architecture makes another arrangement safer.

Do NOT move existing SaaS files merely for aesthetic reasons.

---

# 15. PUBLIC WEBSITE ROUTES

Create or preserve clean public routes such as:

```text
/
```

```text
/about
```

```text
/contact
```

```text
/features
```

or:

```text
/featured
```

Use whichever naming best matches the existing project conventions, but keep the routes public.

Existing authenticated routes MUST continue working.

For example, do not break routes related to:

```text
/login
/register
/dashboard
/owner
/manager
/finance
/tenant
/super-admin
```

The exact existing routes should be discovered from the current routing configuration before making changes.

---

# 16. NAVIGATION REQUIREMENTS

Create a dedicated public navigation component.

It should contain:

* AlphaOne logo
* Home
* Features / Featured
* About
* Contact
* Login
* Get Started / Register CTA

The navigation must be responsive.

Desktop:

* clean horizontal navigation
* strong CTA
* premium SaaS appearance

Mobile:

* proper hamburger menu
* accessible controls
* smooth open/close behavior
* no horizontal overflow
* no interference with SaaS navigation

Do NOT reuse the SaaS dashboard Navbar unless it is already specifically designed for the public website.

Create a dedicated public navigation component.

---

# 17. LANDING PAGE

Build the landing page from scratch.

The page should communicate immediately:

### What AlphaOne is

A modern rental property management platform for landlords, property managers, and tenants across Kenya and East Africa.

### Hero

Create a strong hero section containing:

* clear headline
* supporting statement
* primary CTA
* secondary CTA
* product visual / SaaS screenshot
* subtle visual depth
* premium SaaS presentation

Avoid generic template-looking design.

The product should feel like a serious technology platform.

---

# 18. LANDING PAGE SECTIONS

Create a thoughtful marketing flow.

Suggested structure:

1. Navigation
2. Hero
3. Trust / positioning section
4. Problem statement
5. AlphaOne solution
6. Product screenshot showcase
7. Key capabilities
8. Role-based benefits
9. How AlphaOne works
10. Feature highlights
11. CTA section
12. Footer

You may improve this structure if the existing product information suggests a better storytelling flow.

Do not invent unrealistic product capabilities.

Use only capabilities that are supported by the existing application.

---

# 19. FEATURED / FEATURES PAGE

Create a dedicated product features page.

Showcase actual AlphaOne capabilities such as those supported by the existing application.

Potential categories include:

* Property management
* Unit management
* Tenant management
* Lease management
* Rent/payment management
* Finance
* Expenses
* Reports
* Inspections
* Maintenance/tickets
* Team management
* Notifications
* Bulk uploads
* Role-based dashboards

Do not claim functionality that does not exist.

Where appropriate, use SaaS screenshots from:

```text
frontend/src/assets/
```

Create an attractive visual product showcase.

---

# 20. ABOUT PAGE

The About page should establish:

* what AlphaOne is
* why it exists
* the problem it addresses
* who it serves
* its Kenya/East Africa focus
* the vision behind the platform
* trust and credibility

Do not invent fake statistics.

Do not invent awards.

Do not invent customers.

Do not invent partnerships.

Do not invent testimonials.

Do not make unsupported claims.

Use existing project information where available.

---

# 21. CONTACT PAGE

Create a professional contact page.

Include appropriate contact options based on information already present in the project.

Potential elements:

* contact form
* email
* phone
* location
* business inquiry CTA
* support CTA

Do not invent contact details.

If existing contact details are already present in the current application/SEO configuration, use those.

The form should have excellent UX but should NOT invent a backend endpoint.

If no contact API exists, build the frontend form UI and clearly leave integration isolated rather than pretending submissions are functional.

---

# 22. VISUAL DESIGN DIRECTION

The new public website should feel:

* modern
* premium
* trustworthy
* professional
* clean
* technology-focused
* African-market aware
* SaaS-oriented
* spacious
* responsive
* polished

Avoid:

* generic Bootstrap appearance
* excessive gradients
* excessive glassmorphism
* random animations
* excessive shadows
* childish illustrations
* clutter
* template-like sections
* huge blocks of text
* unnecessary UI decorations

The product screenshots should be treated as a major visual asset.

Let the actual product UI help sell the platform.

---

# 23. RESPONSIVE DESIGN

The public website MUST work well at:

```text
320px
375px
390px
414px
768px
1024px
1280px
1440px+
```

Pay particular attention to:

* navigation
* hero
* screenshots
* feature grids
* cards
* buttons
* typography
* footer
* spacing
* overflow

There must be no horizontal scrolling caused by the new public website.

---

# 24. TYPOGRAPHY

Do not globally modify typography.

Do not change:

```css
body
h1
h2
h3
p
button
a
```

Instead, style typography through scoped classes/CSS modules.

For example:

```text
alpha-public-hero-title
alpha-public-section-title
alpha-public-body
alpha-public-card-title
```

The public website's typography must not affect dashboard typography.

---

# 25. BUTTONS

Do not globally style:

```css
button {}
```

Create dedicated public button classes/components.

For example:

```text
alpha-public-button
alpha-public-button-primary
alpha-public-button-secondary
alpha-public-button-outline
```

The SaaS buttons must remain unchanged.

---

# 26. IMAGES

Use assets from:

```text
frontend/src/assets/
```

especially:

```text
aplha1_logo_.png
```

and any SaaS screenshots found there.

Before referencing an asset, verify its exact filename and path.

Do not assume filenames.

Do not create broken image references.

Use appropriate:

```jsx
alt=""
```

text for accessibility.

---

# 27. SEO

Preserve the existing SEO architecture.

Inspect:

```text
frontend/src/components/SEO.jsx
frontend/src/utils/seo.js
```

Implement page-specific metadata where appropriate.

The public pages should have appropriate:

* title
* description
* canonical URL
* Open Graph metadata
* Twitter metadata

Do not break existing SEO functionality.

Do not introduce malformed HTML.

Do not place Markdown URLs inside HTML attributes.

Use actual HTML URLs.

---

# 28. ACCESSIBILITY

Build the public website with proper accessibility.

Include:

* semantic HTML
* useful alt text
* keyboard-accessible navigation
* visible focus states
* appropriate button/link semantics
* aria labels where necessary
* sufficient contrast
* mobile navigation accessibility

Do not sacrifice accessibility for visual design.

---

# 29. ANIMATION

Use animation sparingly.

Good examples:

* subtle hero entrance
* hover states
* image reveal
* navigation transitions
* card hover
* CTA interaction

Avoid:

* excessive motion
* constant animations
* distracting effects
* animations that make the website feel like a template

Respect reduced-motion preferences where practical.

---

# 30. IMPORTANT: DO NOT REUSE GENERIC EXISTING CLASSES

Do not do this:

```jsx
<div className="container">
```

if `.container` already exists elsewhere.

Do not do this:

```jsx
<button className="btn">
```

if `.btn` exists elsewhere.

Do not do this:

```jsx
<section className="hero">
```

if `.hero` exists elsewhere.

Instead use isolated names:

```jsx
<div className={styles.publicContainer}>
```

or:

```jsx
<div className="alpha-public-container">
```

---

# 31. DEVELOPMENT WORKFLOW

Follow this order.

## Phase 1 — READ ONLY

Inspect the current implementation.

Do not modify files.

Study:

* routing
* Home
* CSS
* assets
* SEO
* application architecture

At the end of this phase, explain your understanding of:

1. How the current public page works
2. How the SaaS routes work
3. Which files are protected
4. Where the new public website should live
5. How styling isolation will be achieved

Then proceed.

---

## Phase 2 — PUBLIC WEBSITE ARCHITECTURE

Create the isolated public website architecture.

Implement:

* public route structure
* public layout
* public navbar
* public footer
* public button system
* isolated CSS modules

Do not touch SaaS styling.

---

## Phase 3 — LANDING PAGE

Build the new landing page.

Do not simply modify the old Home styling.

Create the new presentation from scratch while retaining useful existing content and product knowledge.

---

## Phase 4 — FEATURES PAGE

Create the Features/Featured page.

Use actual product capabilities and screenshots.

---

## Phase 5 — ABOUT PAGE

Create About.

---

## Phase 6 — CONTACT PAGE

Create Contact.

---

## Phase 7 — VERIFY ISOLATION

Before considering the work complete, inspect the changes and verify:

* SaaS dashboard still renders
* Login still renders
* Register still renders
* public pages render
* existing navigation works
* public navigation works
* SaaS CSS has not been modified
* no global selectors were introduced
* no generic class collisions were introduced
* no API code was changed unnecessarily
* no authentication code was changed
* no backend code was changed
* no Docker configuration was changed
* no environment configuration was changed

---

# 32. IMPORTANT FILE CHANGE POLICY

Before modifying an existing file, ask:

> Is this file part of the public website, routing integration, or absolutely necessary for the public website?

If the answer is no:

**DO NOT MODIFY IT.**

Prefer creating new files over modifying existing ones.

If you can solve a problem by creating a new isolated component instead of editing an existing SaaS component, create the new component.

---

# 33. DO NOT COPY OLD CSS

The old public landing page may contain useful content and structure.

However:

**DO NOT copy its CSS wholesale.**

Study it.

Understand it.

Then create a fresh visual system.

The objective is:

```text
Existing SaaS
      │
      │
      ├── Existing styling
      ├── Existing components
      ├── Existing functionality
      └── PROTECTED
       
Public Website
      │
      ├── New components
      ├── New CSS Modules
      ├── New class names
      ├── New visual system
      └── ISOLATED
```

---

# 34. DO NOT CHANGE APP BEHAVIOR

The public redesign must not accidentally alter:

* authentication state
* API URLs
* API requests
* cookies
* JWT
* role detection
* protected routes
* dashboard routing
* tenant routing
* landlord routing
* manager routing
* finance routing
* super-admin routing

If a change appears necessary to `App.jsx` or `AppRoutes.jsx`, make the smallest possible routing-only change.

Do not refactor these files.

---

# 35. VALIDATION

After implementation, run appropriate NON-DESTRUCTIVE development checks.

For example:

```bash
npm run build
```

and, where appropriate:

```bash
npm run dev
```

You may inspect files and run safe project-local validation commands.

DO NOT use sudo.

DO NOT run Git commands.

DO NOT modify system configuration.

If the build fails because of an unrelated pre-existing problem, do not start rewriting unrelated parts of the project.

Report the exact issue.

---

# 36. IF SOMETHING BREAKS

If a public website change breaks the SaaS:

1. Stop.
2. Identify exactly what caused the collision.
3. Revert ONLY your own public-site-related change if necessary.
4. Do not modify unrelated SaaS code to compensate.
5. Reimplement the public feature using stronger isolation.

The solution to a CSS collision is NOT to modify the SaaS CSS.

---

# 37. FINAL QUALITY STANDARD

The final public website should feel like a deliberate product website for a serious SaaS company.

It should communicate:

> "This is a real rental/property management platform."

rather than:

> "This is a React template with some text added."

Use the actual AlphaOne product interface and screenshots as visual proof of the product.

Prioritize:

1. Product clarity
2. Visual hierarchy
3. Trust
4. Conversion
5. Responsive design
6. Accessibility
7. Performance
8. CSS isolation
9. SaaS stability

---

# 38. FINAL REPORT

When finished, provide a concise implementation report containing:

### Created

List the new public website files.

### Modified

List ONLY the existing files that genuinely needed modification.

### Protected

Confirm that the SaaS styling and functionality were left untouched.

### Routes

List the public routes created.

### Assets

List the existing assets reused.

### Validation

Report the validation/build results.

### Potential Follow-up

List anything that requires explicit human approval before proceeding.

---

# FINAL COMMANDMENT

The SaaS application is the protected core product.

The public website is a new isolated presentation layer.

**NEVER sacrifice the SaaS to make the public website easier to build.**

When in doubt:

> CREATE NEW + SCOPE IT

instead of:

> MODIFY EXISTING + RISK COLLISION

Do not use sudo.

Do not use Git.

Do not modify infrastructure.

Do not modify existing SaaS styling.

Do not modify existing SaaS functionality.

Study first.

Then build the public website cleanly and independently.
