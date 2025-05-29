import React, { useState, useEffect, ChangeEvent } from 'react';
import { getAvailableLLMs, LLMModel } from '../services/llmService';
import './LLMSelector.css'; // Import the CSS file

interface LLMSelectorProps {
  onModelChange: (selectedModelId: string | null) => void;
  initialSelectedModelId?: string | null;
  label?: string;
  className?: string; // For the wrapper div
  selectClassName?: string; // For the select element itself
}

const LLMSelector: React.FC<LLMSelectorProps> = ({ 
  onModelChange, 
  initialSelectedModelId = null,
  label = "Select LLM Model:",
  className = '',
  selectClassName = '',
}) => {
  const [llmModels, setLlmModels] = useState<LLMModel[]>([]);
  const [currentSelectedModelId, setCurrentSelectedModelId] = useState<string | null>(initialSelectedModelId);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const models = await getAvailableLLMs();
        setLlmModels(models);
        if (models.length > 0) {
          const initialModelExists = initialSelectedModelId && models.some(m => m.id === initialSelectedModelId);
          if (initialModelExists) {
            setCurrentSelectedModelId(initialSelectedModelId);
            // onModelChange(initialSelectedModelId); // Avoid calling on initial prop set
          } else if (!initialSelectedModelId && models.length > 0) {
            setCurrentSelectedModelId(models[0].id);
            onModelChange(models[0].id); 
          } else {
            setCurrentSelectedModelId(initialSelectedModelId); // Respect null or non-existent initial ID
            // onModelChange(initialSelectedModelId);
          }
        } else {
          setCurrentSelectedModelId(null);
          // onModelChange(null); // If no models, effectively no selection
        }
      } catch (err) {
        console.error("Failed to fetch LLM models:", err);
        setError(err instanceof Error ? err.message : "An unknown error occurred while fetching models.");
        setLlmModels([]);
        setCurrentSelectedModelId(null);
        // onModelChange(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchModels();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Intentionally run once on mount. initialSelectedModelId is for initial state.

  useEffect(() => {
    // This effect synchronizes currentSelectedModelId if initialSelectedModelId prop changes *after* initial mount
    // and models are already loaded.
    if (initialSelectedModelId !== undefined && llmModels.length > 0) {
        const modelExists = llmModels.some(m => m.id === initialSelectedModelId);
        if (modelExists) {
            setCurrentSelectedModelId(initialSelectedModelId);
        } else if (initialSelectedModelId === null) { // Explicitly set to null
            setCurrentSelectedModelId(null);
        }
        // Not calling onModelChange here to prevent potential loops if parent isn't careful
    } else if (initialSelectedModelId === null && llmModels.length > 0) {
        // If initial prop becomes null, reflect that
        setCurrentSelectedModelId(null);
    }
  }, [initialSelectedModelId, llmModels]);


  const handleSelectionChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const newSelectedModelId = event.target.value;
    const finalModelId = newSelectedModelId === "" || newSelectedModelId === "none" ? null : newSelectedModelId;
    setCurrentSelectedModelId(finalModelId);
    onModelChange(finalModelId);
  };

  const wrapperClasses = ['llm-selector-wrapper', className].filter(Boolean).join(' ');
  // Apply global .form-select and local .llm-selector-select for cascading styles
  const selectClasses = ['form-select', 'llm-selector-select', selectClassName].filter(Boolean).join(' ');


  if (isLoading) {
    return <div className={wrapperClasses}><p className="llm-selector-loading">Loading LLM models...</p></div>;
  }

  if (error) {
    return <div className={wrapperClasses}><p className="llm-selector-error">Error: {error}</p></div>;
  }

  if (llmModels.length === 0) {
    return <div className={wrapperClasses}><p className="llm-selector-no-models">No LLM models available.</p></div>;
  }

  return (
    <div className={wrapperClasses}>
      {label && <label htmlFor="llm-selector-id" className="llm-selector-label">{label}</label>}
      <select 
        id="llm-selector-id"
        value={currentSelectedModelId || "none"} // Use "none" for the placeholder option value
        onChange={handleSelectionChange}
        className={selectClasses}
      >
        <option value="none" disabled={currentSelectedModelId !== null}>-- Select a Model (Optional) --</option>
        {llmModels.map((model) => (
          <option key={model.id} value={model.id}>
            {model.name} ({model.id})
          </option>
        ))}
      </select>
    </div>
  );
};

export default LLMSelector;
