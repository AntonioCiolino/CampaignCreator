import React, { useState, useEffect } from 'react';
import Modal from '../../common/Modal';
import Input from '../../common/Input';
import Button from '../../common/Button';
import apiClient from '../../../services/apiClient'; // Import the apiClient
import './ImageGenerationModal.css';

interface ImageGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
  // onImageGenerated?: (imageUrl: string, prompt: string, model: ImageModel) => void;
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
  // onImageGenerated,
}) => {
  const [prompt, setPrompt] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<ImageModel>('dall-e');
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
      // Add size, quality, steps, cfg_scale here if you add UI controls for them
    };

    try {
      const response = await apiClient.post<ImageGenerationResponseData>('/api/images/generate', payload);
      if (response.data && response.data.image_url) {
        setGeneratedImageUrl(response.data.image_url);
        // setGenerationDetails(response.data);
        // onImageGenerated?.(response.data.image_url, response.data.prompt_used, response.data.model_used);
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

        {generatedImageUrl && !isLoading && !error && (
          <div className="image-url-display">
            <span>{generatedImageUrl}</span>
          </div>
        )}

        <div className="modal-actions">
           <Button onClick={handleGenerateImage} disabled={isLoading || !prompt.trim()}>
            {isLoading ? 'Generating...' : 'Generate'}
          </Button>
          <Button onClick={handleCopyToClipboard} disabled={isLoading || !generatedImageUrl || !!error}>
            Copy URL
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
