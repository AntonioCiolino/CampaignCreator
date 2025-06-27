import React, { useState, useEffect } from 'react';
import Modal from '../../common/Modal';
import Input from '../../common/Input';
import Button from '../../common/Button';
// import apiClient from '../../../services/apiClient'; // Removed as generateImage service is used directly
import { generateImage, ImageGenerationParams, ImageGenerationResponse, ImageModelName as BackendImageModelName } from '../../../services/llmService'; // Moved import to top
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
  onImageSuccessfullyGenerated?: (imageUrl: string, promptUsed: string) => void;
  onSetAsThematic?: (imageUrl: string, promptUsed: string) => void;
  primaryActionText?: string;
  autoApplyDefault?: boolean;
  campaignId?: string; // Added campaignId prop
}

// Use ImageModelName from llmService.ts if it's exported, or redefine/align here
type ImageModel = BackendImageModelName; // 'dall-e' | 'stable-diffusion' | 'gemini';

// No longer need ImageGenerationRequestPayload, will use ImageGenerationParams from llmService
// No longer need ImageGenerationResponseData, will use ImageGenerationResponse from llmService

const ImageGenerationModal: React.FC<ImageGenerationModalProps> = ({
  isOpen,
  onClose,
  onImageSuccessfullyGenerated,
  onSetAsThematic,
  primaryActionText,
  autoApplyDefault,
  campaignId, // Destructure campaignId from props
}) => {
  const [prompt, setPrompt] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<ImageModel>('dall-e');

  // DALL-E specific
  const [dalleSize, setDalleSize] = useState<string>('1024x1024'); // Default DALL-E size
  const [dalleQuality, setDalleQuality] = useState<string>('standard'); // Default DALL-E quality

  // Stable Diffusion specific
  const [sdSteps, setSdSteps] = useState<number>(30);
  const [sdCfgScale, setSdCfgScale] = useState<number>(7.5);
  // const [sdModelCheckpoint, setSdModelCheckpoint] = useState<string>(''); // If allowing selection

  // Gemini specific
  const [geminiModelName, setGeminiModelName] = useState<string>('gemini-pro-vision'); // Default Gemini model

  // Common state
  const [genericSizeInput, setGenericSizeInput] = useState<string>('1024x1024'); // For SD and conceptual for Gemini

  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [generationDetails, setGenerationDetails] = useState<ImageGenerationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [generationCompleted, setGenerationCompleted] = useState<boolean>(false);
  const [autoApplyImage, setAutoApplyImage] = useState<boolean>(autoApplyDefault !== undefined ? autoApplyDefault : true);
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
    setGenerationCompleted(false);
    setGenerationDetails(null);

    const params: ImageGenerationParams = {
      prompt,
      model: selectedModel,
    };

    // Add campaignId to params if it exists
    if (campaignId) {
      params.campaign_id = campaignId; // Type in llmService.ImageGenerationParams now includes campaign_id
    }

    if (selectedModel === 'dall-e') {
      params.size = dalleSize;
      params.quality = dalleQuality;
    } else if (selectedModel === 'stable-diffusion') {
      params.size = genericSizeInput; // Use genericSizeInput for SD
      params.steps = sdSteps;
      params.cfg_scale = sdCfgScale;
      // params.sd_model_checkpoint = sdModelCheckpoint; // If used
    } else if (selectedModel === 'gemini') {
      params.size = genericSizeInput; // Use genericSizeInput conceptually for Gemini
      params.gemini_model_name = geminiModelName;
    }

    try {
      // const response = await apiClient.post<ImageGenerationResponseData>('/api/v1/images/generate', payload);
      const responseData = await generateImage(params); // Use the imported service function

      if (responseData && responseData.image_url) {
        setGeneratedImageUrl(responseData.image_url);
        setGenerationDetails(responseData); // Store full response
        setGenerationCompleted(true);
        if (autoApplyImage) {
          onImageSuccessfullyGenerated?.(responseData.image_url, prompt);
          onClose();
        }
      } else {
        setError('Failed to generate image: Invalid response from server.');
        setGenerationCompleted(false);
      }
    } catch (err: any) {
      // Error handling from llmService.ts should provide a message
      console.error('Image generation error in modal:', err);
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
          onClose(); // Close modal after action
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
      onClose(); // Close modal after action
    }
  };

  const handleCopyToClipboard = () => {
    if (generatedImageUrl) {
      navigator.clipboard.writeText(generatedImageUrl)
        .then(() => {
          // Optional: Show a success message
          alert('Image URL copied to clipboard!');
          onClose(); // Close modal after action
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
      // Reset common fields
      setPrompt('');
      setGeneratedImageUrl(null);
      setGenerationDetails(null);
      setIsLoading(false);
      setError(null);
      setGenerationCompleted(false);
      setAutoApplyImage(autoApplyDefault !== undefined ? autoApplyDefault : true);

      // Reset model-specific fields to defaults
      setSelectedModel('dall-e');
      setDalleSize('1024x1024');
      setDalleQuality('standard');
      setSdSteps(30);
      setSdCfgScale(7.5);
      setGeminiModelName('gemini-pro-vision');
      setGenericSizeInput('1024x1024');
    }
  }, [isOpen, autoApplyDefault]);

  let imageActionsContent = null;
  if (generationCompleted && !autoApplyImage && generatedImageUrl && generationDetails && !isLoading && !error) {
    imageActionsContent = (
      <div className="generated-image-actions" style={{ marginTop: '10px' }}>
        <Button
          onClick={() => {
            if (generatedImageUrl && generationDetails?.prompt_used) {
              onImageSuccessfullyGenerated?.(generatedImageUrl, generationDetails.prompt_used);
            }
            onClose();
          }}
          disabled={!generatedImageUrl || !generationDetails?.prompt_used}
          variant="primary"
        >
          {primaryActionText || 'Use Image'}
        </Button>
        <Button
          onClick={handleCopyToClipboard}
          disabled={!generatedImageUrl || generatedImageUrl.startsWith('data:')}
          size="sm"
          style={{ marginLeft: '10px' }}
        >
          Copy URL
        </Button>
        <Button onClick={handleDownloadImage} size="sm" style={{ marginLeft: '10px' }}>
          Download
        </Button>
        <Button
          onClick={() => {
            if (generatedImageUrl && generationDetails?.prompt_used) {
              onSetAsThematic?.(generatedImageUrl, generationDetails.prompt_used);
            }
            onClose();
          }}
          disabled={!generatedImageUrl || !generationDetails?.prompt_used || !onSetAsThematic}
          size="sm"
          style={{ marginLeft: '10px' }}
        >
          Set as Thematic
        </Button>
      </div>
    );
  }

  const renderModelSpecificOptions = () => {
    if (selectedModel === 'dall-e') {
      return (
        <>
          <label>
            DALL-E Size:
            <select value={dalleSize} onChange={(e) => setDalleSize(e.target.value)} disabled={isLoading}>
              <option value="1024x1024">1024x1024</option>
              <option value="1792x1024">1792x1024</option>
              <option value="1024x1792">1024x1792</option>
              {/* DALL-E 2 sizes if model differentiation is added:
              <option value="512x512">512x512</option>
              <option value="256x256">256x256</option> */}
            </select>
          </label>
          <label>
            DALL-E Quality:
            <select value={dalleQuality} onChange={(e) => setDalleQuality(e.target.value)} disabled={isLoading}>
              <option value="standard">Standard</option>
              <option value="hd">HD</option>
            </select>
          </label>
        </>
      );
    } else if (selectedModel === 'stable-diffusion') {
      return (
        <>
          <label>
            Size (Stable Diffusion):
            <Input type="text" value={genericSizeInput} onChange={(e) => setGenericSizeInput(e.target.value)} placeholder="e.g., 1024x1024, 512x768" disabled={isLoading} />
          </label>
          <label>
            Steps:
            <Input type="number" value={sdSteps} onChange={(e) => setSdSteps(parseInt(e.target.value, 10) || 30)} disabled={isLoading} />
          </label>
          <label>
            CFG Scale:
            <Input type="number" step="0.1" value={sdCfgScale} onChange={(e) => setSdCfgScale(parseFloat(e.target.value) || 7.5)} disabled={isLoading} />
          </label>
          {/* Optional: SD Model Checkpoint input
          <label>
            SD Model Checkpoint (Optional):
            <Input type="text" value={sdModelCheckpoint} onChange={(e) => setSdModelCheckpoint(e.target.value)} placeholder="e.g., v1-5-pruned-emaonly.ckpt" disabled={isLoading} />
          </label>
          */}
        </>
      );
    } else if (selectedModel === 'gemini') {
      return (
        <>
          <label>
            Size (Gemini - Conceptual):
            <Input type="text" value={genericSizeInput} onChange={(e) => setGenericSizeInput(e.target.value)} placeholder="e.g., 1024x1024" disabled={isLoading} />
          </label>
          <label>
            Gemini Model Name (Optional):
            <Input type="text" value={geminiModelName} onChange={(e) => setGeminiModelName(e.target.value)} placeholder="e.g., gemini-pro-vision" disabled={isLoading} />
          </label>
        </>
      );
    }
    return null;
  };

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
            <option value="gemini">Gemini</option>
          </select>
        </label>

        {renderModelSpecificOptions()}

        <div style={{ margin: '10px 0' }}>
          <label>
            <input
              type="checkbox"
              checked={autoApplyImage}
              onChange={(e) => setAutoApplyImage(e.target.checked)}
              disabled={isLoading}
            />
            Auto-apply generated image
          </label>
        </div>

        {isLoading && <div className="loading-indicator">Generating image...</div>}
        {error && <div className="error-message">{error}</div>}

        {generatedImageUrl && generationDetails && !isLoading && !error && (
          <div className="image-preview-area" style={{ textAlign: 'center', marginBottom: '15px' }}>
            <p style={{fontSize: '0.8em', color: '#666'}}>
              Using model: {generationDetails.model_used}
              {generationDetails.model_used === 'gemini' && generationDetails.gemini_model_name_used && ` (${generationDetails.gemini_model_name_used})`}
              , Size: {generationDetails.size_used}
              {generationDetails.model_used === 'dall-e' && generationDetails.quality_used && `, Quality: ${generationDetails.quality_used}`}
              {generationDetails.model_used === 'stable-diffusion' && generationDetails.steps_used && `, Steps: ${generationDetails.steps_used}, CFG: ${generationDetails.cfg_scale_used}`}
            </p>
            <img
              src={generatedImageUrl}
              alt="Generated"
              style={{
                maxWidth: '100%',
                maxHeight: '300px',
                marginTop: '5px', // Reduced margin
                marginBottom: '15px',
                border: '1px solid #ccc'
              }}
            />
            {imageActionsContent}
          </div>
        )}

        <div className="modal-actions">
           <Button onClick={handleGenerateImage} disabled={isLoading || !prompt.trim()}>
            {isLoading ? 'Generating...' : (generationDetails ? 'Generate New' : 'Generate')}
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
