import React from 'react';
import Modal from '../common/Modal'; // Assuming a base Modal component exists
import Button from '../common/Button'; // Assuming a base Button component exists
import './ConfirmationModal.css';

interface ConfirmationModalProps {
    isOpen: boolean;
    title: string;
    message: string | React.ReactNode;
    onConfirm: () => void;
    onCancel: () => void;
    confirmButtonText?: string;
    cancelButtonText?: string;
    isConfirming?: boolean;
    confirmButtonVariant?: 'primary' | 'danger' | 'success' | 'warning' | 'info' | 'secondary'; // Matches common button variants
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
    isOpen,
    title,
    message,
    onConfirm,
    onCancel,
    confirmButtonText = 'Confirm',
    cancelButtonText = 'Cancel',
    isConfirming = false,
    confirmButtonVariant = 'primary',
}) => {
    if (!isOpen) {
        return null;
    }

    return (
        <Modal isOpen={isOpen} onClose={onCancel} title={title}>
            <div className="confirmation-modal-content">
                {typeof message === 'string' ? <p>{message}</p> : message}
            </div>
            <div className="confirmation-modal-actions">
                <Button
                    onClick={onCancel}
                    disabled={isConfirming}
                    variant="secondary" // Or a specific "cancel" variant if your Button component supports it
                    className="me-2"
                >
                    {cancelButtonText}
                </Button>
                <Button
                    onClick={onConfirm}
                    // isLoading={isConfirming} // Button.tsx does not have isLoading prop
                    disabled={isConfirming} // Use disabled prop instead
                    variant={confirmButtonVariant}
                >
                    {isConfirming ? 'Processing...' : confirmButtonText}
                    {/* Optionally change text when confirming */}
                </Button>
            </div>
        </Modal>
    );
};

export default ConfirmationModal;
