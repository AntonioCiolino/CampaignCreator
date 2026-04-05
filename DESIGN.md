# Campaign Crafter UI Design System

> Agent-friendly design specification for AI coding assistants.
> This file documents the visual design system used throughout the Campaign Crafter web application.

## Overview

Campaign Crafter is a tabletop RPG campaign creation tool with a dynamic theming system. Each campaign can override the default design tokens via CSS custom properties. The UI uses vanilla CSS (no Tailwind), component-scoped CSS files, and a shared component library in `components/common/`.

---

## Theming Architecture

Campaign Crafter supports per-campaign theming via CSS custom properties. The cascade is:

1. Hardcoded fallbacks in CSS
2. Default variables defined on `body` in `index.css` (e.g., `--campaign-primary-color-default`)
3. Campaign-specific overrides set at runtime via `themeUtils.ts` (e.g., `--campaign-primary-color`)

Components should always reference the campaign variable first, falling back to the default:

```css
color: var(--campaign-primary-color, var(--campaign-primary-color-default));
```

### Theme Properties (set via `themeUtils.ts`)

| CSS Variable | Purpose | Default |
|---|---|---|
| `--campaign-primary-color` | Primary brand color | `#007bff` |
| `--campaign-secondary-color` | Secondary actions | `#6c757d` |
| `--campaign-background-color` | Page background | `#ffffff` |
| `--campaign-text-color` | Body text | `#212529` |
| `--campaign-font-family` | Font stack | System sans-serif |
| `--campaign-background-image-url` | Background image | none |
| `--campaign-background-image-opacity` | Background image opacity | `1` |
| `--campaign-text-color-on-primary` | Text on primary bg | `#ffffff` |
| `--campaign-text-color-on-secondary` | Text on secondary bg | `#ffffff` |
| `--campaign-border-color` | Border color | `#dee2e6` |

---

## Color System

### Core Palette (App.css `:root`)

| Token | Hex | Usage |
|-------|-----|-------|
| `--primary-color` | `#007bff` | Primary buttons, links, focus rings |
| `--primary-color-dark` | `#0056b3` | Primary hover states |
| `--secondary-color` | `#6c757d` | Secondary buttons, disabled states |
| `--secondary-color-dark` | `#5a6268` | Secondary hover |
| `--success-color` | `#28a745` | Success messages, create buttons |
| `--danger-color` | `#dc3545` | Error messages, destructive actions |
| `--warning-color` | `#ffc107` | Warning alerts |
| `--info-color` | `#17a2b8` | Informational elements |

### Surface and Background

| Token | Hex | Usage |
|-------|-----|-------|
| `--background-color` | `#f8f9fa` | Page background |
| `--surface-color` | `#ffffff` | Cards, modals, form backgrounds |
| `--border-color` | `#dee2e6` | Borders, dividers |

### Text Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--text-color` | `#212529` | Primary body text |
| `--text-color-muted` | `#6c757d` | Secondary text, metadata |

### Alert Colors (light backgrounds with dark text)

| Variant | Background | Text | Border |
|---------|------------|------|--------|
| Success | `#d4edda` | `#155724` | `#c3e6cb` |
| Error | `#f8d7da` | `#721c24` | `#f5c6cb` |
| Warning | `#fff3cd` | `#856404` | `#ffeeba` |
| Info | `#d1ecf1` | `#0c5460` | `#bee5eb` |

---

## Typography

### Font Families

```css
/* Primary */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
  'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;

/* Monospace */
font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New', monospace;
```

### Type Scale

| Element | Size | Weight | Usage |
|---------|------|--------|-------|
| h1 | `2.25rem` (mobile: `2rem`) | 500 | Page titles |
| h2 | `1.8rem` (mobile: `1.6rem`) | 500 | Section titles |
| h3 | `1.5rem` (mobile: `1.3rem`) | 500 | Subsection titles |
| h4 | `1.25rem` (mobile: `1.1rem`) | 500 | Card titles |
| Body | `1rem` (16px) | 400 | Default text |
| Small | `0.875rem` | 400 | Badges, helper text |
| Caption | `0.85rem` | 400 | Feedback messages |

