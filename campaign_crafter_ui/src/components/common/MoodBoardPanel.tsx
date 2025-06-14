// campaign_crafter_ui/src/components/common/MoodBoardPanel.tsx
import React, { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  // For horizontal lists, rectSortingStrategy or horizontalListSortingStrategy might be more semantically correct.
  // However, verticalListSortingStrategy works for wrapping lists too. Let's try rectSortingStrategy for potentially better wrapping behavior.
  rectSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

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

// New SortableMoodBoardItem component
interface SortableMoodBoardItemProps {
  id: string;
  url: string;
  index: number; // Keep index for alt text and potential non-dnd related logic
  onRemove: (urlToRemove: string) => void; // Pass remove handler
}

const SortableMoodBoardItem: React.FC<SortableMoodBoardItemProps> = ({ id, url, index, onRemove }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging, // useful for styling the dragged item
  } = useSortable({ id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1, // Example: reduce opacity when dragging
    // Ensure items are still visible and take space when dragging
    // width: '100px', // Assuming fixed size for now, or ensure CSS handles it
    // height: '100px',
    // touchAction: 'none', // Recommended by dnd-kit for pointer sensors
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="mood-board-item-link-wrapper">
      {/* The original <a> tag can be here or you can directly style the div above */}
      <a href={url} target="_blank" rel="noopener noreferrer" className="mood-board-item-link">
        <img src={url} alt={`Mood board ${index + 1}`} className="mood-board-image" />
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onRemove(url);
          }}
          className="mood-board-tile-close-button"
          aria-label={`Remove image ${index + 1}`}
        >
          &times;
        </button>
      </a>
    </div>
  );
};


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

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

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

  const handleRemoveUrl = (urlToRemove: string) => {
    const updatedUrls = moodBoardUrls.filter(u => u !== urlToRemove);
    onUpdateMoodBoardUrls(updatedUrls);
  };

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = moodBoardUrls.findIndex(url => url === active.id);
      const newIndex = moodBoardUrls.findIndex(url => url === over.id);

      if (oldIndex !== -1 && newIndex !== -1) {
        const newOrder = arrayMove(moodBoardUrls, oldIndex, newIndex);
        onUpdateMoodBoardUrls(newOrder);
      }
    }
  }

  const renderContent = () => {
    if (isLoading) {
      return <p className="mood-board-loader">Loading...</p>;
    }
    if (error) {
      return <p className="mood-board-error">Error: {error}</p>;
    }
    // Ensure moodBoardUrls is treated as an array, even if empty
    // URLs are used as IDs for dnd-kit items. Ensure they are unique.
    // If URLs might not be unique (e.g., same image added multiple times),
    // then a more robust ID generation strategy is needed (e.g., objects with {id, url}).
    // For now, assuming URLs are unique enough to serve as keys/IDs.
    const items = moodBoardUrls.map(url => ({ id: url, url }));


    if (items && items.length > 0) {
      return (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={items.map(item => item.id)} // Pass array of IDs
            strategy={rectSortingStrategy} // Use rectSortingStrategy for better wrapping
          >
            <div className="mood-board-list">
              {items.map(({ id, url }, index) => (
                <SortableMoodBoardItem
                  key={id}
                  id={id}
                  url={url}
                  index={index}
                  onRemove={handleRemoveUrl}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
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
            {/* Add Button - moved here */}
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
            {title && <span id="mood-board-title" className="mood-board-title">{title}</span>}
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
