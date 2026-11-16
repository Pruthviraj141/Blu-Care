# Phase 1: Comprehensive Frontend UI/UX & Design System Audit

> **Target**: `frontend/` directory (React 19 + Vite 6 + Tailwind v4 + GSAP)  
> **Standard**: Zero-tolerance for generic AI aesthetics, arbitrary token sprawl, and legacy cocktail template artifacts.

---

## 1. Inventory of Current UI Patterns & Divergence

### 1.1 Buttons & Interactive Controls
- **`GlowButton.jsx`**: Uses heavy cyan/sage box-shadow glows (`shadow-[0_0_20px_var(--glow-sage)]`), backdrop filters, and arbitrary borders (`border-white/10`).
- **Inline Buttons in `MultiRagChatPage.jsx`**: Raw one-off Tailwind classes scattered across 833 lines:
  - `bg-sage hover:bg-sage/90 text-black px-4 py-2 rounded-xl text-sm font-semibold`
  - `p-2 hover:bg-white/5 rounded-lg text-text-subdued hover:text-text-primary transition-all`
  - `border border-white/10 rounded-full px-3 py-1.5 text-xs text-text-secondary`
- **Navigation Controls**: Pill-shaped buttons (`rounded-full`) clashing with cards (`rounded-xl` / `rounded-2xl`).
- **Divergence**: 4 different border radiuses for buttons (`rounded-lg`, `rounded-xl`, `rounded-2xl`, `rounded-full`), inconsistent active states, arbitrary padding values (`px-3 py-1`, `px-4 py-2`, `px-6 py-3`).

### 1.2 Cards, Panels & Surfaces
- **`GlassCard.jsx`**: Blanket glassmorphism (`backdrop-blur-md bg-card/60 border border-white/5`).
- **One-off Cards**:
  - `MultiRagChatPage.jsx`: Inline cards with `bg-surface border border-white/5 p-4 rounded-xl`.
  - `HospitalsPage.jsx`: Hardcoded hospital listing cards with `hover:border-sage/40 transition-all duration-300 shadow-lg`.
  - Landing page sections: Inherited templates from a cocktail bar landing page (`Cocktails.jsx`, `Menu.jsx`) using `bg-surface py-20` and noisy background overlays (`.noisy`).
- **Divergence**: Varying blur strengths (`backdrop-blur-sm` vs `backdrop-blur-md`), conflicting border opacities (`border-white/5`, `border-white/10`, `border-border-light`), arbitrary background alpha channels.

### 1.3 Badges & Status Indicators
- **`RiskBadge.jsx`**: Uses hardcoded colors for High/Medium/Low risk (`bg-red-500/10 text-red-400 border-red-500/20`, etc.).
- **Inline Badges**: `MultiRagChatPage.jsx` introduces inline triage tags (`bg-sage/10 text-sage px-2 py-0.5 rounded text-xs font-mono`).
- **Divergence**: Disconnected border-radius, font-weights (`font-medium` vs `font-bold`), and border opacities.

### 1.4 Inputs & Form Controls
- **Chat Input (`MultiRagChatPage.jsx`)**: Deep nested `textarea` with `resize-none bg-input-bg border-white/5 focus:border-sage/40 rounded-2xl p-4`.
- **Search Filters (`HospitalsPage.jsx`)**: `input` with `rounded-xl bg-surface border border-white/10 px-4 py-2.5 text-sm`.
- **Divergence**: Disparate heights, focus ring styles, padding scales, and disabled states.

---

## 2. Issues Grouped by Severity

### Critical (Actively Broken / Functional Contradiction)
1. **Template Residue (Cocktail Template Identity Crisis)**:
   - `Cocktails.jsx`, `Menu.jsx`, and `About.jsx` still reference cocktail leaves, drink menus, and bar assets (`/images/cocktail-left-leaf.png`, `#c-left-leaf`) inside a clinical medical triage application.
2. **Missing Accessible Contrast in Dark Mode**:
   - Secondary text token `--text-subdued: #8A8D9E` on `--bg-surface: #15151A` fails WCAG AA minimum contrast ratio for small text (3.8:1 vs required 4.5:1).

### High (Visibly Unprofessional / Banned AI Patterns)
1. **Glow & Neon Blobs**:
   - `GlowButton.jsx` and sections of `MultiRagChatPage.jsx` use saturated neon glows (`box-shadow: 0 0 20px var(--glow-sage)`), which explicitly matches the banned AI SaaS aesthetic.
2. **Generic Centered Hero & Blob Layout**:
   - `Hero.jsx` features centered headings, pill buttons with exaggerated border radiuses, and floating decorative blobs.
3. **Inconsistent Radius Sprawl**:
   - Concurrently uses `rounded-sm`, `rounded-md`, `rounded-lg`, `rounded-xl`, `rounded-2xl`, and `rounded-full` without hierarchical rules.

### Medium (Design Polish & Hierarchy)
1. **Arbitrary Spacing in Tailwind Classes**:
   - Arbitrary margins and paddings (`gap-[18px]`, `py-[84px]`, `w-[320px]`) instead of adhering to a strict 4px/8px modular grid.
2. **Overuse of `font-bold`**:
   - Section titles, badges, and card headers overuse heavy weights rather than relying on clean font-size and letter-spacing contrast.

### Low (Nice-to-Haves)
1. **Scrollbar Theming**:
   - Chrome-specific scrollbar rules in `index.css` without universal Firefox `scrollbar-width: thin` fallback.
2. **Keyboard Focus Uniformity**:
   - Global `*:focus-visible` override (`outline: 2px solid var(--accent-sage) !important`) overrides semantic component-level focus rings.

---

## 3. Review of Section 4 Banned Patterns Detected in Codebase

| Banned Pattern | Location Found in Existing Code |
| :--- | :--- |
| **Purple/Sage/Neon Glow Shadows** | `GlowButton.jsx` (`--glow-sage`, `--glow-lavender`) |
| **Glassmorphism everywhere** | `GlassCard.jsx`, `Navbar.jsx`, `MultiRagChatPage.jsx` |
| **Oversized border radiuses (`rounded-2xl` / `rounded-3xl` defaults)** | Chat message bubbles, modals, buttons |
| **Cocktail bar template artifacts** | `Cocktails.jsx`, `Menu.jsx`, `constants/index.js` |
| **Stock floating blobs & generic hero rhythm** | `Hero.jsx` |

---

## 4. Tailwind & CSS Tokens Review
- Current setup uses Tailwind v4 (`@tailwindcss/vite` and `@import "tailwindcss";` in `index.css`).
- Token definitions live in raw CSS custom properties in `:root` inside `index.css`.
- Many components bypass CSS variables and use hardcoded Tailwind utility colors (e.g., `text-red-400`, `bg-emerald-500/10`, `border-white/10`).
