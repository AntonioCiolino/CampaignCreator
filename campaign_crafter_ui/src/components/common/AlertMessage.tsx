import React from 'react';
import './AlertMessage.css'; // CSS for styling the alert

interface AlertMessageProps {
    message: string | null;
    type: 'success' | 'error' | 'warning' | 'info';
    onClose?: () => void; // Optional: If the alert should be dismissible
    className?: string; // Allow passing custom CSS classes
}

const AlertMessage: React.FC<AlertMessageProps> = ({ message, type, onClose, className = '' }) => {
    if (!message) {
        return null;
    }

    const alertTypeClass = `alert-${type}`;
    const combinedClassNames = `alert-message ${alertTypeClass} ${className}`.trim();

    return (
        <div className={combinedClassNames} role="alert">
            <span>{message}</span>
            {onClose && (
                <button
                    type="button"
                    className="alert-close-btn"
                    aria-label="Close"
                    onClick={onClose}
                >
                    &times; {/* HTML entity for 'X' (close icon) */}
                </button>
            )}
        </div>
    );
};

export default AlertMessage;
