import React, { MouseEventHandler } from 'react';
import './IconButton.css';
import Tooltip from './Tooltip'; // Assuming Tooltip component exists

export interface IconButtonProps {
  onClick?: MouseEventHandler<HTMLButtonElement>;
  disabled?: boolean;
  className?: string;
  'aria-label': string;
  title?: string;
  icon: React.ReactNode;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'danger';
  tooltip?: string;
}

const IconButton: React.FC<IconButtonProps> = ({
  onClick,
  disabled = false,
  className = '',
  'aria-label': ariaLabel,
  title,
  icon,
  size = 'medium',
  variant = 'default',
  tooltip,
}) => {
  const classes = `icon-button icon-button-${size} icon-button-${variant} ${className}`;

  const button = (
    <button
      type="button"
      className={classes}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      title={title} // Keep title for accessibility, though tooltip might override visually
    >
      {icon}
    </button>
  );

  if (tooltip) {
    return <Tooltip text={tooltip}>{button}</Tooltip>;
  }

  return button;
};

export default IconButton;
