# MISSION: Total Frontend Redesign — Zero-Tolerance for "AI-Generated" Look

You are acting as a world-class Senior Frontend Engineer + Product Designer + Design
Systems Architect — the caliber of person who has personally shipped design systems at
Apple, Linear, Stripe, Notion, Vercel, Arc, Raycast, or Framer.

Scope: **`frontend/` folder ONLY.**
- Stack: React + Vite + TailwindCSS.
- There is NO backend yet, and you must NOT wire one up, mock one, or add new
  features/business logic. This is a pure visual/UX/design-system transformation of the
  EXISTING screens and components. Every existing page, route, and feature must still
  exist and still work exactly the same functionally — only the look, feel, structure,
  and quality of the code/markup around it changes.
- Do not delete functionality. Do not invent new pages. Do not change data shapes,
  props contracts, or API calls (there aren't any yet — don't add any).

Your job is not decoration. Your job is to make this look like it was hand-crafted over
months by a top-tier design team — not generated in one pass by an AI. That means the
end result must have **zero of the tells** that make people say "this looks AI-made."

---

## 1. THE ACTUAL GOAL (read this before anything else)

I've told you to make this "like nothing seen before in frontend history." Take that
seriously as a *direction*, not as literal marketing copy you should believe about your
own output. What I actually want is:

- Zero generic, templated, "Bootstrap-with-Tailwind-classes-swapped" patterns.
- Zero of the specific visual tics that immediately read as AI-generated (see the
  banned list in Section 4 — this is the most important section in this document).
- Every decision — spacing, type scale, color, radius, motion — made deliberately and
  justified, not defaulted to whatever Tailwind gives you out of the box.
- A level of polish and restraint where the interesting thing is *how considered* it
  is, not how much visual noise it has.

If at any point you're unsure whether something is "premium" or "generic," default to:
**more restraint, more whitespace, fewer competing effects, better typography.**
Premium products are quiet, not loud.

---

## 2. MANDATORY PROCESS — DO NOT SKIP OR REORDER

You must NOT start editing files immediately. Follow this exact sequence:

### Phase 1 — Full Audit (output only, no code changes)
1. Recursively review every file in `frontend/` (components, pages, layouts, hooks,
   Tailwind config, global CSS).
2. Produce a written audit that includes:
   - A full inventory of every distinct UI pattern currently in use (buttons, cards,
     inputs, nav, modals, etc.) and every place each one diverges from the others
     (inconsistent radius, padding, font sizes, color usage, shadow usage).
   - A list of every issue found, grouped by severity: **Critical / High / Medium /
     Low**. Critical = actively broken, inaccessible, or unusable. High = visibly
     unprofessional or inconsistent in ways users will notice immediately. Medium =
     polish issues. Low = nice-to-haves.
   - Explicit callouts anywhere you find the AI-generated tells listed in Section 4.
   - Current Tailwind config review: default theme still in use vs. customized,
     unused config, arbitrary one-off values scattered in class names instead of
     tokens.

### Phase 2 — Design System Proposal (output only, no code changes)
3. Propose ONE cohesive design system (see Section 5 for required parts) as a concrete
   spec: exact type scale with px/rem values and use cases, exact spacing scale, exact
   color tokens with hex values and semantic names, exact shadow tokens, exact radius
   tokens, motion/easing tokens.
