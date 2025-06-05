import React, { useState, useEffect } from 'react';
import Modal from '../../common/Modal';
import Input from '../../common/Input';
import Button from '../../common/Button';
import apiClient from '../../../services/apiClient';
import './ImageGenerationModal.css';

// Helper function to sanitize prompt for use as filename
const sanitizeFilename = (text: string, maxLength = 50): string => {
  if (!text) return "generated_image";
  const sanitized = text
    .trim() // Remove leading/trailing whitespace
    .toLowerCase()
    .split(/\s+/) // Split by one or more whitespace characters
    .slice(0, 5)   // Take the first 5 words
    .join('_')     // Join with underscores
    .replace(/[^\w.-]/g, '') // Remove characters that are not alphanumeric, underscore, dot, or hyphen
    .substring(0, maxLength); // Truncate to maxLength
  // If sanitization results in an empty string (e.g., prompt was all special chars), fallback.
  return sanitized || "generated_image"; 
};

interface ImageGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImageSuccessfullyGenerated?: (imageUrl: string) => void; 
}

// Matches the backend ImageModelName enum and ImageGenerationRequest model
type ImageModel = 'dall-e' | 'stable-diffusion'; 

interface ImageGenerationRequestPayload {
  prompt: string;
  model: ImageModel;
  size?: string; // Optional: Can add UI for these later if needed
  quality?: string; // Optional: For DALL-E
  steps?: number; // Optional: For Stable Diffusion
  cfg_scale?: number; // Optional: For Stable Diffusion
}

interface ImageGenerationResponseData {
  image_url: string;
  prompt_used: string;
  model_used: ImageModel;
  size_used: string;
  quality_used?: string;
  steps_used?: number;
  cfg_scale_used?: number;
}

