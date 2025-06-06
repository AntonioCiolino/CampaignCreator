import React from 'react';
import Modal from '../common/Modal'; // Assuming a generic Modal component exists
import Button from '../common/Button'; // For a close button
import './ImagePreviewModal.css'; // For custom styling

interface ImagePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string | null;
  imageAlt?: string;
}

const ImagePreviewModal: React.FC<ImagePreviewModalProps> = ({
  isOpen,
  onClose,
  imageUrl,
  imageAlt = 'Image Preview',
}) => {
  if (!isOpen || !imageUrl) {
    return null;
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Image Preview">
      <div className="image-preview-modal-content">
        <img src={imageUrl} alt={imageAlt} className="image-preview-modal-image" />
      </div>
      <div className="image-preview-modal-actions">
        <Button onClick={onClose} variant="secondary">
          Close
        </Button>
      </div>
    </Modal>
  );
};

export default ImagePreviewModal;
