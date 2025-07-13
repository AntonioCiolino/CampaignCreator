import React from 'react';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
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
        <Modal show={show} onHide={onHide} centered size="lg">
            <Modal.Header closeButton>
                <Modal.Title>Memory Summary</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {loading && <LoadingSpinner />}
                {error && <div className="alert alert-danger">{error}</div>}
                {!loading && !error && (
                    <p className="pre-wrap">{summary || 'No summary available.'}</p>
                )}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={onHide}>
                    Close
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default MemorySummaryModal;
