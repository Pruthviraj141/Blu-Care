# BLUCARE+ REFINED CLINICAL DESIGN SYSTEM
## Clinical Palette & Component System (Refero, Scrolltide & Navbar Gallery Standard)

---

### 1. Refined Clinical Palette
BluCare+ operates on a strictly disciplined, restrained clinical color system designed for high medical trust, zero cognitive fatigue, and absolute legibility.

```css
:root {
  /* Surface Layers (Deep Ink & Slate Architecture) */
  --bg-base: #101316;          /* Ink - Base canvas */
  --bg-app: #101316;           /* Ink - Main background */
  --bg-subtle: #191F25;        /* Slate - Sidebars, secondary panels, inputs */
  --bg-surface: #252D35;       /* Surface - Cards, dialogs, bot bubbles */
  --bg-card: #252D35;          /* Surface - Component cards */
  --bg-elevated: #2E3741;      /* Elevated - Hovered cards, user bubbles, tooltips */
  --bg-input: #191F25;         /* Slate - Form fields and search inputs */

  /* Typography Hierarchy */
  --text-primary: #E8EDF2;     /* Text Primary - High contrast 14.8:1 */
  --text-secondary: #A1ABB6;   /* Slate Gray - Supporting metadata */
  --text-muted: #727E8A;       /* Muted Slate - Timestamps, placeholders */
  --text-subdued: #727E8A;

  /* Restrained Steel-Blue Clinical Accent (Zero Neon Green) */
  --accent-primary: #7696B5;   /* Steel-Blue Primary Action */
  --accent-hover: #8AAAC9;     /* Steel-Blue Hover State */
  --clinical-teal: #7696B5;
  --clinical-cyan: #8AAAC9;
  --accent-sage: #7696B5;
  --accent-lavender: #8AAAC9;

  /* Semantic Warnings (Strictly Reserved for Medical Urgency) */
  --severity-emergency: #EF4444; /* Emergency alert, acute red flags, 108 shortcut */
  --severity-warning: #F59E0B;   /* Urgent care consultation within 24h */
  --severity-urgent: #F59E0B;
  --severity-routine: #7696B5;   /* Routine primary care */
  --severity-selfcare: #8AAAC9;  /* At-home symptomatic monitoring */
  --severity-info: #7696B5;
  --status-normal: #7696B5;
  --status-risk: #EF4444;

  /* Borders & Separation */
  --border-light: rgba(255, 255, 255, 0.08);
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-strong: rgba(255, 255, 255, 0.15);
  --border-focus: #7696B5;
  --shadow-base: 0 4px 20px rgba(0, 0, 0, 0.35);

  /* Geometry Scale (Max 3 Radii) */
  --radius-control: 6px;       /* Buttons, inputs, chips, dropdown items */
  --radius-card: 10px;         /* Condition cards, facility cards, panels */
  --radius-panel: 14px;        /* Modals, clinical containers */
}
```

---

### 2. Reference Implementation Priority Map

| Priority | Reference | Role in BluCare+ Implementation |
| :--- | :--- | :--- |
| **1** | **Refero Styles** | Core design system foundation, Ink/Slate/Surface palette, spacing scale, DESIGN.md exports, and clinical monochrome structure. |
| **2** | **Scrolltide UI** | Dashboard layouts, real data shapes, structured clinical cards, and loading/empty states. |
| **3** | **Navbar Gallery** | Collapsible navigation sidebar, top breadcrumb header, search controls, and mobile off-canvas drawer. |
| **4** | **CTA Gallery** | High-contrast button hierarchy (primary steel-blue, secondary elevated slate, emergency red), inputs, and clear active states. |
| **5** | **ScreensDesign** | Conversational health consultation flows, patient onboarding, settings, and profile screens. |
| **6** | **Footer Design** | Typographic grid footer with regulatory medical disclaimers and emergency hotline routing (108 / 112). |
| **7** | **Scrolltide Components** | Tab switcher primitives, collapsible sections, and subtle message stream entrance interactions. |
| **8** | **3Dicons / Liquid Glass** | Restrained backdrop blur on navigation bars and floating controls without compromising clinical legibility. |

---

### 3. Visual Rules Applied
1. **Ink & Layered Slate Surfaces**: Deep `#101316` canvas with layered `#191F25` and `#252D35` surfaces.
2. **Clean Typography**: Inter font family with comfortable line heights and WCAG AA contrast.
3. **Restrained Steel-Blue**: Steel-blue `#7696B5` accent instead of garish neon green or purple AI gradients.
4. **Reserved Emergency Colors**: Red `#EF4444` and Amber `#F59E0B` used strictly when clinical warning signs or emergency escalation are required.
5. **Purposeful Feedback**: Thin borders (`rgba(255, 255, 255, 0.08)`), subtle shadows, and tactile button feedback. Zero glowing borders or distracting persistent animations.
