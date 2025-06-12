import React, { useState } from 'react';
import Modal from '../common/Modal'; // Adjust path if Modal.tsx is elsewhere, but assume it's in common
import TextField from '@mui/material/TextField'; // Using MUI TextField for consistency if used elsewhere
import Button from '../common/Button'; // Using common Button

export interface AddMoodBoardImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddUrl: (url: string) => void;
  title?: string;
}

const AddMoodBoardImageModal: React.FC<AddMoodBoardImageModalProps> = ({
  isOpen,
  onClose,
  onAddUrl,
  title = "Add Image to Mood Board",
}) => {
  const [imageUrl, setImageUrl] = useState<string>('');
  const [error, setError] = useState<string>('');

  const handleAddClick = () => {
    if (!imageUrl.trim()) {
      setError('Image URL cannot be empty.');
      return;
    }
    // Basic URL validation (can be enhanced)
    try {
      new URL(imageUrl); // This will throw if the URL is invalid
      setError('');
      onAddUrl(imageUrl);
      setImageUrl(''); // Clear input after adding
      onClose(); // Close modal after successful add
    } catch (_) {
      setError('Please enter a valid URL.');
    }
  };

  const handleModalClose = () => {
    setImageUrl(''); // Clear input on close
    setError('');    // Clear error on close
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleModalClose}
      title={title}
      size="md" // Or 'sm' if preferred for a simple input
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <TextField
          label="Image URL"
          variant="outlined"
          fullWidth
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
          error={!!error}
          helperText={error}
          autoFocus
        />
        <Button
          onClick={handleAddClick}
          variant="primary"
          // className="action-button" // Use variant for styling or ensure this class is globally available
        >
          Add URL
        </Button>
      </div>
    </Modal>
  );
};

export default AddMoodBoardImageModal;
