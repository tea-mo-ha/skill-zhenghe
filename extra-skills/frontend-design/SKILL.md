---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
---


This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

Remember: Claude is capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.

## Output Contract

Every frontend-design deliverable must include:

1. **Design Direction Summary**: One paragraph naming the aesthetic tone, primary font choices, color palette rationale, and the single most memorable visual element.
2. **Design Tokens** (CSS custom properties): At minimum `--color-primary`, `--color-accent`, `--color-bg`, `--color-surface`, `--color-text`, `--font-display`, `--font-body`, `--radius`, `--spacing-unit`.
3. **Working Code**: A single self-contained HTML/CSS/JS file (or framework component) that renders in a browser. No wireframes, no placeholders, no unimplemented stubs.
4. **Responsive Behavior**: Must render sensibly at 375px and 1440px. Breakpoint strategy stated explicitly.

**What this skill does NOT deliver**: data fetching logic, state management, API integration, backend contracts. Those belong to `frontend-ui-engineering` or `api-and-interface-design`.

## Boundary with frontend-ui-engineering

| Concern | frontend-design | frontend-ui-engineering |
|---|---|---|
| **Primary focus** | Visual identity, aesthetic direction, brand expression | Component architecture, state management, interactivity |
| **Output** | Styled page/component with design tokens | Production-ready component with props, types, tests |
| **Typography** | Font selection, pairing, hierarchy | Type scale implementation in design system |
| **Color** | Palette creation, mood, contrast ratios | Semantic token mapping in code |
| **Animation** | Motion design, transition feel, micro-interactions | Implementation via CSS/Framer Motion/GSAP |
| **Layout** | Spatial composition, visual flow, grid-breaking | Responsive grid implementation, flex/grid patterns |
| **Accessibility** | Color contrast, readability | ARIA, keyboard nav, screen reader testing |

**Handoff rule**: When a task spans both skills, `frontend-design` defines the aesthetic contract (tokens, visual direction, reference implementation), and `frontend-ui-engineering` implements it as production components. Do not duplicate work between the two.

## Style Input → Structured Output Rules

When the user provides a vague style direction, map it to concrete design decisions:

| User says | Interpret as | Key design choices |
|---|---|---|
| "高级感" / "premium" | Luxury / refined | Dark palette, high contrast accents, thin serif display font, generous whitespace, restrained animation |
| "科技感" / "techy" | Futuristic / digital | Monospace or geometric sans, neon or electric accents on dark, grid patterns, HUD-like UI elements |
| "清新" / "fresh" | Light / organic | Pastel palette, rounded forms, airy spacing, nature-inspired textures, playful but controlled animation |
| "专业" / "professional" | Corporate / authoritative | Neutral palette, strong type hierarchy, minimal decoration, data-first layout, subtle transitions |
| "有趣" / "fun" | Playful / expressive | Bold colors, hand-drawn or display fonts, asymmetric layout, bouncy animations, personality-rich copy |
| "简约" / "minimal" | Reductive / precise | 2-3 colors max, extreme whitespace, one distinctive font, near-zero decoration, surgical transitions |

If the user provides no style direction at all, **ask before designing**. Do not default to generic.

## Acceptance Criteria

A frontend-design output passes review when:

- [ ] The aesthetic direction is named and defended (not just "modern and clean")
- [ ] Font choices are specific, loaded, and not in the banned list (Inter, Roboto, Arial, system fonts)
- [ ] Color palette has at least 1 dominant + 1 accent color with stated contrast ratios
- [ ] Design tokens are defined as CSS custom properties
- [ ] The output renders in a browser without errors
- [ ] At least one micro-interaction or animation is present and purposeful
- [ ] Two distinct viewport sizes render appropriately (mobile + desktop)
- [ ] A reviewer could not guess "this was AI-generated" from visual inspection alone
