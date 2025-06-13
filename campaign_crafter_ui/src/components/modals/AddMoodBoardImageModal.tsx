import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import TextField from '@mui/material/TextField';
import Button from '../common/Button';
import { uploadMoodboardImageApi } from '../../services/imageService'; // Import the new service

export interface AddMoodBoardImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddUrl: (url: string) => void;
  campaignId?: string; // Made campaignId optional
  onInitiateGenerateImage?: () => void; // New optional prop
  title?: string;
}

const AddMoodBoardImageModal: React.FC<AddMoodBoardImageModalProps> = ({
  isOpen,
  onClose,
  onAddUrl,
  campaignId, // Destructure campaignId
  onInitiateGenerateImage, // Destructure new prop
  title = "Add Image to Mood Board",
}) => {
  const [imageUrl, setImageUrl] = useState<string>('');
  const [error, setError] = useState<string>(''); // General error for URL pasting
  type View = 'choice' | 'upload' | 'pasteUrl';
  const [currentView, setCurrentView] = useState<View>('choice');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Effect to clear upload-specific states when view changes or modal closes
  useEffect(() => {
    if (!isOpen || currentView !== 'upload') {
      setSelectedFile(null);
      setIsUploading(false);
      setUploadError(null);
    }
  }, [isOpen, currentView]);

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
    setImageUrl('');
    setError('');
    // selectedFile, isUploading, uploadError are reset by useEffect or handleBackToChoice
    setCurrentView('choice');
    onClose();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null); // Clear previous upload error on new file selection
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    } else {
      setSelectedFile(null);
    }
  };

  const handleUploadClick = async () => {
    if (selectedFile && campaignId) {
      setIsUploading(true);
      setUploadError(null);
      try {
        const response = await uploadMoodboardImageApi(campaignId, selectedFile);
        onAddUrl(response.imageUrl); // Pass the new URL to the parent
        // Reset states before closing
        setSelectedFile(null);
        setIsUploading(false);
        onClose(); // Close modal on success
      } catch (err: any) {
        console.error("Upload failed:", err);
        setUploadError(err.message || "Failed to upload image. Please try again.");
        setIsUploading(false);
      }
    }
  };

  const handleBackToChoice = () => {
    // Reset all view-specific states when going back to choice
    setImageUrl('');
    setError('');
    setSelectedFile(null);
    setIsUploading(false);
    setUploadError(null);
    setCurrentView('choice');
  };

  const renderChoiceView = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <Button
        onClick={() => {
          if (!campaignId) return; // Should ideally not be reachable if button is disabled
          // Reset states for other views before switching
          setImageUrl('');
          setError('');
          setSelectedFile(null);
          setUploadError(null);
          setCurrentView('upload');
        }}
        variant="secondary"
        disabled={!campaignId} // Disable if no campaignId
        tooltip={!campaignId ? "Campaign context required for upload" : "Upload an image from your computer"} // Tooltip
      >
        Upload Image from Computer
      </Button>
      <Button
        onClick={() => {
          onInitiateGenerateImage?.();
          onClose();
        }}
        variant="secondary"
      >
        Generate New Image
      </Button>
      <Button onClick={() => setCurrentView('pasteUrl')} variant="secondary">
        Add Image by URL
      </Button>
    </div>
  );

  const renderPasteUrlView = () => (
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
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
        <Button onClick={handleBackToChoice} variant="secondary">
          Back
        </Button>
        <Button
          onClick={handleAddClick}
          variant="primary"
        >
          Add URL
        </Button>
      </div>
    </div>
  );

  const renderUploadView = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        style={{
          border: '1px solid #ccc',
          padding: '8px',
          borderRadius: '4px',
        }}
        disabled={isUploading}
      />
      {selectedFile && !isUploading && (
        <p style={{ textAlign: 'center', marginTop: '4px', fontSize: '0.9em' }}>
          Selected: {selectedFile.name}
        </p>
      )}
      {isUploading && <p style={{ textAlign: 'center' }}>Uploading...</p>}
      {uploadError && <p style={{ color: 'red', textAlign: 'center' }}>{uploadError}</p>}
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', marginTop: '8px' }}>
        <Button onClick={handleBackToChoice} variant="secondary" disabled={isUploading}>
          Back
        </Button>
        <Button
          onClick={handleUploadClick}
          variant="primary"
          disabled={!selectedFile || isUploading || !campaignId} // Also disable if no campaignId
        >
          {isUploading ? 'Uploading...' : 'Upload'}
        </Button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleModalClose}
      title={title}
      size="md"
    >
      {currentView === 'choice' && renderChoiceView()}
      {currentView === 'pasteUrl' && renderPasteUrlView()}
      {currentView === 'upload' && renderUploadView()}
    </Modal>
  );
};

export default AddMoodBoardImageModal;
