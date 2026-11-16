# Phase 2: Design System Proposal & Architectural Specification

> **Personality**: **Quiet, Precise, Clinical Engineering** — Inspiring trust, clarity, and rapid legibility (reminiscent of Linear & Stripe Climate, tailored for medical triage). Zero decorative neon, zero cocktail artifacts, zero generic SaaS purple gradients.

---

## 1. Design Tokens Specification

### 1.1 Color Tokens (Semantic & Restrained)

```css
:root {
  /* Surface Layers (Deep, Neutral Slate - Not Pure Black or Violet) */
  --bg-app: #0B0D0E;          /* Base canvas */
  --bg-subtle: #121517;       /* Sidebars, secondary panels */
  --bg-surface: #181C1E;      /* Cards, dropdowns, dialogs */
  --bg-elevated: #202528;     /* Hovered cards, floating tooltips */
  --bg-input: #141719;        /* Inputs, search bars */

  /* Text & Foreground Hierarchy */
  --text-primary: #F0F3F5;    /* Headings, primary content (15.2:1 contrast) */
  --text-secondary: #9BA3A9;  /* Metadata, labels, secondary copy (6.5:1 contrast) */
  --text-muted: #6B747B;      /* Timestamps, placeholder text (4.6:1 contrast - WCAG AA pass) */

  /* Borders & Dividers */
  --border-subtle: rgba(255, 255, 255, 0.07);
  --border-strong: rgba(255, 255, 255, 0.14);
  --border-focus: #38BDF8;    /* Precision cyan focus ring */

  /* Clinical Brand Accents (Restrained, Desaturated) */
  --clinical-teal: #14B8A6;   /* Primary clinical action, verified status */
  --clinical-cyan: #0EA5E9;   /* Interactive links, active tab indicator */

  /* Triage Severity Signals */
  --severity-emergency: #EF4444; /* Immediate action required (Red) */
  --severity-urgent: #F59E0B;    /* Doctor consultation within 24h (Amber) */
  --severity-routine: #10B981;   /* Primary care visit (Emerald) */
  --severity-selfcare: #06B6D4;  /* Home care & monitoring (Cyan) */
}
```

### 1.2 Typography Hierarchy

- **Font Family**: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif.
- **Monospace Family**: "JetBrains Mono", ui-monospace, SFMono-Regular, monospace (for triage IDs, vitals, timestamps).

| Token | Size | Line Height | Tracking | Weight | Semantic Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `text-display` | 32px (2rem) | 38px | -0.025em | 600 | Page hero & dashboard title |
| `text-h1` | 24px (1.5rem) | 30px | -0.02em | 600 | Section headers, modal titles |
| `text-h2` | 18px (1.125rem) | 24px | -0.015em | 500 | Card titles, triage category titles |
| `text-body` | 14px (0.875rem) | 21px | normal | 400 | Chat messages, medical assessment text |
| `text-small` | 12px (0.75rem) | 16px | 0.01em | 400 | Secondary metadata, facility details |
| `text-badge` | 11px (0.6875rem) | 14px | 0.03em | 600 | Triage urgency badges, status tags |

### 1.3 Spacing Scale (Strict 4px Base)
- `space-1`: 4px | `space-2`: 8px | `space-3`: 12px | `space-4`: 16px
- `space-5`: 20px | `space-6`: 24px | `space-8`: 32px | `space-12`: 48px

### 1.4 Border Radius Scale (Max 3 Values)
- `rounded-control`: 6px (`rounded-md`) — Buttons, inputs, chips, dropdown items.
- `rounded-card`: 10px (`rounded-lg`) — Chat cards, hospital facility cards, symptom panels.
- `rounded-panel`: 14px (`rounded-xl`) — Modals, main workspace shells.
- *(No blanket `rounded-2xl` or `rounded-3xl`)*

### 1.5 Shadow Scale (Subtle Layered Depth, No Neon)
- `shadow-subtle`: `0 1px 2px rgba(0, 0, 0, 0.4)`
- `shadow-elevated`: `0 4px 16px rgba(0, 0, 0, 0.35), 0 1px 2px rgba(0, 0, 0, 0.2)`
- `shadow-modal`: `0 16px 36px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.08)`

---

## 2. Shared Component Primitives Architecture

1. **`Button`**:
   - `variant`: `primary` (clinical teal fill), `secondary` (subtle border + elevated bg), `ghost` (transparent, hover surface), `destructive` (red accent).
   - `size`: `sm` (28px height, text-xs), `md` (36px height, text-sm), `lg` (42px height, text-base).
2. **`Input` / `Textarea`**:
   - Consistent border `--border-subtle`, dark background `--bg-input`, active focus ring in `--border-focus`, integrated error message prop.
3. **`Card`**:
   - Background `--bg-surface`, border `--border-subtle`, hover elevation transition to `--bg-elevated`. Zero glowing neon borders.
4. **`TriageBadge`**:
   - Replaces `RiskBadge.jsx` with strict semantic color bindings (Emergency, Urgent, Routine, Self-Care) and consistent `rounded-control` geometry.
5. **`Modal` & `Dialog`**:
   - Standardized backdrop overlay (`rgba(0,0,0,0.7)`), centered entrance animation (<200ms), Escape key dismissal.

---

## 3. Transformation Plan for Existing Screens

1. **Public Landing Portal (`LandingPage.jsx`)**:
   - Strip out cocktail template components (`Cocktails.jsx`, `Menu.jsx`, bar leaf images).
   - Rebuild Hero & Workflow into a modern, clinical decision-support showcase highlighting multi-agent RAG, fast triage, and safety protocols.
2. **Clinical Workspace (`MultiRagChatPage.jsx`)**:
   - Refactor message bubbles from bloated glassmorphism into high-contrast, clean message streams.
   - Refactor diagnostic cards (differential diagnosis, red-flag alerts, facility locator) into cohesive medical card primitives.
3. **Hospitals & Facilities Finder (`HospitalsPage.jsx`)**:
   - Align filter controls, search bars, and facility cards to the unified design tokens.
