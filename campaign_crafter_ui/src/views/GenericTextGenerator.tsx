import React, { useState } from 'react';
import LLMSelector from '../components/LLMSelector';
import { 
    generateTextLLM, LLMTextGenerationParams, 
    generateImage, ImageGenerationRequest, ImageGenerationResponse 
} from '../services/llmService';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import Input from '../components/common/Input'; // Import Input component
import ThematicImageDisplay from '../components/common/ThematicImageDisplay'; // Import Image Display
import './GenericTextGenerator.css';

const GenericTextGenerator: React.FC = () => {
  // State for Text Generation
  const [textPrompt, setTextPrompt] = useState<string>('');
  const [selectedLLMModelId, setSelectedLLMModelId] = useState<string | null>(null);
  const [generatedText, setGeneratedText] = useState<string | null>(null);
  const [textIsLoading, setTextIsLoading] = useState<boolean>(false);
  const [textError, setTextError] = useState<string | null>(null);
  const [textModelUsed, setTextModelUsed] = useState<string | null>(null);

  // State for Image Generation
  const [imagePrompt, setImagePrompt] = useState<string>('');
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [imageIsLoading, setImageIsLoading] = useState<boolean>(false);
  const [imageError, setImageError] = useState<string | null>(null);
  const [promptUsedForImage, setPromptUsedForImage] = useState<string | null>(null);
  const [isImageDisplayVisible, setIsImageDisplayVisible] = useState<boolean>(false);
  // Optional: If you want to allow selecting specific DALL-E model, size, quality via UI
  // const [dalleModel, setDalleModel] = useState<string | null>(null); // e.g., "dall-e-3"
  // const [imageSize, setImageSize] = useState<string | null>(null); // e.g., "1024x1024"
  // const [imageQuality, setImageQuality] = useState<string | null>(null); // e.g., "standard"


  const handleLLMModelChange = (modelId: string | null) => {
    setSelectedLLMModelId(modelId);
    setGeneratedText(null); // Clear previous results
    setTextModelUsed(null);
    setTextError(null);
  };

  const handleGenerateText = async () => {
    if (!textPrompt.trim()) {
      setTextError("Text prompt cannot be empty.");
      return;
    }
    
    setTextIsLoading(true);
    setTextError(null);
    setGeneratedText(null);
    setTextModelUsed(null);

    try {
      const params: LLMTextGenerationParams = {
        prompt: textPrompt,
        model_id_with_prefix: selectedLLMModelId,
      };
      const result = await generateTextLLM(params);
      setGeneratedText(result.text);
      setTextModelUsed(result.model_used || null);
    } catch (err) {
      console.error("Failed to generate text:", err);
      setTextError(err instanceof Error ? err.message : "An unknown error occurred during text generation.");
    } finally {
      setTextIsLoading(false);
    }
  };

  const handleGenerateImage = async () => {
    if (!imagePrompt.trim()) {
      setImageError("Image prompt cannot be empty.");
      setIsImageDisplayVisible(true); // Show display to show the error
      return;
    }

    setImageIsLoading(true);
    setImageError(null);
    setGeneratedImageUrl(null);
    setPromptUsedForImage(null);
    setIsImageDisplayVisible(true); // Show display with loading indicator

    try {
      const request: ImageGenerationRequest = {
        prompt: imagePrompt,
        // model: dalleModel, // Pass if UI allows model selection
        // size: imageSize,   // Pass if UI allows size selection
        // quality: imageQuality, // Pass if UI allows quality selection
      };
      const result = await generateImage(request);
      setGeneratedImageUrl(result.image_url);
      setPromptUsedForImage(result.prompt_used); // Or use result.revised_prompt if available and preferred
    } catch (err) {
      console.error("Failed to generate image:", err);
      setImageError(err instanceof Error ? err.message : "An unknown error occurred during image generation.");
    } finally {
      setImageIsLoading(false);
    }
  };
  
  const handleCloseImageDisplay = () => {
    setIsImageDisplayVisible(false);
    // Optionally clear image data if preferred when closed
    // setGeneratedImageUrl(null);
    // setImageError(null);
    // setPromptUsedForImage(null);
  };


  return (
    <div className="gt-wrapper container"> {/* Added .container for consistent padding/max-width */}
      <h2 className="gt-title">Creative Generation Toolkit</h2>
      
      {/* --- Text Generation Section --- */}
      <section className="gt-text-gen-section">
        <h3>Generate Text</h3>
        <LLMSelector 
          onModelChange={handleLLMModelChange} 
          label="Choose LLM Model for Text (optional):"
        />

        <div className="gt-prompt-group form-group">
          <label htmlFor="text-prompt-textarea" className="gt-prompt-label form-label">
            Enter your text prompt:
          </label>
          <textarea
            id="text-prompt-textarea"
            value={textPrompt}
            onChange={(e) => setTextPrompt(e.target.value)}
            rows={5}
            placeholder="e.g., Write a short story about a brave knight..."
            className="form-textarea gt-prompt-textarea"
          />
        </div>

        <div className="gt-actions">
          <Button 
            onClick={handleGenerateText} 
            disabled={textIsLoading || !textPrompt.trim()}
            variant="primary"
          >
            {textIsLoading ? 'Generating Text...' : 'Generate Text'}
          </Button>
        </div>

        {textError && (
          <div className="gt-error-message"> 
            <strong>Text Gen Error:</strong> {textError}
          </div>
        )}

        {generatedText !== null && (
          <Card className="gt-results-card">
            <h4>Generated Text:</h4>
            {textModelUsed && <p className="gt-results-model-info">Text model used: {textModelUsed}</p>}
            <p className="gt-results-text">{generatedText || <em>(No text was generated)</em>}</p>
          </Card>
        )}
      </section>

      <hr className="gt-section-divider" />

      {/* --- Image Generation Section --- */}
      <section className="gt-image-gen-section">
        <h3 className="gt-image-gen-title">Generate Thematic Image</h3>
        <Input
            type="text"
            id="imagePrompt"
            name="imagePrompt"
            label="Enter your image prompt:"
            value={imagePrompt}
            onChange={(e) => setImagePrompt(e.target.value)}
            placeholder="e.g., A mystical forest scene, digital art"
            wrapperClassName="gt-prompt-group" // Re-use class for margin
            // error={imageError ? "Image generation failed" : undefined} // Or pass imageError directly
        />
        {/* Optional: Add inputs for DALL-E model, size, quality here if desired */}

        <div className="gt-actions">
            <Button
                onClick={handleGenerateImage}
                disabled={imageIsLoading || !imagePrompt.trim()}
                variant="success" // Different color for image button
            >
                {imageIsLoading ? 'Generating Image...' : 'Generate Thematic Image'}
            </Button>
        </div>
      </section>
      
      {/* Thematic Image Display Component - Fixed Position */}
      <ThematicImageDisplay
        imageUrl={generatedImageUrl}
        promptUsed={promptUsedForImage}
        isLoading={imageIsLoading}
        error={imageError}
        isVisible={isImageDisplayVisible}
        onClose={handleCloseImageDisplay} // Allow user to dismiss the image display
      />

    </div>
  );
};

export default GenericTextGenerator;
