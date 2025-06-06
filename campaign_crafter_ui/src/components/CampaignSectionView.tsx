import React, { useState, useEffect } from 'react';
import { CampaignSection } from '../services/campaignService';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import ReactQuill from 'react-quill';
import type { RangeStatic as QuillRange } from 'quill'; // Import QuillRange
import 'react-quill/dist/quill.snow.css'; // Import Quill's snow theme CSS
import Button from './common/Button'; // Added Button import
import RandomTableRoller from './RandomTableRoller';
import ImageGenerationModal from './modals/ImageGenerationModal/ImageGenerationModal'; // Import the new modal
import './CampaignSectionView.css';
import { CampaignSectionUpdatePayload } from '../services/campaignService';
import { generateTextLLM, LLMTextGenerationParams } from '../services/llmService';
import { getFeatures } from '../services/featureService'; // Added import
import { Feature } from '../types/featureTypes'; // Added import
import * as campaignService from '../services/campaignService'; // Moved import to top

interface CampaignSectionViewProps {
  section: CampaignSection;
  onSave: (sectionId: number, updatedData: CampaignSectionUpdatePayload) => Promise<void>;
  isSaving: boolean; // Prop to indicate if this specific section is being saved
  saveError: string | null; // Prop to display save error for this section
  onDelete: (sectionId: number) => void; // Added onDelete prop
  forceCollapse?: boolean; // Optional prop to force collapse state
  // Props for regeneration
  campaignId: string | number; // Campaign ID to make the API call
  onSectionUpdated: (updatedSection: CampaignSection) => void; // Callback to update parent state
}

