import React, { ReactNode, MouseEventHandler } from 'react';
import './Card.css'; // Import the CSS file

export interface CardProps {
  /** The content of the card */
  children: ReactNode;
  /** Optional additional CSS class to apply to the card */
  className?: string;
  /** Optional click handler if the whole card is clickable */
  onClick?: MouseEventHandler<HTMLDivElement>;
  /** If true, applies a hover effect. Useful for clickable cards. */
  interactive?: boolean;
  /** Optional content for a predefined card header section */
  headerContent?: ReactNode;
  /** Optional content for a predefined card footer section */
  footerContent?: ReactNode;
  /** Optional: Renders the card as an anchor tag if href is provided */
  href?: string;
  /** Optional: Standard HTML attributes for the anchor tag if href is provided */
  target?: string;
  rel?: string;
}

/**
 * A flexible Card component for displaying content in a structured manner.
 * Uses CSS variables for styling and includes optional header, body, and footer sections.
 */
const Card: React.FC<CardProps> = ({
  children,
  className = '',
  onClick,
  interactive = false,
  headerContent,
  footerContent,
  href,
  target,
  rel,
  ...props
}) => {
  const baseClass = 'card-component';
  const interactiveClass = interactive || onClick || href ? 'card-component-interactive' : '';
  const linkableClass = href ? 'card-component-linkable' : '';

  const classes = [baseClass, interactiveClass, linkableClass, className].filter(Boolean).join(' ');

  const cardContent = (
    <>
      {headerContent && <div className="card-header">{headerContent}</div>}
      <div className="card-body">{children}</div>
      {footerContent && <div className="card-footer">{footerContent}</div>}
    </>
  );

  if (href) {
    return (
      <a
        href={href}
        className={classes}
        onClick={onClick as unknown as MouseEventHandler<HTMLAnchorElement>} // Allow onClick even on link cards
        target={target}
        rel={rel || (target === '_blank' ? 'noopener noreferrer' : undefined)}
        {...props}
      >
        {cardContent}
      </a>
    );
  }

  return (
    <div
      className={classes}
      onClick={onClick}
      role={onClick ? 'button' : undefined} // Add role button if card is clickable
      tabIndex={onClick ? 0 : undefined} // Make clickable card focusable
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') onClick(e as any); } : undefined}
      {...props}
    >
      {cardContent}
    </div>
  );
};

export default Card;
