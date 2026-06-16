# Decent Visualizer Design Language

## Philosophy

The chart is the hero. The UI is a frame that stays out of the way. Dense but not cluttered. Every element earns its pixels. Dark-first, with semantic tokens that support a future light mode.

**Stack:** Tailwind CSS v4, Base UI (unstyled React components).

## Color Palette

### Dark Mode (Primary)

| Role | Token | Value | Tailwind | Usage |
|---|---|---|---|---|
| Background | `--color-bg-base` | #000000 | `black` | Page background |
| Surface | `--color-bg-surface` | #0a0a0a | `neutral-950` | Cards, panels |
| Surface raised | `--color-bg-raised` | #171717 | `neutral-900` | Hover states, elevated panels |
| Border | `--color-border-default` | #404040 | `neutral-700` | Dividers, card edges |
| Border subtle | `--color-border-subtle` | #262626 | `neutral-800` | Chart gridlines, faint separators |
| Text primary | `--color-text-primary` | #fafafa | `neutral-50` | Headings, key values |
| Text secondary | `--color-text-secondary` | #a3a3a3 | `neutral-400` | Labels, descriptions |
| Text muted | `--color-text-muted` | #525252 | `neutral-600` | Timestamps, tertiary info |

### Chart Line Colors

Chosen for dark-background contrast and colorblind safety.

| Series | Token | Hex | Tailwind |
|---|---|---|---|
| Pressure | `--color-chart-pressure` | #38bdf8 | `sky-400` |
| Flow | `--color-chart-flow` | #a78bfa | `violet-400` |
| Temperature | `--color-chart-temp` | #fb923c | `orange-400` |
| Weight | `--color-chart-weight` | #4ade80 | `green-400` |
| Target/goal lines | -- | Dashed, same hue at 50% opacity | |

### Accent Colors

| Role | Token | Value | Tailwind |
|---|---|---|---|
| Interactive | `--color-accent` | #38bdf8 | `sky-400` |
| Interactive hover | `--color-accent-hover` | #7dd3fc | `sky-300` |
| Destructive | `--color-destructive` | #f87171 | `red-400` |
| Success | `--color-success` | #4ade80 | `green-400` |

## Typography

- **Font:** System font stack. `font-sans` in Tailwind (no web font load).
- **Scale:** Constrained to a small set from Tailwind's defaults:
  - `text-2xl font-semibold` -- page titles (rare)
  - `text-lg font-medium` -- section heads, shot date
  - `text-sm` -- most body text, labels, metadata
  - `text-xs` -- chart axis labels, timestamps, tertiary info
- **Numeric data:** `font-mono tabular-nums` for dose, yield, ratio, duration so digits align.

## Spacing and Layout

- **Max width:** `max-w-6xl` for main content area.
- **Grid:** 12-column CSS grid for dashboard layouts. Chart takes 8 cols, metadata sidebar takes 4.
- **Card padding:** `p-4` standard, `p-3` compact (chart controls).
- **Section gaps:** `gap-4` between cards, `gap-6` between major sections.
- **Border radius:** `rounded-lg` for cards, `rounded-md` for buttons and inputs.

## Component Patterns

### Cards

`bg-(--color-bg-surface) border border-(--color-border-default) rounded-lg`. No box-shadow on dark mode (shadows don't read well). Subtle border instead.

### Buttons (Base UI)

- **Primary:** `bg-(--color-accent)` background, dark text. Hover uses `--color-accent-hover`.
- **Secondary:** Ghost/outline on `bg-(--color-bg-raised)`. Border `--color-border-default`.
- **Size:** Small by default: `text-sm px-3 py-1.5`.
- **Border radius:** `rounded-md`.

### Inputs (Base UI)

`bg-(--color-bg-raised) border-(--color-border-default)` with `text-(--color-text-primary)`. Focus ring in `--color-accent`.

### Tables and Lists

No zebra striping. Use `border-b border-(--color-border-subtle)` between rows. Compact row height.

### Chart Container

Full-bleed within its card. Minimal chrome. Axis labels in `text-(--color-text-muted) text-xs`. Grid lines in `--color-border-subtle`.

## Key UI Regions

1. **Nav bar** -- Slim, fixed top. `bg-(--color-bg-surface) border-b border-(--color-border-default)`. Logo left, auth controls right.
2. **Shot list** -- Table or card list. Each row: date, profile name, dose/yield, duration. Click to open detail.
3. **Shot detail** -- Chart dominates top 60% of viewport. Below: metadata in a two-column grid (brew params left, notes right).
4. **Empty/loading states** -- Skeleton loaders using `bg-(--color-bg-raised) animate-pulse rounded`.

## Future Light Mode

All semantic tokens are defined as CSS custom properties in Tailwind v4's `@theme` block. Swapping to light mode means redefining those properties under a `.light` class or `prefers-color-scheme: light` media query. No component code changes needed.
