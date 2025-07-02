import React, { useState, useEffect } from 'react'; // Removed useRef
import { CampaignSection } from '../types/campaignTypes'; // Corrected import path
import ReactMarkdown from 'react-markdown';
import { Typography } from '@mui/material';
import rehypeRaw from 'rehype-raw';
import ReactQuill from 'react-quill';
import LoadingSpinner from './common/LoadingSpinner'; // Adjust path if necessary
import type { RangeStatic as QuillRange } from 'quill'; // Import QuillRange
import 'react-quill/dist/quill.snow.css'; // Import Quill's snow theme CSS
import Button from './common/Button'; // Added Button import
import RandomTableRoller from './RandomTableRoller';
import ImageGenerationModal from './modals/ImageGenerationModal/ImageGenerationModal'; // Import the new modal
import './CampaignSectionView.css';
import { CampaignSectionUpdatePayload, SectionRegeneratePayload } from '../types/campaignTypes'; // CORRECTED PATH, Added SectionRegeneratePayload
import { getFeatures } from '../services/featureService';
import { Feature } from '../types/featureTypes';
import * as campaignService from '../services/campaignService';

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

// Removed ImageData interface

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
  const [snippetFeatures, setSnippetFeatures] = useState<Feature[]>([]);
  const [selectedSnippetFeatureId, setSelectedSnippetFeatureId] = useState<string>("");
  const [snippetFeatureFetchError, setSnippetFeatureFetchError] = useState<string | null>(null);
  // const [isRegenerating, setIsRegenerating] = useState<boolean>(false); // Removed
  // const [regenerateError, setRegenerateError] = useState<string | null>(null); // Removed

  // Filter features will be handled by the context menu logic later
  // const filteredFeatures = React.useMemo(() => { ... });

  // Effect to reset selectedFeatureId will be handled by context menu logic
  // useEffect(() => { ... });

  const [currentSelection, setCurrentSelection] = useState<QuillRange | null>(null);

  useEffect(() => {
    if (isEditing && quillInstance) {
      const selectionChangeHandler = (range: QuillRange, oldRange: QuillRange, source: string) => {
        if (source === 'user') {
          setCurrentSelection(range);
          if (!range || range.length === 0) { // If selection is lost or empty
            setSelectedSnippetFeatureId(""); // Reset snippet feature selection
          }
        }
      };
      quillInstance.on('selection-change', selectionChangeHandler);
      return () => {
        quillInstance.off('selection-change', selectionChangeHandler);
      };
    }
  }, [isEditing, quillInstance]);

  useEffect(() => {
    if (isEditing) { // Load snippet features when editing starts
      const loadSnippetFeatures = async () => {
        try {
          setSnippetFeatureFetchError(null);
          const allFeatures = await getFeatures();
          const filteredForSnippets = allFeatures.filter(
            f => f.feature_category === 'Snippet' || (!f.feature_category && f.name !== 'Campaign' && f.name !== 'TOC Homebrewery' && f.name !== 'TOC Display' && f.name !== 'Campaign Names') // crude fallback for older features
          );
          setSnippetFeatures(filteredForSnippets);
        } catch (error) {
          console.error("Failed to load snippet features:", error);
          setSnippetFeatureFetchError(error instanceof Error ? error.message : "An unknown error occurred while fetching snippet features.");
        }
      };
      loadSnippetFeatures();
    } else {
      setSnippetFeatures([]); // Clear when not editing
      setSelectedSnippetFeatureId("");
      setCurrentSelection(null);
    }
  }, [isEditing]);

  const [isTableRollerVisible, setIsTableRollerVisible] = useState<boolean>(false); // State for table roller visibility
  // Removed imageData state and imageIdCounter ref


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

  // useEffect(() => { // This useEffect for loading all features will be moved or adapted for snippet features context menu
  //   if (isEditing && features.length === 0 && !featureFetchError) {
  //     const loadFeatures = async () => {
  //       try {
  //         setFeatureFetchError(null);
  //         const fetchedFeatures = await getFeatures();
  //         setFeatures(fetchedFeatures);
  //       } catch (error) {
  //         console.error("Failed to load features:", error);
  //         setFeatureFetchError(error instanceof Error ? error.message : "An unknown error occurred while fetching features.");
  //       }
  //     };
  //     loadFeatures();
  //   } else if (!isEditing) {
  //     // Optional: Clear features or selected feature when not editing
  //     // setSelectedFeatureId("");
  //   }
  // }, [isEditing, features.length, featureFetchError]);
  
  const handleEdit = () => {
    setIsCollapsed(false); // Expand section on edit

    const plainTextContent = section.content || '';
    // Convert plain text to HTML: wrap each line in <p> tags.
    // This handles empty lines as <p></p>, which Quill should treat as a blank paragraph.
    // For a more robust empty line representation (like a visible space),
    // one might use <p><br></p> for lines that are truly empty.
    const lines = plainTextContent.split('\n');
    const htmlContent = lines.map(line => {
      if (line.trim() === '') {
        return '<p><br></p>';
      }
      return `<p>${line}</p>`;
    }).join('');

    setEditedContent(htmlContent);

    setIsEditing(true);
    setLocalSaveError(null); // Clear local errors when starting to edit
    setSaveSuccess(false);
    // setContentGenerationError(null); // Removed as per cleanup task
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
    // initialSelectionRange is now currentSelection state

    try {
      let editorSelectionText = '';
      let isTextActuallySelected = false;

      if (quillInstance && currentSelection && currentSelection.length > 0) {
        editorSelectionText = quillInstance.getText(currentSelection.index, currentSelection.length);
        isTextActuallySelected = true;
      } else if (quillInstance) { // No specific selection, use full text for potential user_instructions
        const fullText = quillInstance.getText();
        editorSelectionText = fullText.substring(0, 2000); // Limit context
      } else { // Fallback if no quillInstance
        editorSelectionText = editedContent.substring(0, 2000);
      }

      if (!section.id) {
        setContentGenerationError("Section ID is missing. Cannot generate content.");
        setIsGeneratingContent(false);
        return;
      }

      let featureIdForBackend: number | undefined = undefined;
      let contextDataForBackend: { [key: string]: any } = {};
      let operationType = "Full Section Generation"; // For logging

      // Check if a snippet feature is selected AND text is actually highlighted
      if (selectedSnippetFeatureId && isTextActuallySelected) {
        const snippetFeature = snippetFeatures.find(f => f.id.toString() === selectedSnippetFeatureId);
        if (snippetFeature) {
          featureIdForBackend = snippetFeature.id;
          operationType = `Snippet: ${snippetFeature.name}`;
          contextDataForBackend['selected_text'] = editorSelectionText; // Key for snippet features
          // Add other context from snippetFeature.required_context if needed (similar to old logic)
          if (snippetFeature.required_context) {
            snippetFeature.required_context.forEach(key => {
              if (key !== 'selected_text') { // selected_text is already primary
                 // Placeholder for other context keys if snippet needs them
                console.log(`Snippet feature '${snippetFeature.name}' also requires '${key}'. This needs to be fetched/passed.`);
                contextDataForBackend[key] = `{${key}_placeholder_for_snippet}`;
              }
            });
          }
        } else {
          // Selected snippet feature ID is invalid, treat as full generation
          setSelectedSnippetFeatureId(""); // Reset invalid selection
        }
      }

      // If not a snippet operation (or invalid snippet selected), it's a full generation
      if (!featureIdForBackend) { // This means it's a full section generation
        operationType = "Full Section Generation (Type-driven)";
        // For full section generation, feature_id is undefined.
        // Backend will determine master feature based on section.type.
        // editorSelectionText (full editor content if nothing was selected) can be passed in context_data.
        if (editorSelectionText && !isTextActuallySelected) { // Full content available, no specific selection
          contextDataForBackend['user_instructions'] = editorSelectionText;
        }
      }

      const regeneratePayload: SectionRegeneratePayload = {
        new_prompt: editorSelectionText, // Main text input (selected for snippet, full for potential user_instructions)
        new_title: section.title || undefined,
        section_type: section.type || undefined,
        model_id_with_prefix: undefined, // Backend handles default
        feature_id: featureIdForBackend,
        context_data: contextDataForBackend,
      };

      console.log(`Regenerate Payload for ${operationType}:`, regeneratePayload);

      const updatedSection = await campaignService.regenerateCampaignSection(Number(campaignId), section.id, regeneratePayload);
      const generatedText = updatedSection.content;

      if (quillInstance) {
        if (isTextActuallySelected && featureIdForBackend && currentSelection) {
          // Snippet operation: replace only selected text
          quillInstance.deleteText(currentSelection.index, currentSelection.length, 'user');
          quillInstance.insertText(currentSelection.index, generatedText, 'user');
          quillInstance.setSelection(currentSelection.index + generatedText.length, 0, 'user');
        } else {
          // Full generation: replace all content
          const delta = quillInstance.clipboard.convert(generatedText);
          quillInstance.setContents(delta, 'user');
        }
        setEditedContent(quillInstance.root.innerHTML);
        onSectionUpdated(updatedSection);
      } else {
        setEditedContent(generatedText);
        onSectionUpdated(updatedSection);
      }

    } catch (error) {
      console.error("Failed to generate content:", error);
      // Ensure error is an instance of Error before accessing message
      if (error instanceof Error) {
        setContentGenerationError(`Failed to generate content: ${error.message}`);
      } else {
        setContentGenerationError('Failed to generate content. An unknown error occurred.');
      }
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
      const quillHtml = quillInstance.root.innerHTML;
      const plainTextContent = convertQuillHtmlToPlainText(quillHtml);
      await onSave(section.id, { content: plainTextContent }); // Removed images: imageData
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

  // const handleRegenerateClick = async () => { // Removed
  //   if (!campaignId || !section?.id) {
  //     setRegenerateError("Missing campaign or section ID for regeneration.");
  //     return;
  //   }
  //   setIsRegenerating(true);
  //   setRegenerateError(null);
  //   try {
  //     // Using an empty payload for now, as per plan
  //     const updatedSection = await campaignService.regenerateCampaignSection(campaignId, section.id, {});
  //     onSectionUpdated(updatedSection); // Notify parent of the update
  //     // Update local state as well, e.g., editedContent if it was based on section.content
  //     setEditedContent(updatedSection.content || '');
  //     // If title can be regenerated and shown in this component directly:
  //     // setSectionTitle(updatedSection.title); // Assuming you add local state for title if it's editable here
  //   } catch (error: any) {
  //     console.error("Failed to regenerate section:", error);
  //     setRegenerateError(error.message || 'An unexpected error occurred during regeneration.');
  //   } finally {
  //     setIsRegenerating(false);
  //   }
  // };

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
              <select
                id={`section-type-${section.id}`}
                value={section.type || 'Generic'} // Default to 'Generic' if type is undefined
                onChange={(e) => onSectionTypeUpdate(section.id, e.target.value)}
                title="Defines the category of the section. This helps in organizing and can assist AI content generation."
                style={{
                  flexGrow: 1,
                  padding: '6px 10px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '0.9em',
                  height: '38px', // Match feature dropdown height
                  boxSizing: 'border-box',
                }}
              >
                {['NPC', 'Character', 'Location', 'Item', 'Quest', 'Monster', 'Chapter', 'Note', 'World Detail', 'Generic'].map(typeOption => (
                  <option key={typeOption} value={typeOption}>
                    {typeOption}
                  </option>
                ))}
              </select>
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
              <Typography variant="caption" display="block" sx={{ mt: 1, color: 'text.secondary' }}>
                Tip: For a horizontal line, use three dashes (`---`) on a line by themselves, surrounded by blank lines.
              </Typography>

              {/* Toggle Button for RandomTableRoller */}
              <Button
                onClick={() => setIsTableRollerVisible(!isTableRollerVisible)}
                variant="outline-secondary"
                size="sm"
                style={{ marginTop: '10px', marginBottom: '5px' }}
              >
                {isTableRollerVisible ? 'Hide Random Tables' : 'Show Random Tables'}
              </Button>

              {/* Conditionally Rendered Random Table Roller Integration */}
              {isTableRollerVisible && (
                <RandomTableRoller onInsertItem={handleInsertRandomItem} />
              )}
              
              <div className="editor-actions">
                <Button onClick={handleSave} className="editor-button" disabled={isSaving || isGeneratingContent}>
                  {isSaving ? 'Saving...' : 'Save Content'}
                </Button>

                {/* Snippet Feature Selector - Shown only when text is selected */}
                {isEditing && currentSelection && currentSelection.length > 0 && snippetFeatures.length > 0 && (
                  <div className="snippet-feature-selector-group" style={{ marginRight: '10px', display: 'inline-block', verticalAlign: 'middle' }}>
                    <select
                      value={selectedSnippetFeatureId}
                      onChange={(e) => setSelectedSnippetFeatureId(e.target.value)}
                      disabled={isGeneratingContent || isSaving}
                      style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #ccc', height: '38px', boxSizing: 'border-box' }}
                      title={snippetFeatureFetchError ? "Error loading snippet features" : "Select a snippet feature to apply to highlighted text"}
                    >
                      <option value="">-- Apply Snippet Feature --</option>
                      {snippetFeatures.map(feature => (
                        <option key={feature.id} value={feature.id.toString()}>
                          {feature.name}
                        </option>
                      ))}
                    </select>
                    {snippetFeatureFetchError && <p className="error-message" style={{fontSize: '0.8em', color: 'red', marginTop: '2px'}}>{snippetFeatureFetchError}</p>}
                     { selectedSnippetFeatureId && snippetFeatures.find(f => f.id.toString() === selectedSnippetFeatureId)?.required_context &&
                       snippetFeatures.find(f => f.id.toString() === selectedSnippetFeatureId)!.required_context!.filter(rc => rc !== 'selected_text').length > 0 && (
                      <Typography variant="caption" display="block" sx={{ mt: 0.5, color: 'text.secondary', fontSize: '0.75rem' }}>
                        Also uses: {snippetFeatures.find(f => f.id.toString() === selectedSnippetFeatureId)!.required_context!.filter(rc => rc !== 'selected_text').join(', ')}
                      </Typography>
                    )}
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
                {/* Regenerate button hidden as per requirements
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
                */}
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
              {/* regenerateError display removed as state and handler are removed */}
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
            console.error("Quill instance not available for inserting image Markdown.");
            // Fallback: Append Markdown to text state if no Quill instance
            const markdownImage = `\n![${promptUsed || 'Generated Image'}](${imageUrl})\n`;
            setEditedContent(prev => prev + markdownImage);
            setIsImageGenerationModalOpen(false);
            return;
          }

          const range = quillInstance.getSelection(true) || { index: quillInstance.getLength() -1, length: 0 };
          let safeIndex = range.index;
          // Adjust safeIndex if editor is empty or Quill reports length 1 for initial newline
          if (quillInstance.getLength() === 1 && safeIndex > 0) {
             safeIndex = 0;
          } else if (safeIndex < 0) { // Should not happen, but as a safeguard
             safeIndex = 0;
          }

          const markdownImage = `\n![${promptUsed || 'Generated Image'}](${imageUrl})\n`;
          quillInstance.insertText(safeIndex, markdownImage, 'user');
          // Move cursor to the end of the inserted markdown image
          quillInstance.setSelection(safeIndex + markdownImage.length, 0, 'user');
          setEditedContent(quillInstance.root.innerHTML); // Update content to reflect new Markdown

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

// New utility function to convert Quill HTML to plain text
// Exported for testing
export const convertQuillHtmlToPlainText = (htmlString: string): string => {
  if (!htmlString) {
    return '';
  }

  let text = htmlString;

  // Replace <br> tags with \n
  text = text.replace(/<br\s*\/?>/gi, '\n');

  // Replace closing </p> tags with \n
  text = text.replace(/<\/p>/gi, '\n');

  // Strip all remaining HTML tags
  text = text.replace(/<[^>]*>/g, '');

  // Normalize newlines: sequences of 3 or more newlines with two newlines
  text = text.replace(/\n{3,}/g, '\n\n');

  // Trim leading and trailing newlines from the entire text
  text = text.trim();

  // Add a single newline at the end if the content is not empty
  if (text) {
    text += '\n';
  }

  return text;
};

export default CampaignSectionView;
