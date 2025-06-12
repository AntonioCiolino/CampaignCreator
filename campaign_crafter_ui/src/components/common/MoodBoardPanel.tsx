// campaign_crafter_ui/src/components/common/MoodBoardPanel.tsx
import React from 'react';
import './MoodBoardPanel.css'; // Ensure this path is correct after rename

export interface MoodBoardPanelProps {
  moodBoardUrls: string[] | null;
  isLoading: boolean; // For loading state if URLs are fetched async, or for general panel loading
  error: string | null;
  onClose?: () => void; // For the main panel
  isVisible: boolean;
  title?: string;
  onRemoveImage?: (imageUrlToRemove: string) => void; // For removing a specific image tile
}

const MoodBoardPanel: React.FC<MoodBoardPanelProps> = ({
  moodBoardUrls,
  isLoading,
  error,
  onClose,
  isVisible,
  title = "Mood Board", // Default title
  onRemoveImage
}) => {
  // Use a more specific main class for the panel itself, wrapper can be for visibility control
  const panelClasses = `mood-board-panel ${isVisible ? 'visible' : 'hidden'}`;

  const renderContent = () => {
    if (isLoading) {
      return <p className="mood-board-loader">Loading...</p>;
    }
    if (error) {
      return <p className="mood-board-error">Error: {error}</p>;
    }
    if (moodBoardUrls && moodBoardUrls.length > 0) {
      return (
        <div className="mood-board-list">
          {moodBoardUrls.map((url, index) => (
            <a key={index} href={url} target="_blank" rel="noopener noreferrer" className="mood-board-item-link">
              <img src={url} alt={`Mood board ${index + 1}`} className="mood-board-image" />
              {onRemoveImage && (
                <button
                  onClick={(e) => {
                    e.preventDefault(); // Important: Prevent link navigation
                    e.stopPropagation(); // Stop event from bubbling up
                    onRemoveImage(url);
                  }}
                  className="mood-board-tile-close-button"
                  aria-label={`Remove image ${index + 1}`}
                >
                  &times;
                </button>
              )}
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
    <div className={panelClasses} role="dialog" aria-labelledby="mood-board-title" aria-modal="true">
      <div className="mood-board-panel-content-wrapper"> {/* Added for better structure if needed */}
        {(onClose || title) && (
          <div className="mood-board-header">
            {title && <span id="mood-board-title" className="mood-board-title">{title}</span>}
            {onClose && (
              <button onClick={onClose} className="mood-board-close-button" aria-label="Close mood board">
                &times;
              </button>
            )}
          </div>
        )}
        <div className="mood-board-content-area"> {/* Renamed for clarity from mood-board-content */}
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default MoodBoardPanel;
