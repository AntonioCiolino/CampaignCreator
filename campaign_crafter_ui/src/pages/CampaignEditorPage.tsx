import React, { useState, useEffect, FormEvent, useMemo, useRef } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import LoadingSpinner from '../components/common/LoadingSpinner';
import LLMSelectionDialog from '../components/modals/LLMSelectionDialog';
import ImageGenerationModal from '../components/modals/ImageGenerationModal/ImageGenerationModal';
import SuggestedTitlesModal from '../components/modals/SuggestedTitlesModal';
import * as campaignService from '../services/campaignService';
import { CampaignSection, SeedSectionsProgressEvent, SeedSectionsCallbacks } from '../services/campaignService'; // Added CampaignSection, SeedSectionsProgressEvent, SeedSectionsCallbacks
import { getAvailableLLMs, LLMModel } from '../services/llmService';
// CampaignSectionView will be used by CampaignSectionEditor
// import CampaignSectionView from '../components/CampaignSectionView'; 
import ReactMarkdown from 'react-markdown';
import './CampaignEditorPage.css';
import Button from '../components/common/Button'; // Ensure common Button is imported

// MUI Icons (attempt to import, will use text/emoji if fails)
// import SaveIcon from '@mui/icons-material/Save'; // Removed SaveIcon
// AddPhotoAlternateIcon, EditIcon, DeleteOutlineIcon are moved to CampaignDetailsEditor
import ListAltIcon from '@mui/icons-material/ListAlt';
import UnfoldLessIcon from '@mui/icons-material/UnfoldLess';
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import CancelIcon from '@mui/icons-material/Cancel';
import SettingsSuggestIcon from '@mui/icons-material/SettingsSuggest';
import PublishIcon from '@mui/icons-material/Publish';


// New Component Imports
import CampaignDetailsEditor from '../components/campaign_editor/CampaignDetailsEditor';
import CampaignLLMSettings from '../components/campaign_editor/CampaignLLMSettings';
import CampaignSectionEditor from '../components/campaign_editor/CampaignSectionEditor';
import { LLMModel as LLM } from '../services/llmService'; // Corrected LLM import
import Tabs, { TabItem } from '../components/common/Tabs'; // Import Tabs component
import { Typography } from '@mui/material'; // Removed Box, kept Typography
import DetailedProgressDisplay from '../components/common/DetailedProgressDisplay'; // Import the new component

