import React, { ReactNode, useEffect } from 'react';
import './Modal.css'; // Import the CSS file
import Button from './Button'; // Import Button for default close button in footer

export interface ModalProps {
  /** Is the modal currently open? */
  isOpen: boolean;
  /** Function to call when the modal is requested to be closed (e.g., by overlay click or close button) */
  onClose: () => void;
  /** Optional title for the modal header */
  title?: string;
  /** Content to be displayed inside the modal body */
  children: ReactNode;
  /** Optional additional CSS class to apply to the modal content wrapper */
  className?: string;
  /** Optional content for the modal footer (e.g., action buttons) */
  footerContent?: ReactNode;
  /** Optional size variant for the modal width */
  size?: 'sm' | 'md' | 'lg';
  /** Set to false to prevent closing when clicking the overlay */
  closeOnOverlayClick?: boolean;
}

/**
 * A reusable Modal component for displaying content in a focused overlay.
 * It handles the overlay, content box, header, body, footer, and close functionality.
 */
const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  className = '',
  footerContent,
  size = 'md', // Default size
  closeOnOverlayClick = true,
}) => {
  useEffect(() => {
    const body = document.body;
    if (isOpen) {
      body.style.overflow = 'hidden'; // Prevent background scrolling
    } else {
      body.style.overflow = 'auto';
    }
    // Cleanup function to restore body scroll if component unmounts while open
    return () => {
      body.style.overflow = 'auto';
    };
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  const handleOverlayClick = () => {
    if (closeOnOverlayClick) {
      onClose();
    }
  };

  const modalSizeClass = `modal-${size}`; // e.g., modal-md, modal-lg

  return (
    <div className={`modal-overlay ${isOpen ? 'modal-open' : ''}`} onClick={handleOverlayClick}>
      <div
        className={`modal-content-wrapper ${modalSizeClass} ${className}`}
        onClick={(e) => e.stopPropagation()} // Prevent click inside modal from closing it
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
      >
        {title && (
          <div className="modal-header">
            <h3 id="modal-title" className="modal-title">{title}</h3>
            <button onClick={onClose} className="modal-close-button" aria-label="Close modal">
              &times;
            </button>
          </div>
        )}
        {!title && ( /* Render close button differently if no title */
            <button 
                onClick={onClose} 
                className="modal-close-button" 
                aria-label="Close modal" 
                style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 1 }}
            >
              &times;
            </button>
        )}
        
        <div className="modal-body">
          {children}
        </div>
        
        {footerContent && (
          <div className="modal-footer">
            {footerContent}
          </div>
        )}
        {/* Example of a default footer if none provided:
        {!footerContent && (
          <div className="modal-footer">
            <Button variant="secondary" onClick={onClose}>Close</Button>
          </div>
        )}
        */}
      </div>
    </div>
  );
};

export default Modal;
