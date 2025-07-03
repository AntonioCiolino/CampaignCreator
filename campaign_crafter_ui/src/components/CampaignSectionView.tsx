import React, { useState, useEffect, useRef } from 'react'; // Added useRef
import ReactDOM from 'react-dom'; // Added ReactDOM for createPortal
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
import { IconButton } from '@mui/material'; // Import IconButton
import EditIcon from '@mui/icons-material/Edit'; // Import EditIcon
import SaveIcon from '@mui/icons-material/Save'; // Import SaveIcon
import CancelIcon from '@mui/icons-material/Cancel'; // Import CancelIcon
import './CampaignSectionView.css';
import { CampaignSectionUpdatePayload, SectionRegeneratePayload } from '../types/campaignTypes'; // CORRECTED PATH, Added SectionRegeneratePayload
import { getFeatures } from '../services/featureService';
import { Feature } from '../types/featureTypes';
import { Character as FrontendCharacter } from '../types/characterTypes'; // Corrected path
import * as campaignService from '../services/campaignService';
import SnippetContextModal from './modals/SnippetContextModal'; // Import the new modal

const SECTION_TYPES = ['NPC', 'Character', 'Location', 'Item', 'Quest', 'Monster', 'Chapter', 'Note', 'World Detail', 'Generic'];

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
  selectedLLMId: string | null; // Add selectedLLMId
  // Prop for updating section type
  onSectionTypeUpdate?: (sectionId: number, newType: string) => void; // Optional for now
  onSetThematicImageFromSection?: (imageUrl: string, promptUsed: string) => void;
  expandSectionId: string | null; // Add this
  campaignCharacters: FrontendCharacter[]; // Added for context modal
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
  selectedLLMId, // Destructure selectedLLMId
  onSectionTypeUpdate, // Destructure the new prop
  onSetThematicImageFromSection,
  expandSectionId, // Add this
  campaignCharacters, // Destructure new prop
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
  const [isEditing, setIsEditing] = useState<boolean>(false); // For content editing
  const [editedContent, setEditedContent] = useState<string>(section.content || '');
  const [isEditingTitle, setIsEditingTitle] = useState<boolean>(false); // For title editing
  const [editedTitle, setEditedTitle] = useState<string>(section.title || '');
  const [quillInstance, setQuillInstance] = useState<any>(null); // Enabled to store Quill instance
  const [localSaveError, setLocalSaveError] = useState<string | null>(null); // General save error for the section
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [isImageGenerationModalOpen, setIsImageGenerationModalOpen] = useState<boolean>(false);
  const [isGeneratingContent, setIsGeneratingContent] = useState<boolean>(false);
  const [contentGenerationError, setContentGenerationError] = useState<string | null>(null);
  const [snippetFeatures, setSnippetFeatures] = useState<Feature[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [selectedSnippetFeatureId, setSelectedSnippetFeatureId] = useState<string>(""); // This will be set by the context menu
  const [snippetFeatureFetchError, setSnippetFeatureFetchError] = useState<string | null>(null);
  const [isSnippetContextMenuOpen, setIsSnippetContextMenuOpen] = useState<boolean>(false);
  const [contextMenuPosition, setContextMenuPosition] = useState<{ x: number, y: number } | null>(null);

  // State for the new SnippetContextModal
  const [isContextModalOpen, setIsContextModalOpen] = useState<boolean>(false);
  const [currentFeatureForModal, setCurrentFeatureForModal] = useState<Feature | null>(null);
  const [currentSelectionForModal, setCurrentSelectionForModal] = useState<QuillRange | null>(null);


  // const [isRegenerating, setIsRegenerating] = useState<boolean>(false); // Removed
  // const [regenerateError, setRegenerateError] = useState<string | null>(null); // Removed

  // Filter features will be handled by the context menu logic later
  // const filteredFeatures = React.useMemo(() => { ... });

  // Effect to reset selectedFeatureId will be handled by context menu logic
  // useEffect(() => { ... });

  const [currentSelection, setCurrentSelection] = useState<QuillRange | null>(null); // This will store the selection range
  const snippetContextMenuRef = useRef<HTMLDivElement>(null); // Ref for the context menu div
  const contextMenuTriggerSelectionRef = useRef<QuillRange | null>(null); // Ref to store selection at menu trigger

  // Effect for Quill selection changes (just to update currentSelection state)
  useEffect(() => {
    if (isEditing && quillInstance) {
      const selectionChangeHandler = (range: QuillRange, oldRange: QuillRange, source: string) => {
        if (source === 'user') {
          // setCurrentSelection(range); // We will use the ref for the action, this can still be useful for other UI if needed
          // Don't open menu here anymore, only update selection state
          if (!range || range.length === 0) {
            // If selection is lost, and menu is open, close it.
            // Also clear the ref if selection is lost and menu was tied to it.
            // This might need careful handling if menu should persist.
            // For now, let's assume losing selection should close the menu.
            setIsSnippetContextMenuOpen(false);
            contextMenuTriggerSelectionRef.current = null;
          }
        }
      };
      quillInstance.on('selection-change', selectionChangeHandler);
      return () => {
        quillInstance.off('selection-change', selectionChangeHandler);
      };
    }
  }, [isEditing, quillInstance]);

  // Effect for handling contextmenu event on the editor
  useEffect(() => {
    if (isEditing && quillInstance && quillInstance.root) { // quillInstance.root is the editor container
      const editorNode = quillInstance.root;
      const handleContextMenu = (event: MouseEvent) => {
        event.preventDefault();
        console.log('[CampaignSectionView] contextmenu event triggered');
        const selection = quillInstance.getSelection();
        if (selection && selection.length > 0) {
          // Store the selection in the ref *when the context menu is triggered*
          contextMenuTriggerSelectionRef.current = selection;
          console.log('[CampaignSectionView] Stored selection in ref:', selection);

          const posX = event.clientX + 10; // Offset 10px to the right of the click
          const posY = event.clientY + 5;  // Offset 5px down from the click
          console.log('[CampaignSectionView] Text selected, opening context menu at viewport X:', event.clientX, 'Y:', event.clientY, 'Menu Pos X:', posX, 'Y:', posY);
          setContextMenuPosition({ x: posX, y: posY });
          setIsSnippetContextMenuOpen(true);
        } else {
          console.log('[CampaignSectionView] No text selected on right-click, not opening menu.');
          contextMenuTriggerSelectionRef.current = null; // Clear ref if no selection
          setIsSnippetContextMenuOpen(false);
        }
      };
      editorNode.addEventListener('contextmenu', handleContextMenu);
      return () => {
        editorNode.removeEventListener('contextmenu', handleContextMenu);
      };
    } else {
      setIsSnippetContextMenuOpen(false); // Ensure menu is closed if not editing or quill not ready
    }
  }, [isEditing, quillInstance]);

  // Effect for handling "click outside" to close the context menu
  useEffect(() => {
    if (!isSnippetContextMenuOpen) return;

    // Handler for clicks outside the menu
    // function handleClickOutside(event: MouseEvent) { // Temporarily disable this
    //   if (snippetContextMenuRef.current && !snippetContextMenuRef.current.contains(event.target as Node)) {
    //     console.log('[CampaignSectionView] Clicked outside context menu (document listener), closing.');
    //     setIsSnippetContextMenuOpen(false);
    //   }
    // }

    // document.addEventListener('mousedown', handleClickOutside); // Temporarily disable this

    return () => {
      // document.removeEventListener('mousedown', handleClickOutside); // Temporarily disable this
    };
  }, [isSnippetContextMenuOpen]);


  useEffect(() => {
    if (isEditing) { // Load snippet features when editing starts
      const loadSnippetFeatures = async () => {
        try {
          console.log('[CampaignSectionView] loadSnippetFeatures - Attempting to fetch features.');
          setSnippetFeatureFetchError(null);
          const allFeatures = await getFeatures();
          console.log('[CampaignSectionView] loadSnippetFeatures - allFeatures fetched:', allFeatures);
          const filteredForSnippets = allFeatures.filter(
            f => f.feature_category === 'Snippet' || (!f.feature_category && f.name !== 'Campaign' && f.name !== 'TOC Homebrewery' && f.name !== 'TOC Display' && f.name !== 'Campaign Names') // crude fallback for older features
          );
          console.log('[CampaignSectionView] loadSnippetFeatures - filteredForSnippets:', filteredForSnippets);
          setSnippetFeatures(filteredForSnippets);
        } catch (error) {
          console.error("[CampaignSectionView] Failed to load snippet features:", error);
          setSnippetFeatureFetchError(error instanceof Error ? error.message : "An unknown error occurred while fetching snippet features.");
        }
      };
      loadSnippetFeatures();
    } else {
      setSnippetFeatures([]); // Clear when not editing
      // setSelectedSnippetFeatureId(""); // Commented out as selectedSnippetFeatureId is not used
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

  // Effect to update editedTitle if section.title prop changes from parent
  useEffect(() => {
    if (!isEditingTitle) { // Only update if not currently editing, to avoid overwriting user input
      setEditedTitle(section.title || '');
    }
  }, [section.title, isEditingTitle]);

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

  const handleModalSubmit = (collectedContextData: Record<string, any>) => {
    if (currentFeatureForModal && currentSelectionForModal) {
      console.log('[CampaignSectionView] Submitting from modal. Feature:', currentFeatureForModal.name, 'Selection:', currentSelectionForModal, 'CollectedContext:', collectedContextData);
      // Call handleGenerateContent, passing the feature ID, selection, and new collected context
      handleGenerateContent(currentFeatureForModal.id.toString(), currentSelectionForModal, collectedContextData);
    } else {
      console.error('[CampaignSectionView] Modal submit called without current feature or selection for modal.');
    }
    // Reset modal state
    setIsContextModalOpen(false);
    setCurrentFeatureForModal(null);
    setCurrentSelectionForModal(null);
  };

  const handleGenerateContent = async (
    overrideSnippetFeatureId?: string,
    explicitSelectionRange?: QuillRange | null,
    collectedContextData?: Record<string, any> | null // New optional parameter for context from modal
  ) => {
    // Log raw parameters
    console.log('[HGC] Raw params - overrideSnippetFeatureId:', overrideSnippetFeatureId, 'explicitSelectionRange:', explicitSelectionRange, 'collectedContextData:', collectedContextData);

    console.log('[HGC] Start. overrideSnippetFeatureId:', overrideSnippetFeatureId, 'explicitSelectionRange:', explicitSelectionRange, 'collectedContextData:', collectedContextData); // Updated log
    setIsGeneratingContent(true);
    setContentGenerationError(null);

    const featureIdToUseForSnippet = overrideSnippetFeatureId;
    console.log('[HGC] featureIdToUseForSnippet (from override):', featureIdToUseForSnippet);

    try {
      let editorSelectionText = '';
      let isTextActuallySelected = false;
      let selectionToReplace: { index: number, length: number } | null = null;

      // Logic for determining editorSelectionText, isTextActuallySelected, and selectionToReplace
      if (featureIdToUseForSnippet) {
        // If an explicit selection is passed (from context menu action), prioritize it
        if (quillInstance && explicitSelectionRange && explicitSelectionRange.length > 0) {
          console.log('[HGC] Using explicitSelectionRange for snippet:', explicitSelectionRange);
          editorSelectionText = quillInstance.getText(explicitSelectionRange.index, explicitSelectionRange.length);
          isTextActuallySelected = true;
          selectionToReplace = { index: explicitSelectionRange.index, length: explicitSelectionRange.length };
        } else {
          // Fallback for safety, though ideally explicitSelectionRange should always be valid if provided for a snippet
          // Or this path could be hit if explicitSelectionRange was somehow invalid (e.g. length 0)
          console.log('[HGC] ExplicitSelectionRange not valid or not provided for snippet. Falling back to contextMenuTriggerSelectionRef or full generation.');
          const storedSelection = contextMenuTriggerSelectionRef.current;
          if (quillInstance && storedSelection && storedSelection.length > 0) {
            console.log('[HGC] Using storedSelection (contextMenuTriggerSelectionRef) for snippet:', storedSelection);
            editorSelectionText = quillInstance.getText(storedSelection.index, storedSelection.length);
            isTextActuallySelected = true;
            selectionToReplace = { index: storedSelection.index, length: storedSelection.length };
          } else {
            // Not a valid snippet call if no selection from ref either, treat as full generation
            console.log('[HGC] No valid selection for snippet (explicit or stored). Treating as full generation.');
            isTextActuallySelected = false;
            if (quillInstance) editorSelectionText = quillInstance.getText().substring(0,2000);
            else editorSelectionText = editedContent.substring(0,2000);
          }
        }
      } else { // Not a snippet call (e.g., "Generate Content" button clicked directly)
        console.log('[HGC] Not a snippet call. Checking current editor selection for user_instructions or full content.');
        if (quillInstance) {
          const currentQuillSel = quillInstance.getSelection();
          if (currentQuillSel && currentQuillSel.length > 0) {
            editorSelectionText = quillInstance.getText(currentQuillSel.index, currentQuillSel.length);
            isTextActuallySelected = true; // This text will become user_instructions for full generation
            console.log('[HGC] Using current editor selection for full generation user_instructions.');
          } else {
            // No text selected, use full content for context (or as prompt if user_instructions is empty)
            editorSelectionText = quillInstance.getText().substring(0, 2000);
            isTextActuallySelected = false;
            console.log('[HGC] No editor selection for full generation, using existing content as context.');
          }
        } else {
          // Fallback if quillInstance is somehow not available
          editorSelectionText = editedContent.substring(0, 2000);
          isTextActuallySelected = false;
          console.log('[HGC] Quill instance not available, using editedContent for full generation context.');
        }
      }
      // Log after all evaluations for editorSelectionText and isTextActuallySelected
      console.log('[HGC] After selection processing - featureIdToUseForSnippet:', featureIdToUseForSnippet, 'isTextActuallySelected:', isTextActuallySelected, 'selectionToReplace:', selectionToReplace, 'editorSelectionText:', editorSelectionText ? editorSelectionText.substring(0,30) + '...' : "N/A");


      if (!section.id) {
        setContentGenerationError("Section ID is missing. Cannot generate content.");
        setIsGeneratingContent(false);
        return;
      }

      let featureIdForBackend: number | undefined = undefined;
      let contextDataForBackend: { [key: string]: any } = {};
      let operationType = "Full Section Generation";
      // selectionToReplace is already set if it's a snippet operation with valid ref selection

      // This block determines if it's a snippet for payload:
      if (featureIdToUseForSnippet && isTextActuallySelected) {
        console.log('[HGC] Looking for snippetFeature with ID:', featureIdToUseForSnippet, 'Available snippetFeatures:', snippetFeatures.map(f => f.id.toString()));
        const snippetFeature = snippetFeatures.find(f => f.id.toString() === featureIdToUseForSnippet);
        console.log('[HGC] Attempting snippet path. Found snippetFeature:', snippetFeature);

        if (snippetFeature) {
          featureIdForBackend = snippetFeature.id;
          operationType = `Snippet: ${snippetFeature.name}`;

          // Always add selected_text
          contextDataForBackend['selected_text'] = editorSelectionText;
          console.log('[HGC] Added selected_text to contextDataForBackend.');

          // Automatically add campaign_characters if required by the feature
          if (snippetFeature.required_context?.includes('campaign_characters')) {
            if (campaignCharacters && campaignCharacters.length > 0) {
              contextDataForBackend['campaign_characters'] = campaignCharacters.map(char => char.name).join(', ');
              console.log('[HGC] Automatically added campaign_characters to contextDataForBackend:', contextDataForBackend['campaign_characters']);
            } else {
              contextDataForBackend['campaign_characters'] = "No specific campaign characters provided.";
              console.log('[HGC] No campaign characters to automatically add; added fallback message.');
            }
          }

          // Merge context collected from modal (for other keys)
          if (collectedContextData) {
            console.log('[HGC] Merging collectedContextData from modal:', collectedContextData);
            for (const key in collectedContextData) {
              if (Object.prototype.hasOwnProperty.call(collectedContextData, key) && key !== 'selected_text' && key !== 'campaign_characters') {
                // Ensure not to overwrite already handled contexts like selected_text or campaign_characters if modal also sent them
                contextDataForBackend[key] = collectedContextData[key];
              }
            }
          }

          // Placeholder for any other required context not provided (should be rare now)
          snippetFeature.required_context?.forEach(key => {
            if (!contextDataForBackend[key]) {
              console.warn(`[HGC] Snippet feature '${snippetFeature.name}' still requires '${key}', but not found in any context source. Using placeholder.`);
              contextDataForBackend[key] = `{${key}_placeholder_for_snippet_very_fallback}`;
            }
          });

        } else {
          console.warn(`[HGC] Snippet feature ID ${featureIdToUseForSnippet} not found in snippetFeatures. Proceeding as full generation.`);
          featureIdForBackend = undefined;
        }
      }

      // Fallback to full section generation if not a snippet or snippet processing failed
      if (!featureIdForBackend) {
        operationType = "Full Section Generation (Type-driven)";
        console.log('[HGC] Not a snippet operation or feature not found/processed correctly, proceeding as Full Section Generation.');
        if (editorSelectionText && Object.keys(contextDataForBackend).length === 0) { // Only add as user_instructions if no other context was built
          contextDataForBackend['user_instructions'] = editorSelectionText;
          console.log('[HGC] Added editor text as user_instructions for full generation.');
        }
      }

      const finalPromptForPayload = featureIdForBackend ? undefined : editorSelectionText;

      console.log('[HGC] Final featureIdForBackend:', featureIdForBackend);
      console.log('[HGC] Final contextDataForBackend:', contextDataForBackend);

      const regeneratePayload: SectionRegeneratePayload = {
        new_prompt: finalPromptForPayload,
        new_title: section.title || undefined,
        section_type: section.type || undefined,
        model_id_with_prefix: selectedLLMId || undefined,
        feature_id: featureIdForBackend,
        context_data: contextDataForBackend,
      };

      console.log(`[HGC] Regenerate Payload for ${operationType}:`, regeneratePayload);

      const updatedSection = await campaignService.regenerateCampaignSection(Number(campaignId), section.id, regeneratePayload);
      const generatedText = updatedSection.content;

      if (quillInstance) {
        console.log('[HGC] Decision point for replacement: selectionToReplace:', selectionToReplace, 'featureIdForBackend:', featureIdForBackend);
        if (selectionToReplace && featureIdForBackend) { // Use captured selection for snippet operation
          // Snippet operation: replace only selected text
          console.log('[HGC] Performing partial replacement.');
          quillInstance.deleteText(selectionToReplace.index, selectionToReplace.length, 'user');
          quillInstance.insertText(selectionToReplace.index, generatedText, 'user');
          quillInstance.setSelection(selectionToReplace.index + generatedText.length, 0, 'user');
        } else {
          // Full generation: replace all content
          console.log('[HGC] Performing full replacement because selectionToReplace is', selectionToReplace, 'and featureIdForBackend is', featureIdForBackend);
          const delta = quillInstance.clipboard.convert(generatedText);
          quillInstance.setContents(delta, 'user');
        }
        setEditedContent(quillInstance.root.innerHTML);
        // Ensure the parent gets the full updated content, not just the snippet from updatedSection.content
        const fullContentPlainText = convertQuillHtmlToPlainText(quillInstance.root.innerHTML);
        const sectionWithFullContent: CampaignSection = {
          ...updatedSection,
          content: fullContentPlainText,
        };
        onSectionUpdated(sectionWithFullContent);
      } else {
        // This case should ideally not be hit if Quill is always available during editing
        setEditedContent(generatedText);
        onSectionUpdated(updatedSection); // Here, updatedSection.content is just the snippet
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

  console.log('[CampaignSectionView] Render state - isEditing:', isEditing, 'isSnippetContextMenuOpen:', isSnippetContextMenuOpen, 'contextMenuPosition:', contextMenuPosition, 'snippetFeatures.length:', snippetFeatures.length, 'currentSelection:', currentSelection);

  const handleSaveTitle = async () => {
    if (editedTitle.trim() === '') {
      setLocalSaveError('Title cannot be empty.');
      return;
    }
    setLocalSaveError(null);
    setSaveSuccess(false);
    try {
      await onSave(section.id, { title: editedTitle });
      setIsEditingTitle(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error("Failed to save section title:", error);
      setLocalSaveError('Failed to save title. Please try again.');
    }
  };

  const handleCancelEditTitle = () => {
    setEditedTitle(section.title || '');
    setIsEditingTitle(false);
    setLocalSaveError(null);
  };

  return (
    <div id={`section-container-${section.id}`} className="campaign-section-view" tabIndex={-1}>
      <div className="section-title-header">
        {isEditingTitle ? (
          <div className="title-edit-container">
            <input
              type="text"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              className="title-edit-input"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSaveTitle();
                if (e.key === 'Escape') handleCancelEditTitle();
              }}
            />
            <Button onClick={handleSaveTitle} size="sm" className="title-edit-button" disabled={isSaving}>
              <SaveIcon fontSize="small" />
            </Button>
            <Button onClick={handleCancelEditTitle} size="sm" variant="secondary" className="title-edit-button">
              <CancelIcon fontSize="small" />
            </Button>
          </div>
        ) : (
          <div className="title-display-container" onClick={() => !isEditing && setIsCollapsed(!isCollapsed)} style={{ cursor: isEditing ? 'default' : 'pointer', display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            <h3 className="section-title" style={{ marginRight: '10px' }}>
              {isCollapsed ? '▶' : '▼'} {section.title || 'Untitled Section'}
            </h3>
            {!isEditing && ( // Only show edit icon if not editing content
              <IconButton onClick={(e: React.MouseEvent) => { e.stopPropagation(); setIsEditingTitle(true); }} size="small" className="edit-title-icon" title="Edit title">
                <EditIcon fontSize="small" />
              </IconButton>
            )}
          </div>
        )}
        {/* Display Section Type if not editing title or content */}
        {!isEditingTitle && !isEditing && section.type && (
          <span style={{ marginLeft: '10px', fontSize: '0.8em', color: '#666', fontStyle: 'italic' }}>
            ({section.type})
          </span>
        )}
      </div>

      {!isCollapsed && (
        <>
          {/* Section Type Input - Placed here for better visibility and context */}
          {onSectionTypeUpdate && ( // Only show if handler is provided
            <div style={{ padding: '5px 10px', display: 'flex', alignItems: 'center', backgroundColor: '#f9f9f9' }}>
              <label htmlFor={`section-type-${section.id}`} style={{ marginRight: '8px', fontSize: '0.9em', fontWeight: 'bold' }}>Type:</label>
              <select
                id={`section-type-${section.id}`}
                value={SECTION_TYPES.find(st => st.toLowerCase() === section.type?.toLowerCase()) || 'Generic'}
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
                {SECTION_TYPES.map(typeOption => (
                  <option key={typeOption} value={typeOption}>
                    {typeOption}
                  </option>
                ))}
              </select>
            </div>
          )}

          {isEditing ? (
            <div className="section-editor" title={getTooltipText(section.type)} style={{ position: 'relative' }}> {/* Added position: relative for context menu positioning */}
              <ReactQuill
                theme="snow"
                value={editedContent}
                onChange={setEditedContent}
                modules={quillModules}
                formats={quillFormats}
                className="quill-editor"
                ref={setQuillRef} // Set the ref to get Quill instance
              />
              {isSnippetContextMenuOpen && contextMenuPosition && snippetFeatures.length > 0 && ReactDOM.createPortal(
                // Restored Portal
                (() => {
                  console.log("[CampaignSectionView] Rendering Snippet Context Menu via Portal with position:", contextMenuPosition, "and features:", snippetFeatures.length);
                  return (
                    <div
                      ref={snippetContextMenuRef}
                      className="snippet-context-menu"
                      style={{
                        position: 'fixed',
                        left: `${contextMenuPosition.x}px`,
                        top: `${contextMenuPosition.y}px`,
                        zIndex: 1050,
                      }}
                    >
                      {snippetFeatureFetchError && <p className="error-message" style={{fontSize: '0.8em', color: 'red', margin: '0 0 5px 0'}}>{snippetFeatureFetchError}</p>}
                      <ul style={{ listStyleType: 'none', margin: 0, padding: 0 }}>
                        {snippetFeatures.map(feature => (
                          <li
                            key={feature.id}
                            data-feature-id={feature.id.toString()}
                            style={{ padding: '5px 10px', cursor: 'pointer' }}
                            onMouseDown={async (event) => {
                              console.log("[CampaignSectionView] Snippet item onMouseDown triggered for feature:", feature.name);
                              event.stopPropagation();
                              event.preventDefault();

                              const quill = quillInstance;
                              // Use contextMenuTriggerSelectionRef.current which is set reliably on contextmenu event
                              const selectionToUse = contextMenuTriggerSelectionRef.current;

                              console.log("[CampaignSectionView] MouseDown: quillInstance exists?", !!quill);
                              console.log("[CampaignSectionView] MouseDown: selection from ref:", selectionToUse);
                              if (selectionToUse) {
                                  console.log("[CampaignSectionView] MouseDown: selection from ref length:", selectionToUse.length);
                              }

                              if (quill && selectionToUse && selectionToUse.length > 0) {
                                // const text = quill.getText(selectionToUse.index, selectionToUse.length); // Unused
                                // const rangeToProcess = { index: selectionToUse.index, length: selectionToUse.length }; // Unused
                                setIsSnippetContextMenuOpen(false); // Close context menu

                                // Determine if there are required context keys other than 'selected_text' and 'campaign_characters'
                                const otherRequiredKeys = feature.required_context?.filter(
                                  key => key !== 'selected_text' && key !== 'campaign_characters'
                                ) || [];

                                if (otherRequiredKeys.length > 0) {
                                  console.log(`[CampaignSectionView] Feature '${feature.name}' requires additional user input for: ${otherRequiredKeys.join(', ')}. Opening modal.`);
                                  setCurrentFeatureForModal(feature); // Pass the full feature
                                  setCurrentSelectionForModal(selectionToUse);
                                  setIsContextModalOpen(true);
                                } else {
                                  // No other keys, or only 'selected_text'/'campaign_characters' which are handled automatically
                                  console.log(`[CampaignSectionView] Feature '${feature.name}' requires no additional user input beyond auto-handled context. Calling HGC directly.`);
                                  // Prepare an empty object for collectedContextData if no modal needed,
                                  // campaign_characters will be added in handleGenerateContent if required by the feature.
                                  await handleGenerateContent(feature.id.toString(), selectionToUse, {});
                                }
                              } else {
                                console.warn("[CampaignSectionView] Snippet item onMouseDown: No valid ref selection or Quill. Quill:", quill, "RefSelection:", selectionToUse);
                                setIsSnippetContextMenuOpen(false); // Ensure context menu is closed
                              }
                            }}
                            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f0f0f0')}
                            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'white')}
                          >
                            {feature.name}
                            {feature.required_context && feature.required_context.filter(rc => rc !== 'selected_text').length > 0 && (
                              <span style={{fontSize: '0.7em', color: '#777', marginLeft: '5px'}}>
                                (+ {feature.required_context.filter(rc => rc !== 'selected_text').join(', ')})
                              </span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })(),
              document.body // Restored Portal target
              )}
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

                {/* Snippet Feature Dropdown removed from here. Context menu will replace it. */}

                <Button
                  onClick={() => handleGenerateContent()} // Changed to call without event arg
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
      <SnippetContextModal
        isOpen={isContextModalOpen}
        onClose={() => {
          setIsContextModalOpen(false);
          setCurrentFeatureForModal(null);
          setCurrentSelectionForModal(null);
        }}
        onSubmit={handleModalSubmit}
        feature={currentFeatureForModal}
        campaignCharacters={campaignCharacters}
        selectedText={currentSelectionForModal && quillInstance ? quillInstance.getText(currentSelectionForModal.index, currentSelectionForModal.length) : ''}
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
