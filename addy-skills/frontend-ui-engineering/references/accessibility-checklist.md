# Accessibility Checklist

WCAG 2.1 AA compliance checklist for frontend engineering. Use alongside the main `frontend-ui-engineering` skill.

## Perceivable

### Text Alternatives

- [ ] All images have descriptive `alt` text (or `alt=""` for decorative images)
- [ ] Icon buttons have `aria-label` or visually hidden text
- [ ] Complex images (charts, diagrams) have extended descriptions
- [ ] Audio/video content has captions or text alternatives

### Color and Contrast

- [ ] Text: ≥ 4.5:1 contrast ratio (normal text)
- [ ] Large text (≥18pt or ≥14pt bold): ≥ 3:1 contrast ratio
- [ ] UI components and graphical objects: ≥ 3:1 contrast ratio
- [ ] Color is never the sole means of conveying information
- [ ] Focus indicators are clearly visible (not just color change)

### Content Structure

- [ ] Single `<h1>` per page; heading levels are sequential (no skipping h2 → h4)
- [ ] Lists use `<ul>`, `<ol>`, or `<dl>` — not styled `<div>`s
- [ ] Tables use `<th>`, `scope`, and `<caption>` for data tables
- [ ] Layout tables are not used (use CSS grid/flexbox instead)
- [ ] Reading order matches visual order in the DOM

## Operable

### Keyboard

- [ ] All interactive elements reachable via Tab key
- [ ] Tab order follows logical reading/interaction order
- [ ] Enter activates buttons and links; Space toggles checkboxes
- [ ] Escape closes modals, dropdowns, and popups
- [ ] Arrow keys navigate within composite widgets (tabs, menus, listboxes)
- [ ] No keyboard traps (user can always Tab away from any element)
- [ ] Skip navigation link provided for long pages

### Focus Management

- [ ] Focus moves to modal/dialog when opened
- [ ] Focus returns to triggering element when modal closes
- [ ] Focus is trapped inside open modals (cannot Tab to background content)
- [ ] Focus is visible at all times (custom `:focus-visible` styles provided)
- [ ] Programmatic focus changes use `tabIndex={-1}` on non-interactive targets
- [ ] Focus is not lost after dynamic content updates (list reorder, item deletion)

### Timing and Motion

- [ ] No time limits on user actions (or extendable/adjustable if unavoidable)
- [ ] Auto-playing content can be paused, stopped, or hidden
- [ ] Animations respect `prefers-reduced-motion` media query
- [ ] No content flashes more than 3 times per second

## Understandable

### Forms

- [ ] Every input has a visible `<label>` (or `aria-label` / `aria-labelledby`)
- [ ] Required fields are indicated (not by color alone)
- [ ] Error messages identify the field and describe the problem
- [ ] Error messages are associated with fields via `aria-describedby`
- [ ] Form validation errors announced to screen readers (`role="alert"` or live region)
- [ ] Instructions appear before the form, not only after submission failure

### Language and Readability

- [ ] `lang` attribute set on `<html>` element
- [ ] Language changes within content marked with `lang` attribute
- [ ] Error messages use plain language (not error codes)
- [ ] Link text is descriptive ("View task details" not "Click here")

## Robust

### Semantic HTML

- [ ] Interactive elements use semantic tags (`<button>`, `<a>`, `<input>`)
- [ ] Custom widgets use appropriate ARIA roles (`role="dialog"`, `role="tablist"`)
- [ ] ARIA states kept in sync with visual state (`aria-expanded`, `aria-selected`, `aria-checked`)
- [ ] `aria-live` used for dynamic content updates (errors, notifications, loading states)
- [ ] No duplicate `id` attributes
- [ ] HTML validates without errors

### Screen Reader Testing

- [ ] Page title announced on navigation
- [ ] Headings provide meaningful page outline
- [ ] Landmark regions defined (`<nav>`, `<main>`, `<aside>`, `<footer>`)
- [ ] Dynamic content updates announced (live regions, `aria-live`)
- [ ] Loading states communicated (`aria-busy`, status messages)

## Testing Tools

```bash
# Automated (catches ~30-40% of issues)
npx axe-core             # CLI accessibility audit
# Lighthouse → Accessibility tab
# eslint-plugin-jsx-a11y  # Lint-time checks for React

# Semi-automated
# Chrome DevTools → Accessibility tree panel
# Chrome DevTools → Rendering → Emulate vision deficiencies

# Manual (catches the other 60-70%)
# Tab through the entire page
# Navigate with VoiceOver (macOS: Cmd+F5) or NVDA (Windows)
# Use screen magnification at 200%
# Test with high-contrast mode
```

## Common Failures and Fixes

| Failure | Impact | Fix |
|---|---|---|
| Image without `alt` | Screen reader says "image" with no context | Add descriptive `alt` or `alt=""` for decorative |
| `<div onClick>` instead of `<button>` | Not keyboard accessible, no screen reader announcement | Use `<button>` |
| Missing form labels | Screen reader users don't know what the field is for | Add `<label htmlFor>` or `aria-label` |
| Low contrast text | Unreadable for low-vision users | Ensure ≥ 4.5:1 ratio |
| Focus lost after action | Keyboard user stranded on page | Manage focus programmatically |
| Auto-playing animation | Motion sickness, distraction | Respect `prefers-reduced-motion` |
| Modal without focus trap | Keyboard user can interact with hidden background | Trap focus inside modal |
| Status update without `aria-live` | Screen reader misses dynamic content | Add `aria-live="polite"` or `role="status"` |
