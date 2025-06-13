// campaign_crafter_ui/src/components/common/MoodBoardPanel.tsx
import React, { useState } from 'react';
import './MoodBoardPanel.css'; // Ensure this path is correct after rename
import AddMoodBoardImageModal from '../modals/AddMoodBoardImageModal';
import { uploadImage } from '../../services/imageService'; // Import uploadImage

export interface MoodBoardPanelProps {
  moodBoardUrls: string[]; // Changed from string[] | null
  isLoading: boolean; // For loading state if URLs are fetched async, or for general panel loading
  error: string | null;
  onClose?: () => void; // For the main panel
  isVisible: boolean;
  title?: string;
  onUpdateMoodBoardUrls: (newUrls: string[]) => void; // New required prop
  campaignId?: string; // Made campaignId optional
  onRequestOpenGenerateImageModal?: () => void; // New optional prop
  // onRemoveImage is removed
}

const MoodBoardPanel: React.FC<MoodBoardPanelProps> = (props) => {
  const {
    moodBoardUrls,
    isLoading,
    error,
    onClose,
    isVisible,
    title = "Mood Board", // Default title
    onUpdateMoodBoardUrls,
    campaignId, // Destructure campaignId
    onRequestOpenGenerateImageModal // Destructure new prop
  } = props;

  const [isAddImageModalOpen, setIsAddImageModalOpen] = useState(false);
  const [isDraggingOver, setIsDraggingOver] = useState(false); // State for drag feedback
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Use a more specific main class for the panel itself, wrapper can be for visibility control
  const panelClasses = `mood-board-panel ${isVisible ? 'visible' : 'hidden'} ${isDraggingOver ? 'dragging-over' : ''}`;

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(true);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    // Optionally set isDraggingOver here if needed, but handleDragEnter should suffice
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => { // Make it async
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);
    setUploadError(null); // Clear previous errors

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      setIsUploading(true);
      let anErrorOccurred = false;

      for (const file of Array.from(files)) { // Use Array.from for iterating FileList
        if (file.type.startsWith('image/')) {
          try {
            console.log("Processing dropped image file:", file.name, file.type);
            const response = await uploadImage(file); // Await here for sequential processing for now
            console.log(`Uploaded ${file.name}, URL: ${response.imageUrl}`);
            // It's crucial that onUpdateMoodBoardUrls correctly updates the moodBoardUrls prop
            // for the next iteration if we want to build upon the state sequentially.
            // If onUpdateMoodBoardUrls is asynchronous or batches updates, this might not reflect immediately.
            // For simplicity, we'll assume it updates the prop 'moodBoardUrls' effectively for the next spread.
            // A more robust way for multiple files would be to collect all new URLs then call onUpdateMoodBoardUrls once.
            onUpdateMoodBoardUrls([...moodBoardUrls, response.imageUrl]);
          } catch (error: any) {
            console.error(`Failed to upload ${file.name}:`, error);
            setUploadError(`Failed to upload ${file.name}: ${error.message || 'Unknown error'}`);
            anErrorOccurred = true;
            // Decide if we should break or try other files. For now, let's try all.
          }
        } else {
          console.log("Skipped non-image file:", file.name, file.type);
        }
      }
      setIsUploading(false);
      if (anErrorOccurred) {
          // Error message is already set for the first error encountered.
      } else if (files.length > 0) { // Check if any files were processed
          // Optionally, set a success message or clear error if all were successful
      }
    }
  };

  const handleAddNewImageUrl = (newUrl: string) => {
    const updatedUrls = [...moodBoardUrls, newUrl];
    onUpdateMoodBoardUrls(updatedUrls);
  };

  const renderContent = () => {
    if (isLoading) {
      return <p className="mood-board-loader">Loading...</p>;
    }
    if (error) {
      return <p className="mood-board-error">Error: {error}</p>;
    }
    // Ensure moodBoardUrls is treated as an array, even if empty
    if (moodBoardUrls && moodBoardUrls.length > 0) {
      return (
        <div className="mood-board-list">
          {moodBoardUrls.map((url, index) => (
            <a key={index} href={url} target="_blank" rel="noopener noreferrer" className="mood-board-item-link">
              <img src={url} alt={`Mood board ${index + 1}`} className="mood-board-image" />
              {/* Button to remove image, now calls onUpdateMoodBoardUrls directly */}
              <button
                onClick={(e) => {
                  e.preventDefault(); // Important: Prevent link navigation
                  e.stopPropagation(); // Stop event from bubbling up
                  const updatedUrls = moodBoardUrls.filter(u => u !== url);
                  onUpdateMoodBoardUrls(updatedUrls);
                }}
                className="mood-board-tile-close-button"
                aria-label={`Remove image ${index + 1}`}
              >
                &times;
              </button>
              {/* TODO: Add drag handles and integrate with a DND library if reordering is needed */}
            </a>
          ))}
        </div>
      );
    }
    // Only show "no images" if panel is meant to be visible and not loading/error
    if (isVisible && !isLoading && !error) {
        return <p className="mood-board-empty">No mood board images added yet.</p>;
    }
    return null;
  };

  // If not visible, don't render the panel structure at all to avoid empty space or interaction
  if (!isVisible) {
    return null;
  }

  return (
    // The wrapper div that controls visibility via CSS transition (if any)
    // Or simply rely on conditional rendering in parent to not mount this when not visible
    <div
      className={panelClasses}
      role="dialog"
      aria-labelledby="mood-board-title"
      aria-modal="true"
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="mood-board-panel-content-wrapper"> {/* Added for better structure if needed */}
        {(onClose || title) && (
          <div className="mood-board-header" onClick={onClose}>
            {/* Close button moved before title and onClick updated */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onClose && onClose(); // Check if onClose exists before calling
              }}
              className="mood-board-close-button"
              aria-label="Close mood board"
            >
              &times;
            </button>
            {title && <span id="mood-board-title" className="mood-board-title">{title}</span>}
            {/* Add Button - always rendered now */}
            <button
              onClick={(e) => {
                e.stopPropagation(); // Prevent header click
                setIsAddImageModalOpen(true);
              }}
              className="mood-board-add-button" // A new class for styling
              aria-label="Add new image to mood board"
            >
              +
            </button>
          </div>
        )}
        <div className="mood-board-content-area"> {/* Renamed for clarity from mood-board-content */}
          {isUploading && <p className="mood-board-loader">Uploading images...</p>}
          {uploadError && <p className="mood-board-error">{uploadError}</p>}
          {/* Do not show main loading/error if upload specific ones are shown */}
          {!isUploading && !uploadError && renderContent()}
        </div>
      </div>
      <AddMoodBoardImageModal
        isOpen={isAddImageModalOpen}
        onClose={() => setIsAddImageModalOpen(false)}
        onAddUrl={handleAddNewImageUrl}
        campaignId={campaignId} // Pass campaignId to the modal
        onInitiateGenerateImage={onRequestOpenGenerateImageModal} // Pass down the prop
      />
    </div>
  );
};

export default MoodBoardPanel;
