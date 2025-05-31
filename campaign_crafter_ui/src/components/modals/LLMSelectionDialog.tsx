import React, { useState, useEffect } from 'react';
import LLMSelector from '../LLMSelector'; // Adjust path as needed
import './LLMSelectionDialog.css'; // We'll create this CSS file later

interface LLMSelectionDialogProps {
  isOpen: boolean;
  currentModelId: string | null;
  onModelSelect: (selectedModelId: string | null) => void;
  onClose: () => void;
  // Optional: To pass down the list of models if already fetched by parent
  // availableLLMs?: LLMModel[];
}

const LLMSelectionDialog: React.FC<LLMSelectionDialogProps> = ({
  isOpen,
  currentModelId,
  onModelSelect,
  onClose,
  // availableLLMs
}) => {
  const [selectedModelInDialog, setSelectedModelInDialog] = useState<string | null>(currentModelId);

  // Update local state if the currentModelId prop changes (e.g., from parent)
  useEffect(() => {
    setSelectedModelInDialog(currentModelId);
  }, [currentModelId]);

  if (!isOpen) {
    return null;
  }

  const handleSelect = () => {
    onModelSelect(selectedModelInDialog);
    onClose();
  };

  const handleCancel = () => {
    // Reset selection to what it was when dialog opened, then close
    setSelectedModelInDialog(currentModelId);
    onClose();
  };

  const handleModelChangeInSelector = (modelId: string | null) => {
    setSelectedModelInDialog(modelId);
  };

  return (
    <div className="llm-selection-dialog-backdrop">
      <div className="llm-selection-dialog-content">
        <h2>Select LLM Model</h2>
        <LLMSelector
          onModelChange={handleModelChangeInSelector}
          initialSelectedModelId={selectedModelInDialog}
          // Pass down pre-fetched models if that optimization is chosen later
          // availableLLMs={availableLLMs}
          label="Choose a model:"
          className="llm-selector-in-dialog"
        />
        <div className="llm-selection-dialog-actions">
          <button onClick={handleSelect} className="dialog-button select-button">
            Select
          </button>
          <button onClick={handleCancel} className="dialog-button cancel-button">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default LLMSelectionDialog;