4. Explain the design direction in plain language: what's the personality of this
   product (e.g., "quiet, dense, technical — like Linear," or "warm, editorial,
   confident — like Stripe's marketing site")? Pick ONE coherent direction and justify
   it based on what the app actually does — don't pick a vibe at random.
5. Present this proposal as a short design rationale before touching code. Wait for
   this to be internally consistent — every subsequent implementation decision should
   trace back to a token or rule defined here, not be invented ad hoc per component.

### Phase 3 — Implementation
6. Build the design system first: Tailwind config (theme extension, not overrides that
   fight Tailwind), design tokens, shared primitive components (Button, Input, Card,
   Badge, Modal, Dropdown, Table, etc.) in a clear, reusable structure.
7. Apply the system to every page/component, one area at a time (e.g., navigation →
   dashboard → forms → tables → modals → empty/loading/error states), replacing
   one-off styling with the shared primitives and tokens.
8. Remove all duplicated/dead styling as you go. Do not leave the old inconsistent
   classes alongside the new system "just in case."
9. Do not introduce new component files unless a pattern is genuinely repeated 2+
   times — don't over-abstract single-use UI into needless components.

### Phase 4 — Self-Review (mandatory before declaring done)
10. Go through the checklist in Section 8 explicitly and honestly. If something fails,
    fix it before finishing — don't just report the failure.
11. Give a final before/after summary: what changed structurally, what design
    decisions were made and why, and any tradeoffs or follow-ups you'd flag for a human
    reviewer.

Do not collapse these phases. Do not start writing component code during Phase 1 or 2.

---

## 3. NON-NEGOTIABLE CONSTRAINTS

- Do not touch anything outside `frontend/`.
- Do not add a backend, mock API layer, fake data-fetching, or new routes/features.
- Do not change any component's props/interface in a way that would break a future
  backend integration — this is a re-skin, not a re-architecture of data flow.
- Preserve all existing functionality, all existing routes, all existing user flows.
- If TypeScript is present, maintain full type safety — do not introduce `any` or
  loosen existing types.
- Keep the diff reviewable: prefer clear, incremental commits/sections of change over
  one giant unreviewable rewrite, even though you're doing the whole frontend.

---

## 4. BANNED PATTERNS — THE SPECIFIC THINGS THAT SCREAM "AI-GENERATED"

This is the most important section. Do not do ANY of the following, even if they seem
like reasonable defaults:

**Layout & structure**
- The generic "hero with centered heading + subheading + two pill buttons + gradient
  blob background" pattern.
- Centered-everything layouts with no asymmetry or intentional grid structure.
- Cards that are just `bg-white rounded-xl shadow p-6` copy-pasted everywhere with no
  variation in density, elevation, or purpose.
- Equal-width 3-column "feature grids" with an icon-in-a-circle, a bold title, and one
  sentence of description, repeated identically.
- Sections that all use identical vertical padding/rhythm with no visual hierarchy
  between "important" and "supporting" content.

**Color & surface**
- Purple-to-blue (or pink-to-orange) gradients used as a default decorative device.
- Indigo/violet as the default "AI SaaS" primary color with no other reasoning behind
  the choice.
- Glassmorphism (frosted blur + translucency) applied everywhere rather than as one
  deliberate accent.
- Random unthemed colors dropped into one-off classes instead of drawn from tokens.

**Shape & elevation**
- Oversized border radius on everything (`rounded-2xl`/`rounded-3xl` used as a
  blanket default rather than a deliberate choice per component type).
- Heavy, glowing, colored box-shadows (the "neon glow card" look).
- Inconsistent radius across sibling components (one card `rounded-lg`, the next
  `rounded-xl`, with no system behind the difference).

**Typography**
- A single default sans font at default Tailwind sizes with no real type scale.
- Overuse of `font-bold` for everything instead of a considered weight/size hierarchy.
- Inconsistent heading sizes across pages that should share hierarchy.

**Icons & imagery**
- Generic rounded-square gradient icon badges (the "colorful icon tile" grid look).
- Overuse of emoji or cartoonish icon sets in a professional product context.
- Stock-looking illustrations that don't match the product's actual content.

**Motion**
- Everything fading+sliding up on scroll with identical timing (the "AOS.js default"
  look).
- Bouncy/springy easing used indiscriminately instead of purposeful, restrained easing.
- Hover effects that scale/glow/shadow-bloom on every single element regardless of
  whether that element is interactive or meaningful.

**Copy & content structure (where it intersects with layout)**
- Vague marketing filler text as placeholder ("Powerful. Flexible. Simple.") sitting
  in real product UI.

If you catch yourself about to write any of the above, stop and choose a more specific,
considered alternative instead — see Section 5 for what to do instead.

---

## 5. REQUIRED DESIGN SYSTEM (define once, use everywhere)

Define and document all of the following as real Tailwind config/tokens — not
one-off inline values:

- **Type scale**: a deliberate, limited set of sizes (not 15 different font sizes)
  with clear semantic roles (display, heading-1..3, body, small, caption, label,
  mono/code if relevant). Real font pairing decision (not default system sans unless
  that's a deliberate choice) with justified line-height and letter-spacing per size.
- **Spacing scale**: one consistent scale used for padding, margin, and gaps
  throughout — no arbitrary pixel values scattered in class names.
- **Color palette**: a small set of semantic tokens (background layers, foreground/
  text layers, border, primary/accent, success/warning/danger, and their
  dark-mode equivalents if dark mode applies) — not a rainbow of unrelated colors.
- **Radius scale**: 2–4 deliberate values max, mapped to component types (e.g., inputs
  vs. cards vs. modals), not one blanket huge radius everywhere.
- **Shadow/elevation scale**: subtle, restrained, used to indicate real elevation
  (dropdown above card above page) rather than decoration.
- **Motion tokens**: a small set of durations/easings (e.g., fast/base/slow,
  standard-ease/emphasized-ease) applied consistently — no per-component invented
  timing.
- **Component variants**: Button (primary/secondary/ghost/destructive × sizes),
  Input/Select/Textarea (default/error/disabled/focus states), Card (variants by
  density/purpose), Badge, Alert/Toast, Modal/Dialog, Dropdown/Menu, Navigation/Sidebar,
  Table, empty/loading/error states, skeleton loaders.

Every one of these must be genuinely reused — audit for and eliminate any component
that reimplements a variant of one of these primitives locally instead of using the
shared one.

---

## 6. ANIMATION — RESTRAINED AND PURPOSEFUL ONLY

Only use motion that clarifies state or hierarchy, never motion for decoration:
- Opacity/translate transitions for entrance, kept small (a few px, not large slides).
- `scale-[1.01]`–`scale-[1.02]` on hover for genuinely interactive elements only.
- Staggered entrance for lists/grids, subtle and quick (not a visible cascade delay
  that makes the UI feel slow).
- Skeleton loaders and considered loading/empty/error states for anything
  asynchronous-looking, even without a real backend yet (build the UI states; don't
  wire up real fetching).
- Page/route transitions should be smooth but fast — under ~200–250ms for most UI
  motion; nothing should feel like it's making the user wait to see content.
- Respect `prefers-reduced-motion`.

---

## 7. ACCESSIBILITY & PERFORMANCE (non-optional, not an afterthought)

- Semantic HTML throughout (proper heading order, `button` vs `a` used correctly,
  landmark regions, lists as `<ul>/<li>`, forms with real `<label>`s).
- Visible, consistent focus states on every interactive element (don't just remove
  outlines — replace with a deliberate focus ring that matches the design system).
- Full keyboard navigability: tab order, escape-to-close on modals/menus, arrow-key
  navigation where a native pattern expects it (menus, tabs).
- Color contrast meeting WCAG AA at minimum for all text/background combinations in
  the new palette.
- Proper ARIA only where semantic HTML isn't sufficient — don't over-apply ARIA.
- Optimize images (correct sizing/formats), avoid layout shift, avoid unnecessary
  re-renders, code-split/lazy-load route-level components where appropriate.
- Target Lighthouse ≥ 95 across Performance/Accessibility/Best Practices for the
  rebuilt pages.

---

## 8. FINAL SELF-REVIEW CHECKLIST (go through explicitly before finishing)

For the whole app, confirm and report on each of the following honestly:

- [ ] No pattern from the Section 4 banned list appears anywhere.
- [ ] Every button, card, input, badge, modal, and nav element uses the shared design
      system — zero one-off reimplementations.
- [ ] Spacing is consistent and intentional across every screen (no eyeballed padding).
- [ ] Type hierarchy is clear and consistent — you can tell what's most important on
      every screen at a glance.
- [ ] Color usage is restrained and semantic — no random unthemed colors.
- [ ] All interactive states exist and are consistent: default, hover, active, focus,
      disabled, error, loading.
- [ ] Every page has a considered empty state, loading state, and error state (even
      without a real backend).
- [ ] Fully responsive from mobile through desktop — verify actual breakpoint behavior,
      not just "it doesn't break."
- [ ] Keyboard-navigable and screen-reader sane throughout.
- [ ] No dead/duplicated CSS or components left behind from before the redesign.
- [ ] If you showed this to a designer from Linear/Stripe/Notion without context, would
      they assume a human designer made deliberate choices here? If the honest answer
      is no anywhere, go back and fix that area before declaring the work done.

---

## 9. OUTPUT FORMAT

1. Phase 1 audit (written).
2. Phase 2 design system proposal (written spec + rationale).
3. Phase 3 implementation (actual code changes to `frontend/`).
4. Phase 4 self-review against the Section 8 checklist + a short before/after summary.

Do not merge these into one undifferentiated wall of changes — keep the phases legible
so the reasoning behind the final result is traceable.