const CampaignSectionView: React.FC<CampaignSectionViewProps> = ({
  section,
  onSave,
  isSaving,
  saveError: externalSaveError,
  onDelete,
  forceCollapse,
  campaignId,
  onSectionUpdated,
}) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    // If section.title is "Campaign Concept", it's collapsed.
    // Otherwise, it retains its current default behavior (true).
    if (section.title === "Campaign Concept") {
      return true;
    }
    return true; // Default for other sections
  });
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedContent, setEditedContent] = useState<string>(section.content || '');
  const [quillInstance, setQuillInstance] = useState<any>(null); // Enabled to store Quill instance
  const [localSaveError, setLocalSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [isImageGenerationModalOpen, setIsImageGenerationModalOpen] = useState<boolean>(false);
  const [isGeneratingContent, setIsGeneratingContent] = useState<boolean>(false);
  const [contentGenerationError, setContentGenerationError] = useState<string | null>(null);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [selectedFeatureId, setSelectedFeatureId] = useState<string>("");
  const [featureFetchError, setFeatureFetchError] = useState<string | null>(null);
  const [isRegenerating, setIsRegenerating] = useState<boolean>(false);
  const [regenerateError, setRegenerateError] = useState<string | null>(null);


  // Ensure editedContent is updated if the section prop changes externally
  // (e.g. if parent component re-fetches and passes a new section object, or after a save)
  useEffect(() => {
    setEditedContent(section.content || '');
    // If the external save error for this section is cleared, clear local error too
    if (externalSaveError === null) {
        setLocalSaveError(null);
    }
  }, [section.content, externalSaveError]);

  useEffect(() => {
    if (forceCollapse !== undefined) {
      setIsCollapsed(forceCollapse);
    }
  }, [forceCollapse]);

  useEffect(() => {
    if (isEditing && features.length === 0 && !featureFetchError) {
      const loadFeatures = async () => {
        try {
          setFeatureFetchError(null);
          const fetchedFeatures = await getFeatures();
          setFeatures(fetchedFeatures);
        } catch (error) {
          console.error("Failed to load features:", error);
          setFeatureFetchError(error instanceof Error ? error.message : "An unknown error occurred while fetching features.");
        }
      };
      loadFeatures();
    } else if (!isEditing) {
      // Optional: Clear features or selected feature when not editing
      // setSelectedFeatureId("");
    }
  }, [isEditing, features.length, featureFetchError]);
  
  const handleEdit = () => {
    setIsCollapsed(false); // Expand section on edit
    setEditedContent(section.content || '');
    setIsEditing(true);
    setLocalSaveError(null); // Clear local errors when starting to edit
    setSaveSuccess(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedContent(section.content || '');
    setLocalSaveError(null);
    setSaveSuccess(false);
    setContentGenerationError(null); // Clear content generation error on cancel
  };

  const handleGenerateContent = async () => {
    setIsGeneratingContent(true);
    setContentGenerationError(null);
    let initialSelectionRange: QuillRange | null = null; // Use QuillRange

    try {
      let contextText = '';
      if (quillInstance) {
        initialSelectionRange = quillInstance.getSelection();
        if (initialSelectionRange && initialSelectionRange.length > 0) {
          contextText = quillInstance.getText(initialSelectionRange.index, initialSelectionRange.length);
        } else {
          // Get all text if no selection, but trim it to avoid overly long contexts.
          // Or consider a configurable max context length.
          const fullText = quillInstance.getText();
          contextText = fullText.substring(0, 2000); // Limit context length
        }
      } else {
        contextText = editedContent.substring(0, 2000); // Fallback and limit
      }

      let finalPrompt = "";
      if (selectedFeatureId) {
        const selectedFeature = features.find(f => f.id.toString() === selectedFeatureId); // Ensure ID types are compared correctly
        if (selectedFeature) {
          if (selectedFeature.template.includes("{}")) {
            finalPrompt = selectedFeature.template.replace("{}", contextText);
          } else {
            finalPrompt = selectedFeature.template; // Context from editor is ignored
          }
        } else {
          // Fallback if selectedFeatureId is somehow invalid
          finalPrompt = `Generate content based on the following context: ${contextText}`;
        }
      } else {
        finalPrompt = `Generate content based on the following context: ${contextText}`;
      }

      const params: LLMTextGenerationParams = {
        prompt: finalPrompt,
        model_id_with_prefix: null, // Use default model
        // Add any other params like max_tokens, temperature if needed
      };

      const response = await generateTextLLM(params);
      const generatedText = response.text; // Changed generated_text to text

      if (quillInstance) {
        // initialSelectionRange was captured at the beginning of the function.
        // We use it to decide the mode of operation (insert after selection, or append to end).

        if (initialSelectionRange && initialSelectionRange.length > 0) {
          // Insert generated text AFTER the selected text
          const insertionPoint = initialSelectionRange.index + initialSelectionRange.length;
          const textToInsert = " " + generatedText; // Prepend with a space

          quillInstance.insertText(insertionPoint, textToInsert, 'user');
          // Set cursor to the end of the newly inserted text
          quillInstance.setSelection(insertionPoint + textToInsert.length, 0, 'user');
        } else {
          // No initial selection, so insert at the current cursor position
          const currentCursorSelection = quillInstance.getSelection(); // Get current cursor
          let insertionPoint = currentCursorSelection ? currentCursorSelection.index : (quillInstance.getLength() -1);
          // Ensure insertionPoint is not negative if getLength() was 0 or 1.
          if (insertionPoint < 0) insertionPoint = 0;

          // For inserting at cursor, we might not need a leading newline by default,
          // unless cursor is at the very start of an empty line or end of doc.
          // For simplicity now, just insert the text. User can add spaces/newlines.
          // const textToInsert = generatedText;
          // Consider adding a space if the preceding character isn't a space, similar to random item insertion.
          let textToInsert = generatedText;
          if (insertionPoint > 0) {
            const textBefore = quillInstance.getText(insertionPoint - 1, 1);
            if (textBefore !== ' ' && textBefore !== '\n') {
              textToInsert = " " + generatedText;
            }
          }

          quillInstance.insertText(insertionPoint, textToInsert, 'user');
          // Move cursor to the end of the inserted text
          quillInstance.setSelection(insertionPoint + textToInsert.length, 0, 'user');
        }
        setEditedContent(quillInstance.root.innerHTML);
      } else {
        // Fallback: Append to editedContent state
        // This won't handle replacing selected text if quillInstance was initially null.
        setEditedContent(prev => prev + "\n" + generatedText);
      }

    } catch (error) {
      console.error("Failed to generate content:", error);
      setContentGenerationError('Failed to generate content. An error occurred.');
    } finally {
      setIsGeneratingContent(false);
    }
  };

  const handleInsertRandomItem = (itemText: string) => {
    // For now, append to the current content.
    // A more advanced implementation would insert at the cursor in ReactQuill.
    // This might require getting a ref to the Quill instance.
    setEditedContent(prevContent => {
      // Add a space if prevContent is not empty and doesn't end with a space
      const prefix = prevContent && !prevContent.endsWith(' ') && !prevContent.endsWith('\n') ? " " : "";
      return prevContent + prefix + itemText;
    });
    // If you have the Quill instance, you could do:
    // if (quillInstance) {
    //   const range = quillInstance.getSelection(true);
    //   quillInstance.insertText(range.index, itemText, 'user');
    // }
  };

  const handleSave = async () => {
    setLocalSaveError(null);
    setSaveSuccess(false);
    try {
      // For now, only content is editable in this component.
      // Title/order would be handled elsewhere or if this component is expanded.
      await onSave(section.id, { content: editedContent });
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000); // Display success for 3s
    } catch (error) {
      console.error("Failed to save section content:", error);
      // The error might already be set by the parent via `externalSaveError`
      // if the parent re-throws. We can also set a local one.
      setLocalSaveError('Failed to save. Please try again.');
      // No need to re-throw if parent is already handling and passing `saveError` prop
    }
  };

  const quillModules = {
    toolbar: {
      container: [
        [{ 'header': [1, 2, 3, false] }],
        ['bold', 'italic', 'underline', 'strike', 'blockquote'],
        [{'list': 'ordered'}, {'list': 'bullet'}, {'indent': '-1'}, {'indent': '+1'}],
        ['link', 'image'], // Enabled 'image'
        ['clean']
      ]
    },
  };

  const quillFormats = [
    'header',
    'bold', 'italic', 'underline', 'strike', 'blockquote',
    'list', 'bullet', 'indent',
    'link', 'image' // Added 'image'
  ];

  // Function to get the Quill instance
  const setQuillRef = (el: ReactQuill | null) => {
    if (el) {
      setQuillInstance(el.getEditor());
    }
  };

  const handleRegenerateClick = async () => {
    if (!campaignId || !section?.id) {
      setRegenerateError("Missing campaign or section ID for regeneration.");
      return;
    }
    setIsRegenerating(true);
    setRegenerateError(null);
    try {
      // Using an empty payload for now, as per plan
      const updatedSection = await campaignService.regenerateCampaignSection(campaignId, section.id, {});
      onSectionUpdated(updatedSection); // Notify parent of the update
      // Update local state as well, e.g., editedContent if it was based on section.content
      setEditedContent(updatedSection.content || '');
      // If title can be regenerated and shown in this component directly:
      // setSectionTitle(updatedSection.title); // Assuming you add local state for title if it's editable here
    } catch (error: any) {
      console.error("Failed to regenerate section:", error);
      setRegenerateError(error.message || 'An unexpected error occurred during regeneration.');
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <div className="campaign-section-view">
      {section.title && (
        <div className="section-title-header" onClick={() => setIsCollapsed(!isCollapsed)}>
          <h3 className="section-title">
            {isCollapsed ? '▶' : '▼'} {section.title}
          </h3>
        </div>
      )}

      {!isCollapsed && (
        <>
          {isEditing ? (
            <div className="section-editor">
              <ReactQuill
                theme="snow"
                value={editedContent}
                onChange={setEditedContent}
                modules={quillModules}
                formats={quillFormats}
                className="quill-editor"
                ref={setQuillRef} // Set the ref to get Quill instance
              />
              {/* Random Table Roller Integration */}
              <RandomTableRoller onInsertItem={handleInsertRandomItem} />
              
              <div className="editor-actions">
                <Button onClick={handleSave} className="editor-button" disabled={isSaving || isGeneratingContent}>
                  {isSaving ? 'Saving...' : 'Save Content'}
                </Button>
                {isEditing && (
                  <div className="feature-selector-group" style={{ marginRight: '10px', display: 'inline-block', verticalAlign: 'middle' }}>
                    <select
                      value={selectedFeatureId}
                      onChange={(e) => setSelectedFeatureId(e.target.value)}
                      disabled={isGeneratingContent || isSaving || features.length === 0}
                      style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #ccc', height: '38px', boxSizing: 'border-box' }}
                      title={features.length === 0 && !featureFetchError ? "Loading features..." : (featureFetchError ? "Error loading features" : "Select a feature to guide content generation")}
                    >
                      <option value="">-- No Specific Feature --</option>
                      {features.map(feature => (
                        <option key={feature.id} value={feature.id}>
                          {feature.name}
                        </option>
                      ))}
                    </select>
                    {featureFetchError && <p className="error-message" style={{fontSize: '0.8em', color: 'red', marginTop: '2px'}}>{featureFetchError}</p>}
                  </div>
                )}
                <Button onClick={handleGenerateContent} className="editor-button" disabled={isGeneratingContent || isSaving}>
                  {isGeneratingContent ? 'Generating...' : 'Generate Content'}
                </Button>
                <Button onClick={() => setIsImageGenerationModalOpen(true)} className="editor-button" disabled={isGeneratingContent || isSaving}>
                  Generate Image
                </Button>
                <Button onClick={handleCancel} className="editor-button" variant="secondary" disabled={isSaving || isGeneratingContent}>
                  Cancel
                </Button>
                {localSaveError && <p className="error-message editor-feedback">{localSaveError}</p>}
                {externalSaveError && !localSaveError && <p className="error-message editor-feedback">{externalSaveError}</p>}
                {contentGenerationError && <p className="error-message editor-feedback">{contentGenerationError}</p>}
                {saveSuccess && <p className="success-message editor-feedback">Content saved!</p>}
              </div>
            </div>
          ) : (
            <>
              <div className="section-content">
                <ReactMarkdown rehypePlugins={[rehypeRaw]}>{section.content}</ReactMarkdown>
              </div>
              <div className="view-actions">
                <button onClick={handleEdit} className="editor-button edit-button">
                  Edit Section Content
                </button>
                <Button
                  onClick={() => onDelete(section.id)}
                  variant="danger"
                  size="sm"
                  className="editor-button delete-button" // Keep existing classes if they add value
                  style={{ marginLeft: '10px' }}
                >
                  Delete Section
                </Button>
                <Button
                  size="sm"
                  variant="secondary" // Changed from "text" to "secondary"
                  onClick={handleRegenerateClick}
                  disabled={isSaving || isRegenerating || isEditing}
                  style={{ marginLeft: '10px' }}
                >
                  {isRegenerating ? 'Regenerating...' : 'Regenerate'}
                </Button>
              </div>
              {regenerateError && <p className="error-message editor-feedback" style={{ marginTop: '5px' }}>{regenerateError}</p>}
            </>
          )}
        </>
      )}
      <ImageGenerationModal
        isOpen={isImageGenerationModalOpen}
        onClose={() => setIsImageGenerationModalOpen(false)}
        // onImageGenerated={(imageUrl) => {
        //   // Optionally insert the image URL into the editor or handle as needed
        //   console.log("Generated image URL:", imageUrl);
        //   // Example: Insert into Quill (would require quillInstance)
        //   // if (quillInstance) {
        //   //   const range = quillInstance.getSelection(true) || { index: editedContent.length, length: 0 };
        //   //   quillInstance.insertEmbed(range.index, 'image', imageUrl, 'user');
        //   //   // Or, to insert as markdown if your editor handles it:
        //   //   // quillInstance.insertText(range.index, `\n![Generated Image](${imageUrl})\n`, 'user');
        //   //   setEditedContent(quillInstance.root.innerHTML); // Or however you get content from Quill
        //   // } else {
        //   // Fallback: append to text state if no Quill instance
        //     setEditedContent(prev => `${prev}\n![Generated Image](${imageUrl})\n`);
        //   // }
        //   setIsImageGenerationModalOpen(false); // Close modal after generation
        // }}
        // This modal is for AI image generation, the toolbar button is for URL insertion.
        // If AI generated image URL needs to be inserted into editor, the onImageSuccessfullyGenerated
        // prop for ImageGenerationModal (if it's added) could use a similar logic to handleImageInsert.
        onImageSuccessfullyGenerated={(imageUrl) => { // Example if you want to connect it
          if (quillInstance) {
            const range = quillInstance.getSelection(true) || { index: editedContent.length, length: 0 };
            quillInstance.insertEmbed(range.index, 'image', imageUrl, 'user');
          } else {
            setEditedContent(prev => `${prev}\n![Generated Image](${imageUrl})\n`);
          }
          setIsImageGenerationModalOpen(false);
        }}
      />
    </div>
  );
};

// Helper function (or move to service if used elsewhere)
// For now, keeping it here for simplicity as it's only used by handleRegenerateClick
// No, this should be in campaignService.ts. The call will be made there.
// CampaignSectionView will call onRegenerate which is handleRegenerateSection in CampaignSectionEditor,
// which then calls the service.
export default CampaignSectionView;
