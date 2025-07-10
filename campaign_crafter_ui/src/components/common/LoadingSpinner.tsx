import React from 'react';
import './LoadingSpinner.css';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'; // Optional size prop
  inline?: boolean; // Optional: if true, doesn't use overlay
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', inline = false }) => {
  const spinnerClassName = `loading-spinner ${size}`;

  if (inline) {
    return <div className={spinnerClassName} data-testid="loading-spinner"></div>;
  }

  return (
    <div className="loading-spinner-overlay" data-testid="loading-spinner-overlay">
      <div className={spinnerClassName} data-testid="loading-spinner"></div>
    </div>
  );
};

export default LoadingSpinner;