### Line Height

- Base: `1.6` (generous for readability)
- Headings: `1.3` (tighter)

---

## Spacing

### Base Unit

No formal spacing scale. Common values used throughout:

| Value | Usage |
|-------|-------|
| `0.25rem` (4px) | Tight gaps, error message margins |
| `0.5rem` (8px) | Button padding (vertical), small gaps |
| `0.75rem` (12px) | Card header/footer padding, form label margin |
| `1rem` (16px) | Standard gap, form group margin, section spacing |
| `1.25rem` (20px) | Card padding |
| `1.5rem` (24px) | Modal padding, section gaps |
| `20px` | Main content padding |

### Common Patterns

- Card padding: `1.25rem`
- Button padding: `0.5rem 1rem` (default), `0.75rem 1.5rem` (large), `0.25rem 0.5rem` (small)
- Form input padding: `0.5rem 0.75rem`
- Modal padding: `1rem 1.5rem` (header/footer), `1.5rem` (body)
- Page container: `width: 90%; max-width: 1200px; margin: auto`

---

## Layout

### Page Structure

```
.app-layout (flex column, min-height: 100vh)
├── .app-header (dark bar, #333 background)
│   ├── Logo + Title (left)
│   └── User actions / Login (right)
├── .app-main-content (flex-grow: 1, padding: 20px)
│   └── Page content
└── .app-footer (light gray, centered)
```

### Container

```css
.container {
  width: 90%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}
```

### Grid Patterns

- Campaign grid: `grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem`
- Horizontal scroll: `display: flex; overflow-x: auto; gap: 1rem`
- Card widths in scroll: `300px` (mobile), `320px` (tablet), `340px` (desktop)

---

## Components

### Card (`components/common/Card`)

```css
.card-component {
  background-color: var(--campaign-card-background-color, var(--campaign-background-color, ...));
  border: 1px solid var(--campaign-border-color, ...);
  border-radius: 0.3rem;
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
}

/* Interactive hover */
.card-component-interactive:hover {
  box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}
```

Structure: `.card-header` → `.card-body` → `.card-footer` (all optional, hide when empty)

### Button (`components/common/Button`)

Variants: `btn-primary`, `btn-secondary`, `btn-success`, `btn-danger`, `btn-warning`, `btn-info`, `btn-link`, `btn-outline-primary`

Sizes: `btn-sm` (0.25rem 0.5rem), default (0.5rem 1rem), `btn-lg` (0.75rem 1.5rem)

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  border: 1px solid transparent;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  border-radius: 0.3rem;
  transition: color 0.15s, background-color 0.15s, border-color 0.15s, box-shadow 0.15s;
}
```

Disabled: `opacity: 0.65; cursor: not-allowed`

### Alert Message (`components/common/AlertMessage`)

```css
.alert-message {
  padding: 0.75rem 1.25rem;
  border: 1px solid transparent;
  border-radius: 0.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
```

Variants: `.alert-success`, `.alert-error`, `.alert-warning`, `.alert-info`

### Modal (`components/common/Modal`)

```css
.modal-overlay {
  background-color: rgba(0, 0, 0, 0.65);
  z-index: 1050;
  /* Fade in/out with opacity transition */
}

.modal-content-wrapper {
  background: white;
  border-radius: 0.5rem;
  max-width: 600px; /* default, .modal-lg: 800px, .modal-sm: 400px */
  max-height: 90vh;
  /* Scale transition on open */
}
```

Structure: `.modal-header` → `.modal-body` (scrollable) → `.modal-footer` (right-aligned buttons)

### Form Inputs

```css
.form-input, .form-textarea, .form-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 0.3rem;
  font-size: 1rem;
  width: 100%;
}