const CampaignEditorPage: React.FC = () => {
  const { campaignId } = useParams<{ campaignId: string }>();
  const [campaign, setCampaign] = useState<campaignService.Campaign | null>(null);
  const [sections, setSections] = useState<campaignService.CampaignSection[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true); // For initial page load
  const [isPageLoading, setIsPageLoading] = useState<boolean>(false); // For subsequent actions
  const [error, setError] = useState<string | null>(null);

  // Editable campaign details
  const [editableTitle, setEditableTitle] = useState<string>('');
  const [editableInitialPrompt, setEditableInitialPrompt] = useState<string>('');
  // const [isSaving, setIsSaving] = useState<boolean>(false); // Removed
  const [saveError, setSaveError] = useState<string | null>(null); // Keep for handleSaveChanges
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null); // Keep for handleSaveChanges

  // Section-specific saving states removed as per plan
  // const [savingSectionId, setSavingSectionId] = useState<number | null>(null);
  // const [sectionSaveError, setSectionSaveError] = useState<{ [key: number]: string | null }>({});

  // LLM Generation states
  const [isGeneratingTOC, setIsGeneratingTOC] = useState<boolean>(false);
  const [tocError, setTocError] = useState<string | null>(null);
  const [isGeneratingTitles, setIsGeneratingTitles] = useState<boolean>(false);
  const [titlesError, setTitlesError] = useState<string | null>(null);
  const [suggestedTitles, setSuggestedTitles] = useState<string[] | null>(null);

  // Add New Section states
  const [newSectionTitle, setNewSectionTitle] = useState<string>('');
  const [newSectionPrompt, setNewSectionPrompt] = useState<string>('');
  const [isAddingSection, setIsAddingSection] = useState<boolean>(false);
  const [addSectionError, setAddSectionError] = useState<string | null>(null);
  const [addSectionSuccess, setAddSectionSuccess] = useState<string | null>(null);

  // LLM Settings State
  const [availableLLMs, setAvailableLLMs] = useState<LLMModel[]>([]); // Corrected type
  const [selectedLLMId, setSelectedLLMId] = useState<string>('');
  const [temperature, setTemperature] = useState<number>(0.7);

  // Export State
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [exportError, setExportError] = useState<string | null>(null);
  // Re-using saveSuccess for general positive feedback for simplicity

  // State for "Collapse All" / "Expand All" functionality
  const [forceCollapseAll, setForceCollapseAll] = useState<boolean | undefined>(undefined);

  // State for UI collapsible sections
  const [isTocCollapsed, setIsTocCollapsed] = useState<boolean>(false); // Default to expanded
  // const [isLLMSettingsCollapsed, setIsLLMSettingsCollapsed] = useState<boolean>(false); // Removed
  const [isAddSectionCollapsed, setIsAddSectionCollapsed] = useState<boolean>(true);
  const [isLLMDialogOpen, setIsLLMDialogOpen] = useState<boolean>(false);
  // isCampaignDetailsCollapsed will be managed by the new component or removed if not needed at page level
  const [isBadgeImageModalOpen, setIsBadgeImageModalOpen] = useState(false); // Added for modal
  const [isSuggestedTitlesModalOpen, setIsSuggestedTitlesModalOpen] = useState<boolean>(false);

  // Auto-save LLM settings state
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);
  const [isAutoSavingLLMSettings, setIsAutoSavingLLMSettings] = useState<boolean>(false);
  const [autoSaveLLMSettingsError, setAutoSaveLLMSettingsError] = useState<string | null>(null);
  const [autoSaveLLMSettingsSuccess, setAutoSaveLLMSettingsSuccess] = useState<string | null>(null);
  const initialLoadCompleteRef = useRef(false);

  // State for badge image updates
  // badgeUpdateLoading, setBadgeUpdateLoading, badgeUpdateError, setBadgeUpdateError will be managed by CampaignDetailsEditor (or passed to it)
  // For now, we keep them here if they are used by functions like handleBadgeImageGenerated that remain in this file.
  const [badgeUpdateLoading, setBadgeUpdateLoading] = useState(false);
  const [badgeUpdateError, setBadgeUpdateError] = useState<string | null>(null);

  // campaignBadgeImage and setCampaignBadgeImage for CampaignDetailsEditor
  // This state is initialized from `campaign.badge_image_url` in useEffect
  const [campaignBadgeImage, setCampaignBadgeImage] = useState<string>('');

  // State for "Approve TOC & Create Sections" button
  const [isSeedingSections, setIsSeedingSections] = useState<boolean>(false);
  const [seedSectionsError, setSeedSectionsError] = useState<string | null>(null);
  const [autoPopulateSections, setAutoPopulateSections] = useState<boolean>(false);

  // New SSE State Variables
  const [detailedProgressPercent, setDetailedProgressPercent] = useState<number>(0);
  const [detailedProgressCurrentTitle, setDetailedProgressCurrentTitle] = useState<string>('');
  const [isDetailedProgressVisible, setIsDetailedProgressVisible] = useState<boolean>(false);
  const eventSourceRef = useRef<(() => void) | null>(null); // Changed type to store abort function

  // Helper function to get selected LLM object
  const selectedLLMObject = useMemo(() => {
    // Ensure availableLLMs is not empty and selectedLLMId is valid before finding
    if (availableLLMs.length > 0 && selectedLLMId) {
      return availableLLMs.find(llm => llm.id === selectedLLMId) as LLM | undefined;
    }
    return undefined;
  }, [selectedLLMId, availableLLMs]);

  // Handler to set selected LLM (object) for the new component
  const handleSetSelectedLLM = (llm: LLM) => {
    setSelectedLLMId(llm.id);
  };
  
  // Handler for updating section content (to be passed to CampaignSectionEditor)
  const handleUpdateSectionContent = (sectionId: number, newContent: string) => {
    handleUpdateSection(sectionId, { content: newContent });
  };

  // Handler for updating section title (to be passed to CampaignSectionEditor)
  const handleUpdateSectionTitle = (sectionId: number, newTitle: string) => {
    handleUpdateSection(sectionId, { title: newTitle });
  };

  const processedToc = useMemo(() => {
    // Use display_toc for rendering in the UI
    if (!campaign?.display_toc || !sections?.length) {
      return campaign?.display_toc || '';
    }
    const tocLines = campaign.display_toc.split('\n');
    const sectionTitleToIdMap = new Map(sections.filter(sec => sec.title).map(sec => [sec.title!.trim().toLowerCase(), `section-container-${sec.id}`]));

    return tocLines.map(line => {
      const match = line.match(/^(?:[#-*]\s*)?(.*)/);
      if (!match || typeof match[1] !== 'string') { // Check if match is null or capture group is not a string
        return line; // Return original line if no valid match
      }
      const potentialTitle = match[1].trim().toLowerCase();

      if (potentialTitle && sectionTitleToIdMap.has(potentialTitle)) {
        const sectionId = sectionTitleToIdMap.get(potentialTitle);
        const prefixMatch = line.match(/^([#-*]\s*)/);
        const prefix = prefixMatch ? prefixMatch[1] : ''; // prefixMatch can also be null
        return `${prefix || ''}[${match[1].trim()}](#${sectionId})`;
      }
      return line;
    }).join('\n');
  }, [campaign?.display_toc, sections]); // Update dependency array

  // Placeholder for handleSeedSectionsFromToc
  const handleSeedSectionsFromToc = async () => {
    if (!campaignId || !campaign?.display_toc) {
      setSeedSectionsError("Cannot create sections: Campaign ID is missing or no Table of Contents available.");
      return;
    }

    if (!window.confirm("This will delete all existing sections and create new ones based on the current Table of Contents. Are you sure you want to proceed?")) {
      return;
    }

    // Clear existing sections as they will be streamed in
    setSections([]);
    setSeedSectionsError(null);
    setIsSeedingSections(true); // Keeps button disabled and text updated
    // setIsPageLoading(true); // REMOVED - let detailed progress control primary feedback
    setIsDetailedProgressVisible(true);
    setDetailedProgressPercent(0);
    setDetailedProgressCurrentTitle('');

    const callbacks: SeedSectionsCallbacks = {
      onOpen: (event) => {
        console.log("SSE connection opened for seeding sections.", event);
        setIsPageLoading(false); // Turn off global spinner once SSE is established
      },
      onProgress: (data: SeedSectionsProgressEvent) => {
        setDetailedProgressPercent(data.progress_percent);
        setDetailedProgressCurrentTitle(data.current_section_title);
      },
      onSectionComplete: (sectionData: CampaignSection) => {
        setSections(prevSections => [...prevSections, sectionData].sort((a, b) => a.order - b.order));
      },
      onDone: (message: string, totalProcessed: number) => {
        console.log("SSE Done:", message, "Total processed:", totalProcessed);
        setIsDetailedProgressVisible(false);
        setIsSeedingSections(false);
        setIsPageLoading(false);
        // Using setSaveSuccess for user feedback instead of alert
        setSaveSuccess(message || `Sections created successfully! Processed: ${totalProcessed}`);
        setTimeout(() => setSaveSuccess(null), 5000); // Clear after 5s

        // if (eventSourceRef.current) { // No longer need to call .close() here
        //   // eventSourceRef.current.close(); // REMOVED
        // }
        eventSourceRef.current = null; // Clear the ref
      },
      onError: (error) => {
        console.error("SSE Error:", error);
        setIsDetailedProgressVisible(false);
        setIsSeedingSections(false);
        setIsPageLoading(false);
        const errorMessage = (error as any)?.message || "An error occurred during section creation.";
        setSeedSectionsError(`SSE Error: ${errorMessage}`);
        // if (eventSourceRef.current) { // No longer need to call .close() here
        //   // eventSourceRef.current.close(); // REMOVED
        // }
        eventSourceRef.current = null; // Clear the ref
      }
    };

    if (campaignId) {
      // Start with page loading true, will be turned off by onOpen or onError
      setIsPageLoading(true);
      eventSourceRef.current = campaignService.seedSectionsFromToc(campaignId, autoPopulateSections, callbacks);
    } else {
      setSeedSectionsError("Campaign ID is missing, cannot start section creation.");
      setIsDetailedProgressVisible(false);
      setIsSeedingSections(false);
      setIsPageLoading(false);
    }
  };

  useEffect(() => {
    // Cleanup function to call abort if component unmounts
    return () => {
      if (eventSourceRef.current) {
        console.log("Aborting SSE connection on component unmount.");
        eventSourceRef.current(); // Call the abort function
        eventSourceRef.current = null;
      }
    };
  }, []); // Empty dependency array means this runs once on mount and cleanup on unmount

  useEffect(() => {
    if (!campaignId) {
      setError('Campaign ID is missing.');
      setIsLoading(false);
      return;
    }

    const fetchInitialData = async () => {
      setIsLoading(true); // This is for the initial load indication
      setError(null);
      try {
        // Use getAvailableLLMs from llmService
        const [campaignDetails, campaignSectionsResponse, fetchedLLMs] = await Promise.all([
          campaignService.getCampaignById(campaignId),
          campaignService.getCampaignSections(campaignId), // This returns { sections: CampaignSection[] }
          getAvailableLLMs(),
        ]);
        setCampaign(campaignDetails);
        // campaignService.getCampaignSections is now expected to return CampaignSection[] directly
        // campaignSectionsResult is named campaignSectionsResponse in the existing code
        if (Array.isArray(campaignSectionsResponse)) {
            setSections(campaignSectionsResponse.sort((a, b) => a.order - b.order));
        } else {
            // This block handles cases where the result might unexpectedly not be an array.
            console.warn("Campaign sections data (campaignSectionsResponse) was not an array as expected:", campaignSectionsResponse);
            setSections([]); // Default to an empty array to prevent further errors.
        }

        setEditableTitle(campaignDetails.title);
        setEditableInitialPrompt(campaignDetails.initial_user_prompt || '');
        setCampaignBadgeImage(campaignDetails.badge_image_url || ''); // Initialize badge image state

        // Load LLM settings from fetched campaign data
        if (campaignDetails.temperature !== null && campaignDetails.temperature !== undefined) {
            setTemperature(campaignDetails.temperature);
        } else {
            setTemperature(0.7); // Default if not set
        }

        setAvailableLLMs(fetchedLLMs);

        if (campaignDetails.selected_llm_id) {
            setSelectedLLMId(campaignDetails.selected_llm_id);
        } else {
            const preferredModelIds = [
                "openai/gpt-4.1-nano",
                "openai/gpt-3.5-turbo",
                "openai/gpt-4",
                "gemini/gemini-pro",
            ];
            let newSelectedLLMId = '';

            // 1. Check preferred models in order
            for (const preferredId of preferredModelIds) {
                const foundModel = fetchedLLMs.find(m => m.id === preferredId);
                if (foundModel) {
                    newSelectedLLMId = foundModel.id;
                    break;
                }
            }

            // 2. If no preferred model found, find the first chat-capable model
            if (!newSelectedLLMId) {
                const potentialChatModels = fetchedLLMs.filter(model =>
                    model.capabilities && (model.capabilities.includes("chat") || model.capabilities.includes("chat-adaptable"))
                );
                if (potentialChatModels.length > 0) {
                    // Try to find preferred models among chat-capable ones first (already covered by above loop, but good for clarity if used independently)
                    // For this logic, we just take the first one if no specific preferred model was found yet.
                    const firstChatModel = potentialChatModels[0];
                    if (firstChatModel) { // Check if firstChatModel is not undefined
                         newSelectedLLMId = firstChatModel.id;
                    }
                }
            }

            // 3. If still no model, take the first from the fetched list
            if (!newSelectedLLMId && fetchedLLMs.length > 0) {
                newSelectedLLMId = fetchedLLMs[0].id;
            }

            setSelectedLLMId(newSelectedLLMId); // This will be '' if fetchedLLMs is empty
        }
        initialLoadCompleteRef.current = true; // Mark initial load of settings as complete
      } catch (err) {
        console.error('Failed to fetch initial campaign or LLM data:', err);
        setError('Failed to load initial data. Please try again later.');
      } finally {
        setIsLoading(false); // Initial load finished
      }
    };
    fetchInitialData();
  }, [campaignId]);

  // Auto-save LLM settings
  useEffect(() => {
    if (!initialLoadCompleteRef.current || !campaignId || !campaign || isLoading) {
        return; // Don't run if initial load isn't complete or essential data missing
    }

    // console.log("LLM_AUTOSAVE_EFFECT_RUN:", {
    //   selectedLLMId,
    //   temperature,
    //   campaignId, // from useParams
    //   campaignIdFromCampaign: campaign?.id,
    //   campaignSelectedLLM: campaign?.selected_llm_id,
    //   campaignTemperature: campaign?.temperature,
    //   isLoading,
    //   debounceTimerExists: !!debounceTimer
    // });

    // Clear previous timer if it exists
    if (debounceTimer) {
        clearTimeout(debounceTimer);
    }

    const newTimer = setTimeout(async () => {
        // Ensure 'campaign' is available from the outer scope of useEffect.
        if (!campaign) {
            console.warn("LLM_AUTOSAVE_TIMEOUT_SKIP: Campaign object not available in setTimeout, skipping.");
            return;
        }
        // campaignId from useParams is available in the outer scope.
        // Using campaign.id from the state object for the actual API call for consistency.
        if (!campaign.id) {
            console.warn("LLM_AUTOSAVE_TIMEOUT_SKIP: Campaign ID not available in campaign state (inside setTimeout), skipping.");
            return;
        }

        // console.log("LLM_AUTOSAVE_CHECKING_CONDITIONS:", {
        //   campaignExists: !!campaign, // Should be true here
        //   selectedLLMId_state: selectedLLMId,
        //   campaign_selected_llm_id: campaign?.selected_llm_id,
        //   temperature_state: temperature,
        //   campaign_temperature: campaign?.temperature
        // });

        // THE CRUCIAL CHECK:
        if (selectedLLMId === campaign.selected_llm_id &&
            temperature === campaign.temperature) {
            // console.log("LLM_AUTOSAVE_SKIPPED: No change in settings.");
            return;
        }

        // If the code reaches here, it means settings have changed and a save is needed.
        // console.log("LLM_AUTOSAVE_PROCEEDING: Settings changed or initial save. Attempting save.", {
        //    campaignIdToSave: campaign.id,
        //    selectedLLMId,
        //    temperature
        // });
        setIsAutoSavingLLMSettings(true);
        setAutoSaveLLMSettingsError(null);
        setAutoSaveLLMSettingsSuccess(null);

        try {
          const payload: campaignService.CampaignUpdatePayload = {
            selected_llm_id: selectedLLMId || null,
            temperature: temperature,
          };
          const updatedCampaign = await campaignService.updateCampaign(campaign.id, payload);
          setCampaign(updatedCampaign);
          setAutoSaveLLMSettingsSuccess("LLM settings auto-saved!");
          setTimeout(() => setAutoSaveLLMSettingsSuccess(null), 3000);
        } catch (err) {
          console.error("Failed to auto-save LLM settings:", err);
          setAutoSaveLLMSettingsError("Failed to auto-save LLM settings.");
          setTimeout(() => setAutoSaveLLMSettingsError(null), 5000);
        } finally {
          setIsAutoSavingLLMSettings(false);
        }
    }, 1500); // Debounce period (e.g., 1.5 seconds)

    setDebounceTimer(newTimer);

    // Cleanup timer on component unmount or before next effect run
    return () => {
        if (newTimer) {
            clearTimeout(newTimer);
        }
    };
  }, [selectedLLMId, temperature, campaignId, campaign?.selected_llm_id, campaign?.temperature, isLoading, debounceTimer]);


  const handleSaveChanges = async () => {
    if (!campaignId || !campaign) return;
    if (editableTitle === campaign.title && editableInitialPrompt === (campaign.initial_user_prompt || '')) {
      setSaveSuccess("No changes to save.");
      setTimeout(() => setSaveSuccess(null), 3000);
      return;
    }
    if (!editableTitle.trim() || !editableInitialPrompt.trim()) {
      setSaveError("Title and Initial Prompt cannot be empty.");
      return;
    }
    setIsPageLoading(true);
    // setIsSaving(true); // Removed, isPageLoading can cover this
    setSaveError(null);
    setSaveSuccess(null);
    try {
      const updatedCampaign = await campaignService.updateCampaign(campaignId, {
        title: editableTitle,
        initial_user_prompt: editableInitialPrompt,
      });
      setCampaign(updatedCampaign);
      setEditableTitle(updatedCampaign.title);
      setEditableInitialPrompt(updatedCampaign.initial_user_prompt || '');
      setSaveSuccess('Campaign details saved successfully!');
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err) {
      setSaveError('Failed to save changes.');
    } finally {
      // setIsSaving(false); // Removed
      setIsPageLoading(false);
    }
  };

  const handleUpdateSectionOrder = async (orderedSectionIds: number[]) => {
    if (!campaignId) return;
    // Optimistically update the UI
    const oldSections = [...sections];
    const newSections = orderedSectionIds.map((id, index) => {
      const section = sections.find(s => s.id === id);
      if (!section) throw new Error(`Section with id ${id} not found for reordering.`); // Should not happen
      return { ...section, order: index };
    }).sort((a,b) => a.order - b.order); // Ensure sorted by new order for local state
    setSections(newSections);
    setIsPageLoading(true);
    try {
      await campaignService.updateCampaignSectionOrder(campaignId, orderedSectionIds);
      setSaveSuccess("Section order saved successfully!"); // Provide feedback
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (error) {
      console.error("Failed to update section order:", error);
      setError("Failed to save section order. Please try again."); // Show error feedback
      setSections(oldSections); // Revert optimistic update on error
    } finally {
      setIsPageLoading(false);
    }
  };

  const handleBadgeImageGenerated = async (imageUrl: string) => {
    if (!campaign) {
      setBadgeUpdateError("No active campaign to update."); // Or handle more gracefully
      return;
    }

    if (!imageUrl || typeof imageUrl !== 'string') {
      setBadgeUpdateError("Invalid image URL received from generation modal.");
      setIsBadgeImageModalOpen(false); // Close modal even if URL is bad
      return;
    }

    setIsPageLoading(true);
    setBadgeUpdateLoading(true);
    setBadgeUpdateError(null);
    setIsBadgeImageModalOpen(false); // Close modal immediately

    try {
      const updatedCampaignData = { badge_image_url: imageUrl };
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      
      if (typeof setCampaign === 'function') { // setCampaign should be available from useState [campaign, setCampaign]
          setCampaign(updatedCampaign);
          // Explicitly update the campaignBadgeImage state variable
          setCampaignBadgeImage(updatedCampaign.badge_image_url || '');

          // Optionally, show a success message for badge update
          // setSaveSuccess("Campaign badge updated successfully!");
          // setTimeout(() => setSaveSuccess(null), 3000);
      } else {
          console.warn("setCampaign function is not available to update local state.");
          // Consider a page reload or other mechanism if direct state update isn't possible
          // For now, rely on next full fetch or manual refresh by user.
      }

    } catch (error: any) {
      console.error("Failed to update badge image URL from modal:", error);
      const detail = error.response?.data?.detail || error.message || "Failed to update badge image from modal.";
      setBadgeUpdateError(detail);
      alert(`Error setting badge: ${detail}`); // Alert for immediate user feedback
    } finally {
      setBadgeUpdateLoading(false);
      setIsPageLoading(false);
    }
  };

  const handleDeleteSection = async (sectionId: number) => {
    if (!campaignId) return;

    if (window.confirm(`Are you sure you want to delete section ${sectionId}? This action cannot be undone.`)) {
      setIsPageLoading(true);
      try {
        await campaignService.deleteCampaignSection(campaignId, sectionId);
        setSections(prevSections => prevSections.filter(s => s.id !== sectionId));
        setSaveSuccess(`Section ${sectionId} deleted successfully.`);
        setTimeout(() => setSaveSuccess(null), 3000);
      } catch (err: any) {
        console.error(`Failed to delete section ${sectionId}:`, err);
        const detail = axios.isAxiosError(err) && err.response?.data?.detail ? err.response.data.detail : (err.message || 'Failed to delete section.');
        setError(`Error deleting section ${sectionId}: ${detail}`);
         setTimeout(() => setError(null), 5000);
      } finally {
        setIsPageLoading(false);
      }
    }
  };

  const handleAddSection = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!campaignId) return;
    if (!newSectionTitle.trim() && !newSectionPrompt.trim()) {
      setAddSectionError("Please provide a title or a prompt for the new section.");
      return;
    }
    setIsPageLoading(true);
    setIsAddingSection(true);
    setAddSectionError(null);
    setAddSectionSuccess(null);
    try {
      const newSection = await campaignService.addCampaignSection(campaignId, {
        title: newSectionTitle.trim() || undefined,
        prompt: newSectionPrompt.trim() || undefined,
        model_id_with_prefix: selectedLLMId || undefined, // Corrected line
      });
      setSections(prev => [...prev, newSection].sort((a, b) => a.order - b.order));
      setNewSectionTitle('');
      setNewSectionPrompt('');
      setAddSectionSuccess("New section added successfully!");
      setTimeout(() => setAddSectionSuccess(null), 3000);
    } catch (err: any) { // Use 'err: any' for easier access to response properties initially
      console.error('Failed to add new section:', err); // Keep console log for full error
      if (axios.isAxiosError(err) && err.response && err.response.data && typeof err.response.data.detail === 'string') {
        setAddSectionError(err.response.data.detail);
      } else if (err instanceof Error) {
        setAddSectionError(err.message);
      } else {
        setAddSectionError('Failed to add new section due to an unexpected error.');
      }
    } finally {
      setIsAddingSection(false);
    setIsPageLoading(false);
    }
  };

  const handleUpdateSection = async (sectionId: number, updatedData: campaignService.CampaignSectionUpdatePayload) => {
    if (!campaignId) return;
    setIsPageLoading(true);
    // setSavingSectionId(sectionId); // Removed
    // setSectionSaveError(prev => ({ ...prev, [sectionId]: null })); // Removed
    try {
      const updatedSection = await campaignService.updateCampaignSection(campaignId, sectionId, updatedData);
      setSections(prev => prev.map(sec => sec.id === sectionId ? updatedSection : sec));
      // Optionally, add a global success message for section updates if desired
      // setSaveSuccess("Section updated successfully!");
      // setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err) {
      // setSectionSaveError(prev => ({ ...prev, [sectionId]: 'Failed to save section.' })); // Removed
      // For simplicity, errors from CampaignSectionView's local save will be shown there.
      // If a global error for section saving is needed, it could be set here.
      console.error(`Error updating section ${sectionId}:`, err);
      // Propagate the error if other parts of this page need to react, or handle globally:
      setError(`Failed to save section ${sectionId}.`); // Example of setting a global error
      setTimeout(() => setError(null), 5000);
      setIsPageLoading(false); // Ensure loading is stopped on error
      throw err; // Re-throw so CampaignSectionView can also catch it for local feedback
    } finally {
      // setSavingSectionId(null); // Removed
      setIsPageLoading(false); // Ensure loading is always stopped
    }
  };

  const handleGenerateTOC = async () => {
    if (!campaignId) return;
    setIsPageLoading(true);
    setIsGeneratingTOC(true);
    setTocError(null);
    setSaveSuccess(null);
    try {
      const updatedCampaign = await campaignService.generateCampaignTOC(campaignId, {});
      setCampaign(updatedCampaign);
      setSaveSuccess("Table of Contents generated successfully!");
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err) {
      setTocError('Failed to generate Table of Contents.');
    } finally {
      setIsGeneratingTOC(false);
      setIsPageLoading(false);
    }
  };

  const handleGenerateTitles = async () => {
    if (!campaignId) return;
    setIsPageLoading(true);
    setIsGeneratingTitles(true);
    setTitlesError(null);
    setSuggestedTitles(null);
    setSaveSuccess(null);
    try {
      const response = await campaignService.generateCampaignTitles(campaignId, {}, 5);
      setSuggestedTitles(response.titles);
      // setSaveSuccess("Suggested titles generated successfully!"); // Optional: keep or remove
      // setTimeout(() => setSaveSuccess(null), 3000);
      setIsSuggestedTitlesModalOpen(true); // Open the modal
    } catch (err) {
      setTitlesError('Failed to generate titles.');
    } finally {
      setIsGeneratingTitles(false);
      setIsPageLoading(false);
    }
  };

  const handleTitleSelected = (selectedTitle: string) => {
    setEditableTitle(selectedTitle);
    setIsSuggestedTitlesModalOpen(false);
    // setSuggestedTitles(null); // Optional: Clear suggestions after selection
  };
  
  // const hasChanges = campaign ? (editableTitle !== campaign.title || editableInitialPrompt !== (campaign.initial_user_prompt || '')) : false; // Removed

  const handleExportHomebrewery = async () => {
    if (!campaignId || !campaign) return;

    setIsPageLoading(true);
    setIsExporting(true);
    setExportError(null);
    setSaveSuccess(null); // Clear other messages

    try {
      const markdownString = await campaignService.exportCampaignToHomebrewery(campaignId);
      
      const filename = `campaign_${campaign.title?.replace(/\s+/g, '_') || campaignId}_homebrewery.md`;
      const blob = new Blob([markdownString], { type: 'text/markdown;charset=utf-8,' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      setSaveSuccess("Campaign exported successfully!"); 
      setTimeout(() => setSaveSuccess(null), 3000);

    } catch (err) {
      console.error('Failed to export campaign to Homebrewery:', err);
      setExportError('Failed to export campaign. Please try again.');
      setTimeout(() => setExportError(null), 5000); // Clear error after 5s
    } finally {
      setIsExporting(false);
      setIsPageLoading(false);
    }
  };

  const handleOpenBadgeImageModal = async () => { // Renamed from handleSetOrChangeBadgeImage
    if (!campaign) return;
    setIsBadgeImageModalOpen(true); 
  };

  const handleEditBadgeImageUrl = async () => {
    if (!campaign) return;
    const currentUrl = campaign.badge_image_url || "";
    const imageUrl = window.prompt("Enter or edit the image URL for the campaign badge:", currentUrl);

    if (imageUrl === null) return; // User cancelled prompt

    if (imageUrl.trim() !== "" && !imageUrl.startsWith('http') && !imageUrl.startsWith('data:')) {
       alert("Please enter a valid HTTP/HTTPS URL or a Data URL.");
       return;
    }
    
    setIsPageLoading(true);
    setBadgeUpdateLoading(true);
    setBadgeUpdateError(null);
    try {
      const updatedCampaignData = { badge_image_url: imageUrl.trim() === "" ? null : imageUrl.trim() };
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      
      if (typeof setCampaign === 'function') { 
          setCampaign(updatedCampaign);
          // Explicitly update the campaignBadgeImage state variable as well for immediate UI refresh
          setCampaignBadgeImage(updatedCampaign.badge_image_url || '');
      } else {
          console.warn("setCampaign function is not available to update local state.");
      }
    } catch (error: any) {
      console.error("Failed to update badge image URL via edit:", error);
      const detail = error.response?.data?.detail || error.message || "Failed to update badge image URL.";
      setBadgeUpdateError(detail);
      alert(`Error: ${detail}`);
    } finally {
      setBadgeUpdateLoading(false);
      setIsPageLoading(false);
    }
  };

  const handleRemoveBadgeImage = async () => {
    if (!campaign || !campaign.badge_image_url) return;

    if (!window.confirm("Are you sure you want to remove the campaign badge image?")) return;

    setIsPageLoading(true);
    setBadgeUpdateLoading(true);
    setBadgeUpdateError(null);
    try {
      const updatedCampaignData = { badge_image_url: null }; // Set to null to remove
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      
      if (typeof setCampaign === 'function') {
          setCampaign(updatedCampaign);
          // Explicitly update the campaignBadgeImage state variable when removing
          setCampaignBadgeImage(''); // Set to empty string as URL is removed
      } else {
           console.log("Campaign badge URL removed. Parent component should re-fetch or update state.");
      }

    } catch (error: any) {
      console.error("Failed to remove badge image URL:", error);
      const detail = error.response?.data?.detail || error.message || "Failed to remove badge image.";
      setBadgeUpdateError(detail);
      alert(`Error: ${detail}`);
    } finally {
      setBadgeUpdateLoading(false);
      setIsPageLoading(false);
    }
  };


  if (isLoading) return <LoadingSpinner />; // Use spinner for initial load
  if (error) return <p className="error-message">{error}</p>;
  if (!campaign) return <p className="error-message">Campaign not found.</p>;

  const detailsTabContent = (
    <>
      <CampaignDetailsEditor
        editableTitle={editableTitle}
        setEditableTitle={setEditableTitle}
        initialPrompt={editableInitialPrompt}
        setInitialPrompt={setEditableInitialPrompt}
        campaignBadgeImage={campaignBadgeImage}
        setCampaignBadgeImage={(value: string) => {
          setCampaignBadgeImage(value);
        }}
        handleSaveCampaignDetails={handleSaveChanges}
        // Pass new props for title generation
        onSuggestTitles={handleGenerateTitles}
        isGeneratingTitles={isGeneratingTitles}
        titlesError={titlesError}
        selectedLLMId={selectedLLMId}
        // Pass original values for enabling/disabling save button
        originalTitle={campaign.title}
        originalInitialPrompt={campaign.initial_user_prompt || ''}
        // Pass props for badge actions
        originalBadgeImageUrl={campaign.badge_image_url || ''}
        onOpenBadgeImageModal={handleOpenBadgeImageModal}
        onEditBadgeImageUrl={handleEditBadgeImageUrl}
        onRemoveBadgeImage={handleRemoveBadgeImage}
        badgeUpdateLoading={badgeUpdateLoading}
        badgeUpdateError={badgeUpdateError}
      />
      {/* Global save error/success can be shown here or above tabs */}
      {saveError && <p className="error-message save-feedback">{saveError}</p>}
      {saveSuccess && <p className="success-message save-feedback">{saveSuccess}</p>}

      {/* The title-generation-section div has been removed */}
      {/* The campaign-badge-area editor-section div has been removed and its functionality moved to CampaignDetailsEditor */}

      {/* Campaign Concept section is MOVED from here to above tabs */}
      {/* TOC Section */}
      <section className="campaign-detail-section editor-section">
        {campaign.display_toc && ( // Use display_toc: Only show header if TOC exists to be collapsed/expanded
          <h2 onClick={() => setIsTocCollapsed(!isTocCollapsed)} style={{ cursor: 'pointer' }}>
            {isTocCollapsed ? '▶' : '▼'} Table of Contents
          </h2>
        )}
        {/* Content: TOC display and/or Generate button */}
        {(!campaign.display_toc || !isTocCollapsed) && ( // Use display_toc: Show if no TOC, or if TOC exists and is not collapsed
          <div className="toc-controls-and-display" style={{ marginTop: '10px' }}>
            {campaign.display_toc && <ReactMarkdown>{processedToc}</ReactMarkdown>} {/* Use display_toc for conditional rendering */}
            <Button
              onClick={handleGenerateTOC}
              disabled={isGeneratingTOC || !selectedLLMId}
              className="action-button"
              style={{ marginTop: campaign.display_toc ? '10px' : '0' }} // Use display_toc for style condition
              icon={<ListAltIcon />}
              tooltip={!selectedLLMId ? "Select an LLM model from the Settings tab first" : "Generate or re-generate the Table of Contents based on the campaign concept and sections"}
            >
              {isGeneratingTOC ? 'Generating TOC...' : (campaign.display_toc ? 'Re-generate Table of Contents' : 'Generate Table of Contents')} {/* Use display_toc for button text */}
            </Button>
            {tocError && <p className="error-message feedback-message" style={{ marginTop: '5px' }}>{tocError}</p>}

            {campaign.display_toc && (
              <div style={{ marginTop: '15px' }}>
                {!isDetailedProgressVisible ? (
                  <>
                    <Button
                      onClick={handleSeedSectionsFromToc}
                      disabled={isSeedingSections || !campaign.display_toc}
                      className="action-button"
                      icon={<AddCircleOutlineIcon />}
                      tooltip="Parse the current Table of Contents and create campaign sections based on its structure. Optionally auto-populate content."
                    >
                      {isSeedingSections ? (autoPopulateSections ? 'Creating & Populating Sections...' : 'Creating Sections...') : 'Approve TOC & Create Sections'}
                    </Button>
                    {/* seedSectionsError is now displayed by DetailedProgressDisplay if isDetailedProgressVisible, or here if not */}
                    {!isDetailedProgressVisible && seedSectionsError && <p className="error-message feedback-message" style={{ marginTop: '5px' }}>{seedSectionsError}</p>}
                    <div style={{ marginTop: '10px', marginBottom: '10px' }}>
                      <label htmlFor="autoPopulateCheckbox" style={{ marginRight: '8px' }}>
                        Auto-populate sections with generated content:
                      </label>
                      <input
                        type="checkbox"
                        id="autoPopulateCheckbox"
                        checked={autoPopulateSections}
                        onChange={(e) => setAutoPopulateSections(e.target.checked)}
                        disabled={isSeedingSections}
                      />
                    </div>
                  </>
                ) : (
                  <DetailedProgressDisplay
                    percent={detailedProgressPercent}
                    currentTitle={detailedProgressCurrentTitle}
                    error={seedSectionsError} // Pass the error to the component
                    title="Seeding Sections from Table of Contents..." // Optional: override default title
                  />
                )}
              </div>
            )}
          </div>
        )}
      </section>
    </>
  );

  const sectionsTabContent = (
    <>
      <div className="section-display-controls editor-section">
        <h3>Section Display</h3>
        <Button
          onClick={() => setForceCollapseAll(true)}
          className="action-button"
          icon={<UnfoldLessIcon />}
          tooltip="Collapse all campaign sections"
        >
          Collapse All Sections
        </Button>
        <Button
          onClick={() => setForceCollapseAll(false)}
          className="action-button"
          icon={<UnfoldMoreIcon />}
          tooltip="Expand all campaign sections"
        >
          Expand All Sections
        </Button>
      </div>
      <CampaignSectionEditor
        campaignId={campaignId!} // campaignId is checked at the start of CampaignEditorPage
        sections={sections}
        setSections={setSections}
        handleAddNewSection={() => setIsAddSectionCollapsed(false)}
        // Disable "Add New Section" button if concept is not defined
        isAddSectionDisabled={!campaign?.concept?.trim()}
        handleDeleteSection={handleDeleteSection}
        handleUpdateSectionContent={handleUpdateSectionContent}
        handleUpdateSectionTitle={handleUpdateSectionTitle}
        onUpdateSectionOrder={handleUpdateSectionOrder} // Pass the new handler
        forceCollapseAllSections={forceCollapseAll} // Pass the state here
      />
      {!isAddSectionCollapsed && campaign?.concept?.trim() && ( // Only show form if concept exists and not collapsed
        <div className="editor-actions add-section-area editor-section card-like" style={{ marginTop: '20px' }}>
          <h3>Add New Section</h3>
          <form onSubmit={handleAddSection} className="add-section-form">
            <div className="form-group">
              <label htmlFor="newSectionTitle">Section Title (Optional):</label>
              <input type="text" id="newSectionTitle" className="form-input" value={newSectionTitle} onChange={(e) => setNewSectionTitle(e.target.value)} placeholder="E.g., Chapter 1: The Discovery" />
            </div>
            <div className="form-group">
              <label htmlFor="newSectionPrompt">Section Prompt (Optional):</label>
              <textarea id="newSectionPrompt" className="form-textarea" value={newSectionPrompt} onChange={(e) => setNewSectionPrompt(e.target.value)} rows={3} placeholder="E.g., Start with the players finding a mysterious map..." />
            </div>
            {selectedLLMObject && (
                 <p style={{fontSize: '0.9em', margin: '10px 0'}}>New section will use LLM: <strong>{selectedLLMObject.name}</strong></p>
            )}
            {addSectionError && <p className="error-message feedback-message">{addSectionError}</p>}
            {addSectionSuccess && <p className="success-message feedback-message">{addSectionSuccess}</p>}
            <Button
              type="submit"
              disabled={isAddingSection || !selectedLLMId || !campaign?.concept?.trim()}
              className="action-button add-section-button"
              icon={<AddCircleOutlineIcon />}
              tooltip={!campaign?.concept?.trim() ? "Please define and save a campaign concept first." : (!selectedLLMId ? "Please select an LLM in settings." : "Add this new section to the campaign")}
            >
              {isAddingSection ? 'Adding Section...' : 'Confirm & Add Section'}
            </Button>
            <Button
              type="button"
              onClick={() => setIsAddSectionCollapsed(true)}
              className="action-button secondary-action-button"
              style={{marginLeft: '10px'}}
              icon={<CancelIcon />}
              tooltip="Cancel adding a new section"
            >
              Cancel
            </Button>
          </form>
        </div>
      )}
      {!campaign?.concept?.trim() && (
        <div className="editor-section user-message card-like" style={{ marginTop: '20px', padding: '15px', textAlign: 'center' }}>
          <Typography variant="h6" color="textSecondary">
            Please define and save a campaign concept in the 'Details' tab before adding or managing sections.
          </Typography>
        </div>
      )}
    </>
  );

  const settingsTabContent = (
    <>
      {selectedLLMObject && availableLLMs.length > 0 ? (
        <CampaignLLMSettings
          selectedLLM={selectedLLMObject}
          setSelectedLLM={handleSetSelectedLLM}
          temperature={temperature}
          setTemperature={setTemperature}
          availableLLMs={availableLLMs.map(m => ({...m, name: m.name || m.id})) as LLM[]}
        />
      ) : (
        <div className="editor-section">
          <p>Loading LLM settings or no LLMs available...</p>
          {!selectedLLMId && availableLLMs.length > 0 && (
            <Button
              onClick={() => setIsLLMDialogOpen(true)}
              className="action-button"
              icon={<SettingsSuggestIcon />}
              tooltip="Select the primary Language Model for campaign generation tasks"
            >
              Select Initial LLM Model
            </Button>
          )}
        </div>
      )}
      <div className="llm-autosave-feedback editor-section feedback-messages">
        {isAutoSavingLLMSettings && <p className="feedback-message saving-indicator">Auto-saving LLM settings...</p>}
        {autoSaveLLMSettingsError && <p className="error-message feedback-message">{autoSaveLLMSettingsError}</p>}
        {autoSaveLLMSettingsSuccess && <p className="success-message feedback-message">{autoSaveLLMSettingsSuccess}</p>}
      </div>
      {/* LLM related errors can be shown within this tab or globally */}
      {tocError && <p className="error-message llm-feedback editor-section">{tocError}</p>}
      {/* titlesError is now handled by CampaignDetailsEditor */}

      {/* The old suggested titles display is removed from here. It's now handled by the modal. */}

      <div className="action-group export-action-group editor-section">
        <Button
          onClick={handleExportHomebrewery}
          disabled={isExporting}
          className="llm-button export-button" // Assuming llm-button is a valid class for Button or should be action-button
          icon={<PublishIcon />}
          tooltip="Export the campaign content as Markdown formatted for Homebrewery"
        >
          {isExporting ? 'Exporting...' : 'Export to Homebrewery'}
        </Button>
        {exportError && <p className="error-message llm-feedback">{exportError}</p>}
      </div>
    </>
  );

  const tabItems: TabItem[] = [
    { name: 'Details', content: detailsTabContent },
    { name: 'Sections', content: sectionsTabContent, disabled: !campaign?.concept?.trim() },
    { name: 'Settings', content: settingsTabContent },
  ];

  return (
    <div className="campaign-editor-page">
      {isPageLoading && <LoadingSpinner />}

      {/* === Campaign Concept Display === */}
      {campaign && campaign.concept && (
        <section className="campaign-detail-section read-only-section editor-section page-level-concept">
          <h2>Campaign Concept</h2>
          <div className="concept-content"><ReactMarkdown>{campaign.concept}</ReactMarkdown></div>
        </section>
      )}
      {/* === End of Campaign Concept Display === */}

      <Tabs tabs={tabItems} />

      {/* Modals remain at the top level */}
      <LLMSelectionDialog
        isOpen={isLLMDialogOpen}
        currentModelId={selectedLLMId}
        onModelSelect={(modelId) => {
          if (modelId !== null) {
            setSelectedLLMId(modelId);
          }
          setIsLLMDialogOpen(false);
        }}
        onClose={() => setIsLLMDialogOpen(false)}
      />
      <ImageGenerationModal
        isOpen={isBadgeImageModalOpen}
        onClose={() => setIsBadgeImageModalOpen(false)}
        onImageSuccessfullyGenerated={handleBadgeImageGenerated}
      />
      <SuggestedTitlesModal
        isOpen={isSuggestedTitlesModalOpen}
        onClose={() => {
          setIsSuggestedTitlesModalOpen(false);
          // setSuggestedTitles(null); // Optional: Clear suggestions when modal is closed without selection
        }}
        titles={suggestedTitles || []}
        onSelectTitle={handleTitleSelected}
      />
    </div>
  );
};

export default CampaignEditorPage;

// Note: The redundant LLMModel type alias (campaignService.ModelInfo) was already addressed by using LLMModel from llmService.
