import React, { useState, useEffect } from 'react'; // Added useEffect
import LLMSelector from '../components/LLMSelector';
import {
    generateTextLLM, LLMTextGenerationParams, LLMModel, // Added LLMModel
    generateImage, ImageGenerationParams, ImageGenerationResponse // Changed ImageGenerationRequest to ImageGenerationParams
} from '../services/llmService';
import { getFeatures } from '../services/featureService'; // Updated import
import { Feature } from '../types/featureTypes'; // Updated import
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import Input from '../components/common/Input'; // Import Input component
import MoodBoardPanel from '../components/common/MoodBoardPanel'; // Updated Import
import ImageGenerationModal from '../components/modals/ImageGenerationModal/ImageGenerationModal'; // Import ImageGenerationModal
import './GenericTextGenerator.css';

const GenericTextGenerator: React.FC = () => {
  // State for Text Generation
  const [textPrompt, setTextPrompt] = useState<string>('');
  const [selectedLLMModel, setSelectedLLMModel] = useState<LLMModel | null>(null); // Updated state
  const [temperature, setTemperature] = useState<number>(0.7); // Added temperature state
  const [generatedText, setGeneratedText] = useState<string | null>(null);
  const [textIsLoading, setTextIsLoading] = useState<boolean>(false);
  const [textError, setTextError] = useState<string | null>(null); // Existing text error
  const [textModelUsed, setTextModelUsed] = useState<string | null>(null);

  // State for Feature Prompts
  const [features, setFeatures] = useState<Feature[]>([]); // Updated type
  const [selectedFeatureName, setSelectedFeatureName] = useState<string>('');
  const [featureError, setFeatureError] = useState<string | null>(null); // Error for fetching features
  const [selectedFeatureTemplateDisplay, setSelectedFeatureTemplateDisplay] = useState<string | null>(null);

  // State for Image Generation
  const [imagePrompt, setImagePrompt] = useState<string>('');
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [imageIsLoading, setImageIsLoading] = useState<boolean>(false);
  const [imageError, setImageError] = useState<string | null>(null);
  const [promptUsedForImage, setPromptUsedForImage] = useState<string | null>(null);
  const [isImageDisplayVisible, setIsImageDisplayVisible] = useState<boolean>(false);
  const [isGeneratingForGenericDisplay, setIsGeneratingForGenericDisplay] = useState<boolean>(false);
  // Optional: If you want to allow selecting specific DALL-E model, size, quality via UI
  // const [dalleModel, setDalleModel] = useState<string | null>(null); // e.g., "dall-e-3"
  // const [imageSize, setImageSize] = useState<string | null>(null); // e.g., "1024x1024"
  // const [imageQuality, setImageQuality] = useState<string | null>(null); // e.g., "standard"

  // Effect to load features on mount
  useEffect(() => {
    const loadFeatures = async () => {
      try {
        setFeatureError(null);
        const fetchedFeatures = await getFeatures(); // Updated function call
        setFeatures(fetchedFeatures);
      } catch (error) {
        console.error("Failed to load features:", error);
        setFeatureError(error instanceof Error ? error.message : "An unknown error occurred while fetching features.");
      }
    };
    loadFeatures();
  }, []);

  const handleLLMModelChange = (model: LLMModel | null) => { // Updated signature
    setSelectedLLMModel(model); // Updated state setter
    setGeneratedText(null); // Clear previous results
    setTextModelUsed(null);
    setTextError(null); // Clear text generation errors
  };

  const handleFeatureChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const featureName = event.target.value;
    setSelectedFeatureName(featureName);
    const selectedFeature = features.find(f => f.name === featureName);
    if (selectedFeature) {
      setSelectedFeatureTemplateDisplay(selectedFeature.template);
      // If template does not have a placeholder, replace textPrompt.
      // If it has a placeholder, clear textPrompt to encourage user to fill it.
      if (!selectedFeature.template.includes('{}')) {
        setTextPrompt(selectedFeature.template);
      } else {
        setTextPrompt(''); // Clear prompt for user to input placeholder content
      }
    } else {
      setSelectedFeatureTemplateDisplay(null);
      // Optionally, reset textPrompt if no feature is selected, or leave it as is
      // setTextPrompt('');
    }
  };

  const handleGenerateText = async () => {
    let finalPrompt = textPrompt;
    const selectedFeature = features.find(f => f.name === selectedFeatureName);

    if (selectedFeature && selectedFeature.template) {
      if (selectedFeature.template.includes('{}')) {
        // Ensure textPrompt is not empty if placeholder exists
        if (!textPrompt.trim()) {
          setTextError("Please provide input for the selected feature's placeholder {}.");
          return;
        }
        finalPrompt = selectedFeature.template.replace('{}', textPrompt);
      } else {
        // If no placeholder, the template is the full prompt
        finalPrompt = selectedFeature.template;
      }
    } else if (!textPrompt.trim()) { // No feature selected, check normal prompt
      setTextError("Text prompt cannot be empty.");
      return;
    }
    
    setTextIsLoading(true);
    setTextError(null); // Clear previous text errors
    setGeneratedText(null);
    setTextModelUsed(null);

    try {
      const params: LLMTextGenerationParams = {
        prompt: finalPrompt,
        model_id_with_prefix: selectedLLMModel ? selectedLLMModel.id : null,
      };
      if (selectedLLMModel && selectedLLMModel.supports_temperature) {
        params.temperature = temperature;
      }
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
      // Ensure this matches the ImageGenerationParams from llmService.ts
      // The `model` field is now mandatory in ImageGenerationParams.
      // Since this component doesn't have model selection for images yet,
      // we'll need to decide a default or add UI for it.
      // For now, let's assume a default like 'dall-e' or make it more explicit.
      // This part of the code might need further UI logic if model selection is desired here.
      const params: ImageGenerationParams = {
        prompt: imagePrompt,
        model: 'dall-e', // Defaulting to 'dall-e' for now as no UI for model selection here.
                           // This should ideally be configurable or selected by the user.
        // size: imageSize,
        // quality: imageQuality,
      };
      const result = await generateImage(params); // Changed 'request' to 'params'
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

  const handleMoodBoardUrlAdded = (newUrls: string[]) => {
    if (newUrls && newUrls.length > 0) {
      const newUrl = newUrls[newUrls.length - 1]; // Assume the last one is the newly added one
      setGeneratedImageUrl(newUrl);
      setPromptUsedForImage("Image added by URL"); // Or derive from URL if possible
      setImageError(null); // Clear any previous image errors
      setIsImageDisplayVisible(true);
    }
  };

  const handleImageGeneratedForGenericDisplay = (imageUrl: string, prompt?: string) => {
    setGeneratedImageUrl(imageUrl);
    setPromptUsedForImage(prompt || "Generated Image");
    setImageError(null);
    setIsImageDisplayVisible(true);
    setIsGeneratingForGenericDisplay(false); // Close the modal
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
          // Pass initialSelectedModelId if you want to control it from this component's state,
          // e.g., initialSelectedModelId={selectedLLMModel?.id}
          // However, LLMSelector manages its own initial selection if not directly controlled post-mount.
        />

        {selectedLLMModel && (
          <div className="gt-model-info form-group">
            <p><strong>Model Type:</strong> {selectedLLMModel.model_type}</p>
            <p>
              {selectedLLMModel.supports_temperature
                ? "Supports temperature adjustment."
                : "Temperature not adjustable for this model."}
            </p>
            {selectedLLMModel.supports_temperature && (
              <div className="gt-temperature-slider">
                <label htmlFor="temperature-slider" className="form-label">
                  Temperature: {temperature.toFixed(1)}
                </label>
                <input
                  type="range"
                  id="temperature-slider"
                  min="0.0"
                  max="1.0" // Or 2.0, adjust as needed
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="form-range"
                />
              </div>
            )}
          </div>
        )}

        {/* Feature Prompts Section */}
        <div className="gt-feature-group form-group">
          <label htmlFor="feature-select" className="form-label">Select Feature (Optional):</label>
          <select
            id="feature-select"
            value={selectedFeatureName}
            onChange={handleFeatureChange}
            className="form-select"
          >
            <option value="">-- Select a Feature --</option>
            {features.map(feature => (
              <option key={feature.name} value={feature.name}>
                {feature.name}
              </option>
            ))}
          </select>
          {featureError && <p className="gt-error-message">Error loading features: {featureError}</p>}
          {selectedFeatureTemplateDisplay && (
            <p className="gt-template-display">
              <strong>Template:</strong> <code className="gt-code-block">{selectedFeatureTemplateDisplay}</code>
              {selectedFeatureTemplateDisplay.includes("{}") && <em> (Fill the <code>{"{}"}</code> in the prompt below)</em>}
            </p>
          )}
        </div>

        <div className="gt-prompt-group form-group">
          <label htmlFor="text-prompt-textarea" className="gt-prompt-label form-label">
            {selectedFeatureTemplateDisplay && selectedFeatureTemplateDisplay.includes("{}")
              ? "Enter content for the placeholder {}:"
              : "Enter your text prompt (or use a feature above):"}
          </label>
          <textarea
            id="text-prompt-textarea"
            value={textPrompt}
            onChange={(e) => setTextPrompt(e.target.value)}
            rows={5}
            placeholder={
              selectedFeatureTemplateDisplay && selectedFeatureTemplateDisplay.includes("{}")
              ? "e.g., a mysterious artifact"
              : "e.g., Write a short story about a brave knight..."
            }
            className="form-textarea gt-prompt-textarea"
          />
        </div>

        <div className="gt-actions">
          <Button 
            onClick={handleGenerateText} 
            disabled={textIsLoading || (!textPrompt.trim() && !(selectedFeatureName && features.find(f=>f.name === selectedFeatureName)?.template && !features.find(f=>f.name === selectedFeatureName)!.template.includes('{}')))}
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
      
      {/* MoodBoardPanel now used for displaying the single generated image */}
      <MoodBoardPanel
        moodBoardUrls={generatedImageUrl ? [generatedImageUrl] : []}
        isLoading={imageIsLoading}
        error={imageError}
        isVisible={isImageDisplayVisible}
        onClose={handleCloseImageDisplay}
        title={promptUsedForImage ? `Generated: ${promptUsedForImage}` : "Generated Image"}
        onUpdateMoodBoardUrls={handleMoodBoardUrlAdded} // Updated prop
        onRequestOpenGenerateImageModal={() => setIsGeneratingForGenericDisplay(true)} // New prop
      />

      <ImageGenerationModal
        isOpen={isGeneratingForGenericDisplay}
        onClose={() => setIsGeneratingForGenericDisplay(false)}
        onImageSuccessfullyGenerated={handleImageGeneratedForGenericDisplay}
        onSetAsThematic={() => { /* No-op in this context */ }}
        primaryActionText="Display This Image"
        autoApplyDefault={true}
        // campaignId={undefined} // Explicitly undefined or omit if not needed by modal for basic generation
        // selectedLLMId={selectedLLMModel?.id} // Pass if modal needs LLM context for generation
      />
    </div>
  );
};

export default GenericTextGenerator;
