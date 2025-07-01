import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import CollapsibleSection from '../common/CollapsibleSection'; // Import CollapsibleSection
import { Character } from '../../types/characterTypes';
import { ImageModelName } from '../../services/llmService';
import './ImageGenerationModal/ImageGenerationModal.css'; // Corrected path

export interface CharacterImageGenSettings {
  model_name: ImageModelName;
  size?: string;
  quality?: string; // DALL-E
  steps?: number; // Stable Diffusion
  cfg_scale?: number; // Stable Diffusion
  gemini_model_name?: string; // Gemini
}

interface CharacterImagePromptModalProps {
  isOpen: boolean;
  onClose: () => void;
  character: Character | null;
  onSubmit: (basePrompt: string, additionalDetails: string, settings: CharacterImageGenSettings) => void;
  isGenerating: boolean; // To disable inputs/button during submission
}

const CharacterImagePromptModal: React.FC<CharacterImagePromptModalProps> = ({
  isOpen,
  onClose,
  character,
  onSubmit,
  isGenerating,
}) => {
  const [basePrompt, setBasePrompt] = useState<string>('');
  const [additionalDetails, setAdditionalDetails] = useState<string>('');

  // Image Generation Settings
  const [selectedModel, setSelectedModel] = useState<ImageModelName>('dall-e');
  const [dalleSize, setDalleSize] = useState<string>('1024x1024');
  const [dalleQuality, setDalleQuality] = useState<string>('standard');
  const [sdSteps, setSdSteps] = useState<number>(30);
  const [sdCfgScale, setSdCfgScale] = useState<number>(7.5);
  const [geminiModelName, setGeminiModelName] = useState<string>('gemini-pro-vision'); // Or your default
  const [genericSizeInput, setGenericSizeInput] = useState<string>('1024x1024');


  useEffect(() => {
    if (isOpen && character) {
      let autoPrompt = `Character: ${character.name}.`;
      if (character.appearance_description) {
        autoPrompt += ` Appearance: ${character.appearance_description}.`;
      }
      if (character.description) {
        autoPrompt += ` Description: ${character.description}.`;
      }
      if (character.notes_for_llm) {
        autoPrompt += ` LLM Notes: ${character.notes_for_llm}.`;
      }
      autoPrompt += " Style: detailed digital illustration, fantasy art."; // Updated default style
      setBasePrompt(autoPrompt);
      setAdditionalDetails(''); // Reset additional details
    }
  }, [isOpen, character]);

  const handleSubmit = () => {
    if (!basePrompt.trim()) {
      // Basic validation, parent can show error
      alert("Base prompt cannot be empty.");
      return;
    }
    const settings: CharacterImageGenSettings = {
      model_name: selectedModel,
    };
    if (selectedModel === 'dall-e') {
      settings.size = dalleSize;
      settings.quality = dalleQuality;
    } else if (selectedModel === 'stable-diffusion') {
      settings.size = genericSizeInput;
      settings.steps = sdSteps;
      settings.cfg_scale = sdCfgScale;
    } else if (selectedModel === 'gemini') {
      settings.size = genericSizeInput; // Conceptual
      settings.gemini_model_name = geminiModelName;
    }
    onSubmit(basePrompt, additionalDetails, settings);
  };

  const renderModelSpecificOptions = () => {
    // This can be copied/adapted from ImageGenerationModal.tsx or made a shared component
    if (selectedModel === 'dall-e') {
      return (
        <>
          <label>
            DALL-E Size:
            <select value={dalleSize} onChange={(e) => setDalleSize(e.target.value)} disabled={isGenerating}>
              <option value="1024x1024">1024x1024</option>
              <option value="1792x1024">1792x1024</option>
              <option value="1024x1792">1024x1792</option>
            </select>
          </label>
          <label>
            DALL-E Quality:
            <select value={dalleQuality} onChange={(e) => setDalleQuality(e.target.value)} disabled={isGenerating}>
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
            <input type="text" className="form-input" value={genericSizeInput} onChange={(e) => setGenericSizeInput(e.target.value)} placeholder="e.g., 1024x1024" disabled={isGenerating} />
          </label>
          <label>
            Steps:
            <input type="number" className="form-input" value={sdSteps} onChange={(e) => setSdSteps(parseInt(e.target.value, 10) || 30)} disabled={isGenerating} />
          </label>
          <label>
            CFG Scale:
            <input type="number" step="0.1" className="form-input" value={sdCfgScale} onChange={(e) => setSdCfgScale(parseFloat(e.target.value) || 7.5)} disabled={isGenerating} />
          </label>
        </>
      );
    } else if (selectedModel === 'gemini') {
      return (
        <>
          <label>
            Size (Gemini - Conceptual):
            <input type="text" className="form-input" value={genericSizeInput} onChange={(e) => setGenericSizeInput(e.target.value)} placeholder="e.g., 1024x1024" disabled={isGenerating} />
          </label>
          <label>
            Gemini Model Name (Optional):
            <input type="text" className="form-input" value={geminiModelName} onChange={(e) => setGeminiModelName(e.target.value)} placeholder="e.g., gemini-pro-vision" disabled={isGenerating} />
          </label>
        </>
      );
    }
    return null;
  };


  if (!isOpen || !character) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Generate Image for ${character.name}`}>
      <div className="image-generation-modal-content"> {/* Reuse class for styling consistency */}
        <div className="character-context-section" style={{ marginBottom: '15px', paddingBottom: '10px', borderBottom: '1px solid #eee' }}>
          <p><strong>Character:</strong> {character.name}</p>
          {character.appearance_description && (
            <p className="pre-wrap" style={{ fontSize: '0.9em', maxHeight: '100px', overflowY: 'auto' }}>
              <strong>Current Appearance:</strong> {character.appearance_description}
            </p>
          )}
        </div>

        <CollapsibleSection
          title="View/Edit Auto-Generated Base Prompt"
          initialCollapsed={true}
          className="prompt-collapsible-section" // Optional: for specific styling of this collapsible
        >
          <label htmlFor="basePromptModalInput" className="sr-only">Base Prompt (auto-generated, feel free to edit):</label>
          <textarea
            id="basePromptModalInput"
            className="prompt-textarea" // Existing class for styling
            value={basePrompt}
            onChange={(e) => setBasePrompt(e.target.value)}
            rows={6} // Increased rows for better visibility when expanded
            disabled={isGenerating}
            style={{ marginTop: '5px' }} // Add some space below the title when expanded
          />
        </CollapsibleSection>

        <label htmlFor="additionalDetailsModalInput" style={{ marginTop: '15px', display: 'block' }}> {/* Added display:block for proper spacing */}
          Additional Details / Customizations (Your Prompt):
          <textarea
            id="additionalDetailsModalInput"
            className="prompt-textarea"
            value={additionalDetails}
            onChange={(e) => setAdditionalDetails(e.target.value)}
            placeholder="e.g., a castle in the background, specific clothing, dynamic pose"
            rows={3}
            disabled={isGenerating}
          />
        </label>

        {/* Settings Section - Can be made collapsible later */}
        {/* Settings Section - Styled to match ImageGenerationModal's collapsible approach later */}
        <div className="image-generation-settings" style={{ marginTop: '20px', borderTop: '1px solid #eee', paddingTop: '15px' }}>
          <h4 style={{ marginTop: '0', marginBottom: '15px' }}>Image Generation Settings</h4>
          <div className="settings-grid"> {/* Optional: Use a grid for better layout if needed */}
            <label>
              Model:
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value as ImageModelName)}
                disabled={isGenerating}
                className="form-select" // Added for styling consistency
              >
                <option value="dall-e">DALL-E</option>
                <option value="stable-diffusion">Stable Diffusion</option>
                <option value="gemini">Gemini</option>
              </select>
            </label>
            {renderModelSpecificOptions()}
          </div>
        </div>

        <div className="modal-actions"> {/* Ensure this class is styled like in ImageGenerationModal.css */}
          <Button onClick={handleSubmit} disabled={isGenerating || !basePrompt.trim()}>
            {isGenerating ? 'Generating...' : 'Generate Image'}
          </Button>
          <Button onClick={onClose} variant="secondary" disabled={isGenerating}>
            Cancel
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default CharacterImagePromptModal;