const ImageGenerationModal: React.FC<ImageGenerationModalProps> = ({
  isOpen,
  onClose,
  onImageSuccessfullyGenerated, 
}) => {
  const [prompt, setPrompt] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<ImageModel>('dall-e');
  const [selectedSize, setSelectedSize] = useState<string>('1024x1024'); // Default size
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  // Optional: store full response details if needed for display or callback
  // const [generationDetails, setGenerationDetails] = useState<ImageGenerationResponseData | null>(null);

  const handleGenerateImage = async () => {
    if (!prompt.trim()) {
      setError('Prompt cannot be empty.');
      return;
    }
    setIsLoading(true);
    setError(null);
    setGeneratedImageUrl(null);
    // setGenerationDetails(null);

    const payload: ImageGenerationRequestPayload = {
      prompt,
      model: selectedModel,
    };
    if (selectedModel === 'dall-e') {
      payload.size = selectedSize;
    }

    try {
      const response = await apiClient.post<ImageGenerationResponseData>('/api/v1/images/generate', payload);
      if (response.data && response.data.image_url) {
        setGeneratedImageUrl(response.data.image_url);
        // setGenerationDetails(response.data); // Optional: if you want to store more details
        onImageSuccessfullyGenerated?.(response.data.image_url); // Call the callback
      } else {
        setError('Failed to generate image: Invalid response from server.');
      }
    } catch (err: any) {
      console.error('Image generation error:', err);
      if (err.response && err.response.data && err.response.data.detail) {
        if (Array.isArray(err.response.data.detail)) {
          // Handle FastAPI validation errors (array of objects)
          const errorMessages = err.response.data.detail.map((e: any) => `${e.loc.join('.')} - ${e.msg}`).join('; ');
          setError(`API Error: ${errorMessages}`);
        } else if (typeof err.response.data.detail === 'string') {
          // Handle simple string detail errors
          setError(`API Error: ${err.response.data.detail}`);
        } else {
          setError('An unexpected API error occurred.');
        }
      } else if (err.request) {
        setError('Network error: Could not connect to the server.');
      } else {
        setError(`An unexpected error occurred: ${err.message || 'Unknown error'}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadImage = () => {
    if (!generatedImageUrl) return;

    const baseFileName = sanitizeFilename(prompt); // Use the 'prompt' state variable

    if (generatedImageUrl.startsWith('data:')) {
      // Handle Data URL
      try {
        const response = fetch(generatedImageUrl); // fetch can handle data URLs
        response.then(res => res.blob()).then(blob => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.style.display = 'none';
          a.href = url;
          
          // Attempt to get a better file extension from MIME type
          const mimeType = blob.type; // e.g., "image/webp"
          let extension = ".png"; // default
          if (mimeType) {
            const ext = mimeType.split('/')[1];
            if (ext) extension = "." + ext;
          }
          a.download = baseFileName + extension; // Use baseFileName
          
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        }).catch(e => {
          console.error("Error creating blob from data URL:", e);
          alert("Failed to prepare image for download.");
        });
      } catch (e) {
          console.error("Error processing data URL for download:", e);
          alert("Failed to download image.");
      }
    } else {
      // Handle regular HTTP/HTTPS URL
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = generatedImageUrl;
      a.target = "_blank"; // Added
      a.rel = "noopener noreferrer"; // Added
      
      // Try to get filename from URL, fallback to default
      try {
        const urlObj = new URL(generatedImageUrl); // Define urlObj once
        const urlPath = urlObj.pathname;
        const originalFileNameFromUrl = urlPath.substring(urlPath.lastIndexOf('/') + 1);
        let extension = ".png"; // Default extension
        if (originalFileNameFromUrl.includes('.')) {
          const parts = originalFileNameFromUrl.split('.');
          const ext = parts.pop();
          if (ext && parts.join('.').length > 0) { // Ensure there was a name before the dot and ext is not empty
               extension = "." + ext.toLowerCase();
          } else if (ext) { // if originalFileNameFromUrl was just ".ext" or "ext"
               extension = "." + ext.toLowerCase();
          }
        }
        a.download = baseFileName + extension;
      } catch {
        a.download = baseFileName + ".png"; // Fallback with default extension
      }
      
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  const handleCopyToClipboard = () => {
    if (generatedImageUrl) {
      navigator.clipboard.writeText(generatedImageUrl)
        .then(() => {
          // Optional: Show a success message
          alert('Image URL copied to clipboard!');
        })
        .catch(err => {
          console.error('Failed to copy URL: ', err);
          alert('Failed to copy URL.');
        });
    }
  };

  // Reset state when modal is closed/reopened
  useEffect(() => {
    if (isOpen) {
      setPrompt('');
      setSelectedModel('dall-e');
      setSelectedSize('1024x1024');
      setGeneratedImageUrl(null);
      setIsLoading(false);
      setError(null);
    }
  }, [isOpen]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Generate Image">
      <div className="image-generation-modal-content">
        <label>
          Prompt:
          <Input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter a description for the image"
            disabled={isLoading}
          />
        </label>
        
        <label>
          Model:
          <select 
            value={selectedModel} 
            onChange={(e) => setSelectedModel(e.target.value as ImageModel)}
            disabled={isLoading}
          >
            <option value="dall-e">DALL-E</option>
            <option value="stable-diffusion">Stable Diffusion</option>
          </select>
        </label>
        <label>
          Size (DALL-E):
          <select
            value={selectedSize}
            onChange={(e) => setSelectedSize(e.target.value)}
            disabled={isLoading || selectedModel !== 'dall-e'} // Disable if not DALL-E or loading
          >
            <option value="256x256">256x256</option>
            <option value="512x512">512x512</option>
            <option value="1024x1024">1024x1024</option>
          </select>
        </label>

        {isLoading && <div className="loading-indicator">Generating image...</div>}
        {error && <div className="error-message">{error}</div>}

        <div className="image-preview">
          {isLoading && <div className="image-preview-placeholder">Generating image...</div>}
          {!isLoading && error && <div className="image-preview-placeholder error-message">{error}</div>}
          {!isLoading && !error && generatedImageUrl && (
            <img src={generatedImageUrl} alt="Generated" />
          )}
          {!isLoading && !error && !generatedImageUrl && (
            <div className="image-preview-placeholder">Image will appear here</div>
          )}
        </div>
        
        {/* {generatedImageUrl && !isLoading && !error && (
          <div className="image-url-display">
            <span>{generatedImageUrl}</span>
          </div>
        )} */}

        <div className="modal-actions">
           <Button onClick={handleGenerateImage} disabled={isLoading || !prompt.trim()}>
            {isLoading ? 'Generating...' : 'Generate'}
          </Button>
          <Button 
            onClick={handleCopyToClipboard} 
            disabled={isLoading || !generatedImageUrl || !!error || generatedImageUrl.startsWith('data:')}
          >
            Copy URL
          </Button>
          <Button onClick={handleDownloadImage} disabled={isLoading || !generatedImageUrl || !!error}>
            Download
          </Button>
           <Button onClick={onClose} variant="secondary" disabled={isLoading}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default ImageGenerationModal;
