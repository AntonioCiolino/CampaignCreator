import React from 'react';
import './AlertMessage.css'; // CSS for styling the alert

interface AlertMessageProps {
    message: string | null;
    type: 'success' | 'error' | 'warning' | 'info';
    onClose?: () => void; // Optional: If the alert should be dismissible
}

const AlertMessage: React.FC<AlertMessageProps> = ({ message, type, onClose }) => {
    if (!message) {
        return null;
    }

    const alertTypeClass = `alert-${type}`;

    return (
        <div className={`alert-message ${alertTypeClass}`} role="alert">
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
