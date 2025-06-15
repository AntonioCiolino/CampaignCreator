import React, { useState, useEffect } from 'react';
import { CampaignSection } from '../services/campaignService';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import ReactQuill from 'react-quill';
import LoadingSpinner from './common/LoadingSpinner'; // Adjust path if necessary
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
  // Prop for updating section type
  onSectionTypeUpdate?: (sectionId: number, newType: string) => void; // Optional for now
  onSetThematicImageFromSection?: (imageUrl: string, promptUsed: string) => void;
  expandSectionId: string | null; // Add this
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
  onSectionTypeUpdate, // Destructure the new prop
  onSetThematicImageFromSection,
  expandSectionId, // Add this
}) => {

  // Function to get tooltip text based on section type
  const getTooltipText = (sectionType: string | undefined): string => {
    switch (sectionType?.toLowerCase()) {
      case "npc":
        return "Suggested: Name, Description, Stats, Motivations, Plot Hooks";
      case "character":
        return "Suggested: Name, Description, Stats, Motivations, Plot Hooks";
      case "location":
        return "Suggested: Description, Atmosphere, Inhabitants, Points of Interest, Secrets";
      case "item":
        return "Suggested: Appearance, Powers, History, How to Obtain/Use";
      case "quest":
        return "Suggested: Objectives, Key NPCs, Steps, Rewards, Consequences";
      case "monster":
        return "Suggested: Appearance, Abilities, Lair, Combat Tactics";
      case "chapter":
        return "Suggested: Overview, Key Events, Encounters, Challenges";
      case "note":
        return "General notes or ideas for this section.";
      case "world_detail":
        return "Detailed information about the game world, lore, history, factions, etc.";
      case "generic":
        return "General content for this section. Define the structure as needed.";
      default:
        return "Enter content for this section. You can define the structure and details as needed.";
    }
  };

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
    // Check if this section is the one to be expanded and if it's currently collapsed
    if (expandSectionId === section.id.toString() && isCollapsed) {
      setIsCollapsed(false);
    }
  }, [expandSectionId, section.id, isCollapsed, setIsCollapsed]); // Add dependencies

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

    if (quillInstance) {
      quillInstance.setText(section.content || ''); // Set Quill's content directly using plain text
      setEditedContent(quillInstance.root.innerHTML); // Sync React state with Quill's HTML
    } else {
      // Fallback if Quill instance isn't ready (should be rare if editor is visible)
      console.warn("Quill instance not available in handleEdit. Falling back to setting plain text directly to state.");
      setEditedContent(section.content || '');
    }

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
    if (!quillInstance) {
      console.error("Quill instance not available for inserting random item.");
      // Fallback: append to the current content if Quill is not available
      setEditedContent(prevContent => {
        const prefix = prevContent && !prevContent.endsWith(' ') && !prevContent.endsWith('\n') ? " " : "";
        return prevContent + prefix + itemText;
      });
      return;
    }

    const range = quillInstance.getSelection();
    let insertionPoint;

    if (range) {
      insertionPoint = range.index;
      // If there's a selection, we could choose to replace it or insert after.
      // For simplicity, this example inserts at the start of the selection.
      // To replace: quillInstance.deleteText(range.index, range.length, 'user');
    } else {
      // No selection, insert at current cursor position or end of document
      insertionPoint = quillInstance.getLength(); // Defaults to end if no cursor focus
      if (insertionPoint > 0) insertionPoint -=1; // Adjust if getLength() is used for end
      else insertionPoint = 0; // Ensure not negative
    }

    // Ensure insertionPoint is not negative if getLength() was 0 or 1.
    if (insertionPoint < 0) insertionPoint = 0;


    let textToInsert = itemText;
    if (insertionPoint > 0) {
      const textBefore = quillInstance.getText(insertionPoint - 1, 1);
      if (textBefore !== ' ' && textBefore !== '\n') {
        textToInsert = " " + itemText;
      }
    }

    quillInstance.insertText(insertionPoint, textToInsert, 'user');
    quillInstance.setSelection(insertionPoint + textToInsert.length, 0, 'user');
    setEditedContent(quillInstance.root.innerHTML);
  };

  const handleSave = async () => {
    setLocalSaveError(null);
    setSaveSuccess(false);

    if (!quillInstance) {
      console.error("Editor not available. Cannot save.");
      setLocalSaveError("Editor not available. Cannot save.");
      // setLocalSaving(false); // We don't have localSaving in this version of the code
      return;
    }

    try {
      // For now, only content is editable in this component.
      // Title/order would be handled elsewhere or if this component is expanded.
      await onSave(section.id, { content: quillInstance.getText() });
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
    <div id={`section-container-${section.id}`} className="campaign-section-view" tabIndex={-1}>
      {section.title && (
        <div className="section-title-header" onClick={() => setIsCollapsed(!isCollapsed)}>
          <h3 className="section-title">
            {isCollapsed ? '▶' : '▼'} {section.title}
          </h3>
          {/* Display Section Type if not editing title area */}
          {!isEditing && section.type && (
            <span style={{ marginLeft: '10px', fontSize: '0.8em', color: '#666', fontStyle: 'italic' }}>
              ({section.type})
            </span>
          )}
        </div>
      )}

      {!isCollapsed && (
        <>
          {/* Section Type Input - Placed here for better visibility and context */}
          {onSectionTypeUpdate && ( // Only show if handler is provided
            <div style={{ padding: '5px 10px', display: 'flex', alignItems: 'center', backgroundColor: '#f9f9f9' }}>
              <label htmlFor={`section-type-${section.id}`} style={{ marginRight: '8px', fontSize: '0.9em', fontWeight: 'bold' }}>Type:</label>
              <input
                id={`section-type-${section.id}`}
                type="text"
                value={section.type || ''}
                onChange={(e) => onSectionTypeUpdate(section.id, e.target.value)}
                placeholder="e.g., NPC, Location, Quest"
                title="Defines the category of the section (e.g., NPC, Location, Quest, Item, Monster, Chapter, Note, Generic). This helps in organizing and can assist AI content generation."
                style={{
                  flexGrow: 1,
                  padding: '6px 10px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '0.9em'
                }}
              />
            </div>
          )}

          {isEditing ? (
            <div className="section-editor" title={getTooltipText(section.type)}>
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
                <Button
                  onClick={handleGenerateContent}
                  className="editor-button"
                  disabled={isGeneratingContent || isSaving}
                  style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
                >
                  {isGeneratingContent && <LoadingSpinner />}
                  <span>{isGeneratingContent ? 'Generating...' : 'Generate Content'}</span>
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
                <Button
                  onClick={handleEdit}
                  variant="secondary"
                  size="sm"
                  className="editor-button" // Removed edit-button, specific color styling will be removed from CSS
                >
                  Edit Section Content
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleRegenerateClick}
                  disabled={isSaving || isRegenerating || isEditing}
                  style={{ marginLeft: '10px', display: 'flex', alignItems: 'center', gap: '5px' }}
                >
                  {isRegenerating && <LoadingSpinner />}
                  <span>{isRegenerating ? 'Regenerating...' : 'Regenerate'}</span>
                </Button>
                <Button
                  onClick={() => onDelete(section.id)}
                  variant="danger"
                  size="sm"
                  className="editor-button delete-button" // delete-button class might still have specific icon color logic
                  style={{ marginLeft: '10px' }}
                >
                  Delete Section
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
        onImageSuccessfullyGenerated={(imageUrl, promptUsed) => {
          if (!quillInstance) {
            console.error("Quill instance not available for inserting image or setting alt text.");
            setEditedContent(prev => `${prev}\n![${promptUsed || 'Generated Image'}](${imageUrl})\n`);
            setIsImageGenerationModalOpen(false);
            return;
          }

          const range = quillInstance.getSelection(true) || { index: quillInstance.getLength() -1, length: 0 };
          // Ensure range.index is valid if editor is empty or nearly empty
          let safeIndex = range.index;
          if (quillInstance.getLength() === 1 && safeIndex > 0) { // Quill starts with a newline
             safeIndex = 0;
          } else if (safeIndex < 0) {
             safeIndex = 0;
          }

          quillInstance.insertEmbed(safeIndex, 'image', imageUrl, 'user');

          try {
            setTimeout(() => {
              if (!quillInstance) return; // Check again inside timeout
              const editorRoot = quillInstance.root;
              // Query for the specific image. Note: src might get proxied or altered by Quill/browser.
              // A more robust way might involve marking the image somehow before insertion if this fails.
              const imgElements = editorRoot.querySelectorAll(`img[src="${imageUrl}"]`);
              if (imgElements.length > 0) {
                const imgElement = imgElements[imgElements.length - 1] as HTMLImageElement; // Assume last is newest
                imgElement.alt = promptUsed || 'Generated image'; // Set alt text
                // Update Quill's internal model if direct DOM manipulation isn't picked up
                // This ensures the change is saved and part of the undo/redo stack.
                setEditedContent(quillInstance.root.innerHTML);
              } else {
                console.warn("Could not find the inserted image to set alt text for src:", imageUrl);
              }
            }, 100); // 100ms delay to allow Quill to render the image
          } catch (e) {
            console.error("Error setting alt text for image:", e);
          }

          // Move cursor after the inserted image + a space for better UX
          // Quill inserts images as 0-length embeds, cursor behavior can be tricky.
          // This attempts to place it after.
          quillInstance.setSelection(safeIndex + 1, 0, 'user');


          setIsImageGenerationModalOpen(false);
        }}
        onSetAsThematic={onSetThematicImageFromSection}
        primaryActionText="Insert into Editor"
        autoApplyDefault={true}
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