/* Focus */
:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}
```

Mobile: inputs get `0.75rem 1rem` padding for larger touch targets.

### Loading Spinner (`components/common/LoadingSpinner`)

Centered spinner with configurable size.

### Tabs (`components/common/Tabs`)

Tab navigation component for switching between content panels.

### Tooltip (`components/common/Tooltip`)

Hover-triggered tooltip for additional context.

### Collapsible Section (`components/common/CollapsibleSection`)

Expandable/collapsible content sections with header toggle.

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--border-radius` | `0.3rem` (4.8px) | Default (buttons, inputs, cards) |
| `--border-radius-lg` | `0.5rem` (8px) | Modals |
| Small | `4px` | Badge images, context menus |

---

## Shadows

| Name | Value | Usage |
|------|-------|-------|
| `--box-shadow` | `0 0.125rem 0.25rem rgba(0,0,0,0.075)` | Cards, default elevation |
| Card hover | `0 0.25rem 0.75rem rgba(0,0,0,0.1)` | Interactive card hover |
| Modal | `0 5px 15px rgba(0,0,0,0.2)` | Modal dialogs |
| Login card | `0 4px 12px rgba(0,0,0,0.1)` | Centered login card |

---

## Animations and Transitions

```css
/* Default transition (buttons, links, inputs) */
transition: color 0.15s ease-in-out,
            background-color 0.15s ease-in-out,
            border-color 0.15s ease-in-out,
            box-shadow 0.15s ease-in-out;

/* Card hover */
transition: box-shadow 0.2s ease-in-out, transform 0.2s ease-in-out;

/* Modal overlay */
transition: opacity 0.3s ease-in-out, visibility 0.3s ease-in-out;

/* Modal content */
transition: transform 0.3s ease-in-out;

/* Badge image pop on card hover */
transform: scale(1.08);
```

---

## Responsive Breakpoints

| Breakpoint | Usage |
|------------|-------|
| `480px` | Quill toolbar wrapping |
| `576px` | Campaign grid single column |
| `600px` | Card width adjustments |
| `768px` | Mobile layout changes, font size adjustments |
| `992px` | Desktop card widths |

### Mobile Considerations

- Font size reduces to `15px` base on mobile
- Heading sizes scale down proportionally
- Form inputs and buttons get larger padding for touch targets
- Container padding reduces to `10px`
- Campaign grid collapses to single column below `576px`

---

## File Structure

```
campaign_crafter_ui/src/
├── App.css                    # Global variables, resets, base styles
├── index.css                  # Theme variable defaults, background image support
├── utils/themeUtils.ts        # Runtime theme application
├── components/
│   ├── common/                # Shared component library
│   │   ├── Button.tsx + .css
│   │   ├── Card.tsx + .css
│   │   ├── AlertMessage.tsx + .css
│   │   ├── Modal.tsx + .css
│   │   ├── Input.tsx + .css
│   │   ├── Layout.tsx + .css
│   │   ├── LoadingSpinner.tsx + .css
│   │   ├── Tabs.tsx + .css
│   │   ├── Tooltip.tsx + .css
│   │   └── CollapsibleSection.tsx + .css
│   └── [feature]/             # Feature-specific components
├── pages/                     # Page components with co-located CSS
└── views/                     # View components with co-located CSS
```

---

## Usage Notes for AI Agents

When generating UI code for Campaign Crafter:

1. **Use vanilla CSS** with component-scoped `.css` files (no Tailwind, no CSS-in-JS)
2. **Use CSS custom properties** for colors, always with the campaign variable cascade:
   ```css
   color: var(--campaign-primary-color, var(--campaign-primary-color-default));
   ```
3. **Use the shared components** from `components/common/` (Button, Card, AlertMessage, Modal, Input, etc.)
4. **Follow the naming convention**: `.component-name`, `.component-name-variant`
5. **Include responsive styles** with `@media (max-width: 768px)` at minimum
6. **Ensure touch-friendly targets** on mobile (minimum padding `0.75rem` for buttons/inputs)
7. **Use the existing color tokens** from `:root` in App.css, don't introduce new hex values
8. **Cards should use** the `Card` component or follow `.card-component` patterns
9. **Buttons should use** the `Button` component with appropriate variant class
10. **Alerts should use** the `AlertMessage` component with `success`, `error`, `warning`, or `info` type
