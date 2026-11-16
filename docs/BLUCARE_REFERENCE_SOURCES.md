# BLUCARE+ REFERENCE SOURCES & ATTRIBUTION MAPPING

This document records the component concepts, layout patterns, and design references adapted from authorized source libraries into BluCare+.

---

### 1. Refero Design Systems (https://styles.refero.design/)
- **Source**: Refero Clean SaaS & Design-MD patterns (`styles.refero.design/design-styles/clean-saas`)
- **Implemented Locations**:
  - `frontend/src/index.css`: Neutral graphite surface layering (`--bg-app`, `--bg-subtle`, `--bg-surface`, `--bg-elevated`).
  - `frontend/src/components/common/Card.jsx`: Neutral surface container with subtle border elevation.
  - `frontend/src/components/navigation/Sidebar.jsx`: Clean, collapsible sidebar with date grouping and 2px active indicator.
- **Adaptations**: Colors mapped to clinical dark graphite palette; removed high-contrast borders in favor of subtle 8% alpha dividers.

---

### 2. Scrolltide UI (https://www.scrolltide.co/)
- **Source**: Scrolltide UI & Components (`scrolltide.co/ui`, `scrolltide.co/components`)
- **Implemented Locations**:
  - `frontend/src/components/landing/ProductPreviewSection.jsx`: Segmented tabs with smooth indicator transition.
  - `frontend/src/components/common/Tabs.jsx`: Tab switcher primitive with counter badges.
  - `frontend/src/components/landing/HeroSection.jsx`: Interactive mock workspace preview container.
- **Adaptations**: Removed continuous animated shader background effects to prioritize accessibility and medical legibility.

---

### 3. Navbar Gallery (https://www.navbar.gallery/)
- **Source**: Navbar Gallery Minimal SaaS patterns (`navbar.gallery`)
- **Implemented Locations**:
  - `frontend/src/components/Navbar.jsx`: Sticky backdrop-blur navigation with brand icon, section anchor links, and mobile slide-in drawer.
  - `frontend/src/components/navigation/TopHeader.jsx`: Workspace header with context breadcrumb, quick 108 SOS action, and Clerk user menu.
- **Adaptations**: Integrated responsive mobile drawer with backdrop blur and keyboard ESC dismissal.

---

### 4. CTA Gallery (https://www.cta.gallery/)
- **Source**: CTA Gallery Buttons & Interactive States (`cta.gallery/categories/button`)
- **Implemented Locations**:
  - `frontend/src/components/common/Button.jsx`: Universal button hierarchy (primary, secondary, outline, ghost, danger).
  - `frontend/src/components/common/IconButton.jsx`: Compact icon actions with focus rings.
- **Adaptations**: Fully removed neon glow animations (`shadow-[0_0_20px_var(--glow-sage)]`) and replaced with high-contrast tactile feedback.

---

### 5. Footer Design (https://www.footer.design/)
- **Source**: Typographic Grid Footer patterns (`footer.design/styles/typographic`, `footer.design/styles/grid`)
- **Implemented Locations**:
  - `frontend/src/components/landing/LandingFooter.jsx`: 5-column typographic grid with platform links, emergency hotline direct links (108/112), regulatory medical disclaimers, and live system status pill.
- **Adaptations**: Added specific emergency service contact numbers (108 Ambulance) and medical device disclaimers.

---

### 6. Supahero & ScreensDesign (https://supahero.io/, https://screensdesign.com/)
- **Source**: Healthcare and diagnostic SaaS workflows (`supahero.io`, `screensdesign.com`)
- **Implemented Locations**:
  - `frontend/src/components/landing/HeroSection.jsx`: Direct product preview showing realistic differential diagnostic hypotheses rather than generic dashboard charts.
  - `frontend/src/components/landing/PipelineSection.jsx`: 4-stage clinical intelligence workflow (Intake -> Clinical Reasoning -> Dual-Domain Guidance -> Verified Facility Dispatch).

