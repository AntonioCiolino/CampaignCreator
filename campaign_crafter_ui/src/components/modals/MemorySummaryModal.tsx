import React from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';

interface MemorySummaryModalProps {
    show: boolean;
    onHide: () => void;
    summary: string | null;
    loading: boolean;
    error: string | null;
}

const MemorySummaryModal: React.FC<MemorySummaryModalProps> = ({ show, onHide, summary, loading, error }) => {
    return (
        <Modal
            isOpen={show}
            onClose={onHide}
            title="Memory Summary"
            size="lg"
            footerContent={<Button onClick={onHide}>Close</Button>}
        >
            {loading && <LoadingSpinner />}
            {error && <div className="alert alert-danger">{error}</div>}
            {!loading && !error && (
                <p className="pre-wrap">{summary || 'No summary available.'}</p>
            )}
        </Modal>
    );
};

export default MemorySummaryModal;
