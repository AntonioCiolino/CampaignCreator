import React, { MouseEventHandler } from 'react';
import './IconButton.css';

export interface IconButtonProps {
  onClick?: MouseEventHandler<HTMLButtonElement>;
  disabled?: boolean;
  className?: string;
  'aria-label': string;
  title?: string;
  icon: React.ReactNode;
}

const IconButton: React.FC<IconButtonProps> = ({
  onClick,
  disabled = false,
  className = '',
  'aria-label': ariaLabel,
  title,
  icon,
}) => {
  const classes = `icon-button ${className}`;

  return (
    <button
      type="button"
      className={classes}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      title={title}
    >
      {icon}
    </button>
  );
};

export default IconButton;
