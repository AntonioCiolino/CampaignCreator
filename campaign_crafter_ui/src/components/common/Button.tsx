import React, { MouseEventHandler, ReactNode } from 'react';
import './Button.css'; // Import the CSS file

export type ButtonVariant = 
  | 'primary' 
  | 'secondary' 
  | 'success' 
  | 'danger' 
  | 'warning' 
  | 'info' 
  | 'link'
  | 'outline-primary'
  | 'outline-secondary'; // Add more outline variants as needed

export type ButtonSize = 'sm' | 'md' | 'lg';
export type ButtonType = 'button' | 'submit' | 'reset';

export interface ButtonProps {
  /** Content to be displayed inside the button */
  children: ReactNode;
  /** Click handler */
  onClick?: MouseEventHandler<HTMLButtonElement>;
  /** Which style variant to use */
  variant?: ButtonVariant;
  /** How large should the button be? */
  size?: ButtonSize;
  /** Is the button disabled? */
  disabled?: boolean;
  /** Optional additional CSS classes to apply */
  className?: string;
  /** HTML button type attribute */
  type?: ButtonType;
  /** Make the button a full-width block element */
  isBlock?: boolean;
  /** Optional: For 'link' variant, the URL to navigate to. If provided, renders as an <a> tag. */
  href?: string;
  /** Optional: For 'link' variant, target attribute for the <a> tag. */
  target?: string;
  /** Optional: For 'link' variant, rel attribute for the <a> tag. */
  rel?: string;
  /** Optional: Inline styles to apply to the button */
  style?: React.CSSProperties; // Added style prop
  /** Optional: Icon to display in the button */
  icon?: ReactNode;
  /** Optional: Tooltip text to display on hover */
  tooltip?: string;
}

/**
 * Primary UI component for user interaction.
 * Styled using CSS variables and dedicated CSS file.
 */
const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary', // Default variant
  size = 'md',       // Default size
  disabled = false,
  className = '',
  type = 'button',
  isBlock = false,
  href,
  target,
  rel,
  style, // Explicitly destructure style
  icon,
  tooltip,
  ...props // Spread any other native button props like aria-label, etc.
}) => {
  const baseClass = 'btn';
  const variantClass = `btn-${variant}`;
  const sizeClass = size !== 'md' ? `btn-${size}` : ''; // Only add size class if not medium (md is default via CSS)
  const blockClass = isBlock ? 'btn-block' : '';
  const disabledClass = disabled ? 'disabled' : ''; // CSS might handle this via :disabled pseudo-class too

  const classes = [baseClass, variantClass, sizeClass, blockClass, disabledClass, className]
    .filter(Boolean) // Remove any empty strings
    .join(' ');

  if (href) {
    // Render as an anchor tag if href is provided
    return (
      <a
        href={href}
        className={classes}
        onClick={onClick as unknown as MouseEventHandler<HTMLAnchorElement>} // Cast needed if onClick expects button event
        target={target}
        rel={rel || (target === '_blank' ? 'noopener noreferrer' : undefined)} // Common security for _blank links
        role="button" // ARIA role for accessibility
        aria-disabled={disabled}
        title={tooltip}
        style={{ ...(disabled ? { pointerEvents: 'none', opacity: 0.65 } : {}), ...style }} // Merge disabled styles with provided style
        {...props}
      >
        {icon && <span className="btn-icon" style={{ marginRight: children ? '0.5em' : '0' }}>{icon}</span>}
        {children}
      </a>
    );
  }

  return (
    <button
      type={type}
      className={classes}
      onClick={onClick}
      disabled={disabled}
      title={tooltip}
      style={style}
      {...props} // Spread other props
    >
      {icon && <span className="btn-icon" style={{ marginRight: children ? '0.5em' : '0' }}>{icon}</span>}
      {children}
    </button>
  );
};

export default Button;
