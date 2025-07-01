import React, { useState, ChangeEvent } from 'react';
import { CharacterImage } from '../types/characterTypes';
import ImagePreviewModal from './modals/ImagePreviewModal'; // Assuming this modal can be reused
import Button from './common/Button'; // Common button component
// import ImageGenerationModal from './modals/ImageGenerationModal/ImageGenerationModal'; // If AI generation is needed
import './CharacterImageGallery.css'; // CSS for styling

interface CharacterImageGalleryProps {
  images: CharacterImage[];
  onImagesChange: (newImages: CharacterImage[]) => void;
  campaignId?: number | string; // Optional: for AI image generation context
  characterName?: string; // Optional: for default prompts or naming generated images
}

const CharacterImageGallery: React.FC<CharacterImageGalleryProps> = ({
  images,
  onImagesChange,
  campaignId,
  characterName,
}) => {
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState<boolean>(false);
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null);
  const [previewImageCaption, setPreviewImageCaption] = useState<string | null>(null);
  // const [isGenerateModalOpen, setIsGenerateModalOpen] = useState<boolean>(false); // For AI generation

  const handleImageClick = (image: CharacterImage) => {
    setPreviewImageUrl(image.url);
    setPreviewImageCaption(image.caption || null);
    setIsPreviewModalOpen(true);
  };

  const handleAddImageManually = () => {
    const url = prompt('Enter image URL:');
    if (url) {
      const caption = prompt('Enter optional caption:');
      const newImage: CharacterImage = { url, caption: caption || undefined };
      onImagesChange([...images, newImage]);
    }
  };

  // Placeholder for file input handling - more robust implementation needed for actual uploads
  const handleImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // This is a simplified version. In a real app, you would:
      // 1. Upload the file to a server/blob storage.
      // 2. Get the URL of the uploaded image.
      // 3. Create a CharacterImage object with that URL.
      // For now, using FileReader to display locally (not persisted beyond session unless URL is actual)
      const reader = new FileReader();
      reader.onloadend = () => {
        const newImage: CharacterImage = {
          url: reader.result as string, // This will be a data URL
          caption: file.name, // Use file name as a default caption
        };
        onImagesChange([...images, newImage]);
      };
      reader.readAsDataURL(file);
      event.target.value = ''; // Reset file input
    }
  };

  const handleRemoveImage = (indexToRemove: number) => {
    if (window.confirm('Are you sure you want to remove this image?')) {
      onImagesChange(images.filter((_, index) => index !== indexToRemove));
    }
  };

  const handleEditCaption = (indexToEdit: number) => {
    const currentImage = images[indexToEdit];
    const newCaption = prompt('Edit caption:', currentImage.caption || '');
    if (newCaption !== null) { // Prompt wasn't cancelled
      const updatedImages = images.map((img, index) =>
        index === indexToEdit ? { ...img, caption: newCaption || undefined } : img
      );
      onImagesChange(updatedImages);
    }
  };

  // const handleOpenGenerateModal = () => {
  //   if (!campaignId) {
  //     alert("Campaign context is needed for image generation.");
  //     return;
  //   }
  //   setIsGenerateModalOpen(true);
  // };

  // const handleImageGenerated = (imageUrl: string, promptUsed?: string) => {
  //   const newImage: CharacterImage = {
  //     url: imageUrl,
  //     caption: promptUsed || `AI Generated for ${characterName || 'character'}`,
  //   };
  //   onImagesChange([...images, newImage]);
  //   setIsGenerateModalOpen(false);
  // };

  return (
    <div className="character-image-gallery">
      <h4>Character Images</h4>
      <div className="gallery-actions">
        <Button onClick={handleAddImageManually} variant="secondary" size="sm">
          Add Image URL
        </Button>
        <label htmlFor="imageUpload" className="button button-secondary button-sm file-upload-label">
          Upload Image
        </label>
        <input
          type="file"
          id="imageUpload"
          accept="image/*"
          onChange={handleImageUpload}
          style={{ display: 'none' }}
        />
        {/* {campaignId && ( // Conditionally show AI generation button
          <Button onClick={handleOpenGenerateModal} variant="secondary" size="sm">
            Generate Image (AI)
          </Button>
        )} */}
      </div>

      {images.length === 0 ? (
        <p className="no-images-message">No images added for this character yet.</p>
      ) : (
        <div className="gallery-grid">
          {images.map((image, index) => (
            <div key={index} className="gallery-item" title={image.caption || image.url}>
              <img
                src={image.url}
                alt={image.caption || `Character image ${index + 1}`}
                onClick={() => handleImageClick(image)}
                className="gallery-thumbnail"
              />
              {image.caption && <p className="gallery-caption">{image.caption}</p>}
              <div className="gallery-item-actions">
                <Button onClick={() => handleEditCaption(index)} variant="outline-secondary" size="xs" className="action-btn">
                  Edit Caption
                </Button>
                <Button onClick={() => handleRemoveImage(index)} variant="danger" size="xs" className="action-btn">
                  Remove
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {previewImageUrl && (
        <ImagePreviewModal
          isOpen={isPreviewModalOpen}
          onClose={() => setIsPreviewModalOpen(false)}
          imageUrl={previewImageUrl}
          imageAlt={previewImageCaption || 'Character Image Preview'}
          caption={previewImageCaption}
        />
      )}

      {/* {campaignId && isGenerateModalOpen && (
        <ImageGenerationModal
          isOpen={isGenerateModalOpen}
          onClose={() => setIsGenerateModalOpen(false)}
          onImageSuccessfullyGenerated={handleImageGenerated}
          campaignId={campaignId}
          // Pass other necessary props like selectedLLMId if the modal needs it
          // Default prompt could be something like: `Portrait of ${characterName || 'a fantasy character'}`
          initialPrompt={`Detailed portrait of ${characterName || 'a character'}`}
          primaryActionText="Add to Character Gallery"
        />
      )} */}
    </div>
  );
};

export default CharacterImageGallery;
