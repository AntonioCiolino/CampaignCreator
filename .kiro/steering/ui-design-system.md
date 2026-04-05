---
inclusion: fileMatch
fileMatchPattern: "campaign_crafter_ui/src/**/*.{tsx,ts,css}"
---

# UI Design System Guidelines

When working on UI components in Campaign Crafter, follow the design system documented in `#[[file:DESIGN.md]]`.

## Quick Reference

### Styling Approach
- Vanilla CSS with component-scoped `.css` files (no Tailwind)
- CSS custom properties for theming with campaign variable cascade
- Shared components in `components/common/`

### Color Variables (always use the cascade pattern)
```css
color: var(--campaign-primary-color, var(--campaign-primary-color-default));
background-color: var(--campaign-background-color, var(--campaign-background-color-default));
```

### Core Colors (from App.css :root)
- Primary: `--primary-color: #007bff`
- Success: `--success-color: #28a745`
- Danger: `--danger-color: #dc3545`
- Warning: `--warning-color: #ffc107`
- Info: `--info-color: #17a2b8`
- Text: `--text-color: #212529`
- Muted: `--text-color-muted: #6c757d`
- Border: `--border-color: #dee2e6`

### Shared Components
- `Button` - variants: primary, secondary, success, danger, warning, info, link, outline-primary
- `Card` - with optional header, body, footer sections
- `AlertMessage` - types: success, error, warning, info
- `Modal` - with header, body, footer; sizes: default, lg, sm
- `Input`, `FileInput`, `Checkbox` - form controls
- `LoadingSpinner`, `Tabs`, `Tooltip`, `CollapsibleSection`

### Spacing
- Card padding: `1.25rem`
- Button padding: `0.5rem 1rem`
- Form input padding: `0.5rem 0.75rem`
- Container: `width: 90%; max-width: 1200px`

### Responsive
- Always include `@media (max-width: 768px)` styles
- Larger touch targets on mobile (min `0.75rem` padding)
