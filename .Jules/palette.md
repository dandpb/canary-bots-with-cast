# Palette's Journal - Critical Learnings

## 2026-11-08 - Accessible Map Floor Controls
**Learning:** Embedded web map controls (such as Leaflet/custom map floor navigation steppers) often render icon/symbol-only buttons (`&minus;`, `&plus;`) and live numeric displays without proper screen reader labels and live regions. While tooltips provide mouse affordances, screen readers need explicit `aria-label`s on stepper buttons, `aria-live="polite"` on active floor indicators, and keyboard `:focus-visible` outlines matching the retro/vintage UI palette.
**Action:** When adding or enhancing custom map widgets and compact toolbar steppers, ensure icon/symbol buttons have explicit `aria-label`s, dynamic coordinate/floor values announce updates via polite live regions, and `.wm-btn:focus-visible` styles maintain clear visual affordances without disrupting default mouse clicks.
