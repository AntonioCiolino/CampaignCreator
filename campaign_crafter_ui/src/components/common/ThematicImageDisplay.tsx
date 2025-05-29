import React from 'react';
import './ThematicImageDisplay.css'; // Import the CSS file

export interface ThematicImageDisplayProps {
  imageUrl: string | null;
  promptUsed: string | null;
  isLoading: boolean;
  error: string | null;
  onClose?: () => void; // Optional: If the display can be actively closed by the user
  isVisible: boolean; // To control appearance/disappearance with transition
  title?: string; // Optional title for the display header
}

/**
 * A component to display a thematically generated image, typically in a fixed, unobtrusive position.
 * Handles loading, error, and image display states.
 */
const ThematicImageDisplay: React.FC<ThematicImageDisplayProps> = ({
  imageUrl,
  promptUsed,
  isLoading,
  error,
  onClose,
  isVisible,
  title = "Thematic Image" // Default title
}) => {
  const wrapperClasses = `thematic-image-display-wrapper ${isVisible ? '' : 'hidden'}`;

  const renderContent = () => {
    if (isLoading) {
      return <p className="thematic-image-loader">Generating image...</p>;
    }
    if (error) {
      return <p className="thematic-image-error">Error: {error}</p>;
    }
    if (imageUrl) {
      return (
        <>
          <div className="thematic-image-container">
            <img src={imageUrl} alt={promptUsed || "Generated thematic image"} />
          </div>
          {promptUsed && (
            <p className="thematic-image-caption">
              <strong>Prompt:</strong> {promptUsed}
            </p>
          )}
        </>
      );
    }
    // If not loading, no error, and no image, it means it's idle (or just closed)
    // Or could show a placeholder message if desired when visible but no image/error/loading
    if (isVisible) {
        return <p className="thematic-image-loader" style={{ fontStyle: 'italic' }}>Image will appear here.</p>;
    }
    return null;
  };

  // If not visible and not loading (to allow it to animate out), don't render anything.
  // Or, if you want it to always be in the DOM for transitions, the CSS .hidden handles it.
  // For simplicity, we can just let CSS handle the .hidden state.

  return (
    <div className={wrapperClasses} role="dialog" aria-live="polite" aria-atomic="true">
      {(onClose || title) && (
        <div className="thematic-image-header">
          <span className="thematic-image-title">{title}</span>
          {onClose && (
            <button onClick={onClose} className="thematic-image-close-button" aria-label="Close image display">
              &times;
            </button>
          )}
        </div>
      )}
      <div className="thematic-image-content">
        {renderContent()}
      </div>
    </div>
  );
};

export default ThematicImageDisplay;
