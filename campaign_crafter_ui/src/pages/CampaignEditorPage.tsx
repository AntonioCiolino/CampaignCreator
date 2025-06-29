import React, { useState, useEffect, FormEvent, useMemo, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import LoadingSpinner from '../components/common/LoadingSpinner';
import LLMSelectionDialog from '../components/modals/LLMSelectionDialog';
import ImageGenerationModal from '../components/modals/ImageGenerationModal/ImageGenerationModal';
import SuggestedTitlesModal from '../components/modals/SuggestedTitlesModal';
import * as campaignService from '../services/campaignService';
import { getCampaignFiles } from '../services/campaignService'; // Added for getCampaignFiles
import { Campaign, CampaignSection, TOCEntry, SeedSectionsProgressEvent, SeedSectionsCallbacks } from '../services/campaignService';
import { getAvailableLLMs, LLMModel } from '../services/llmService';
import ReactMarkdown from 'react-markdown';
import './CampaignEditorPage.css';
import Button from '../components/common/Button';
import ImagePreviewModal from '../components/modals/ImagePreviewModal'; // Added import

import ListAltIcon from '@mui/icons-material/ListAlt';
import UnfoldLessIcon from '@mui/icons-material/UnfoldLess';
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import CancelIcon from '@mui/icons-material/Cancel';
import SettingsSuggestIcon from '@mui/icons-material/SettingsSuggest';
import PublishIcon from '@mui/icons-material/Publish';
import EditIcon from '@mui/icons-material/Edit'; // Import EditIcon
import SaveIcon from '@mui/icons-material/Save'; // Import SaveIcon for concept saving
import ImageIcon from '@mui/icons-material/Image';
// import ThematicImageDisplay, { ThematicImageDisplayProps } from '../components/common/ThematicImageDisplay'; // Old import
import MoodBoardPanel from '../components/common/MoodBoardPanel'; // New import

import CampaignDetailsEditor from '../components/campaign_editor/CampaignDetailsEditor';
import CampaignLLMSettings from '../components/campaign_editor/CampaignLLMSettings';
import CampaignSectionEditor from '../components/campaign_editor/CampaignSectionEditor';
import { LLMModel as LLM } from '../services/llmService';
import Tabs, { TabItem } from '../components/common/Tabs';
import { Typography, TextField } from '@mui/material'; // Import TextField
import DetailedProgressDisplay from '../components/common/DetailedProgressDisplay';
import TOCEditor from '../components/campaign_editor/TOCEditor';
import CampaignThemeEditor, { CampaignThemeData } from '../components/campaign_editor/CampaignThemeEditor';
import { applyThemeToDocument } from '../utils/themeUtils'; // Import the function
import { BlobFileMetadata } from '../types/fileTypes'; // Added for CampaignFile type

const CampaignEditorPage: React.FC = () => {
  const { campaignId } = useParams<{ campaignId: string }>();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [sections, setSections] = useState<CampaignSection[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isPageLoading, setIsPageLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [editableTitle, setEditableTitle] = useState<string>('');
  const [editableInitialPrompt, setEditableInitialPrompt] = useState<string>('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const [isGeneratingTOC, setIsGeneratingTOC] = useState<boolean>(false);
  const [tocError, setTocError] = useState<string | null>(null);
  const [isGeneratingTitles, setIsGeneratingTitles] = useState<boolean>(false);
  const [titlesError, setTitlesError] = useState<string | null>(null);
  const [suggestedTitles, setSuggestedTitles] = useState<string[] | null>(null);

  const [newSectionTitle, setNewSectionTitle] = useState<string>('');
  const [newSectionPrompt, setNewSectionPrompt] = useState<string>('');
  const [isAddingSection, setIsAddingSection] = useState<boolean>(false);
  const [addSectionError, setAddSectionError] = useState<string | null>(null);
  const [addSectionSuccess, setAddSectionSuccess] = useState<string | null>(null);

  const [availableLLMs, setAvailableLLMs] = useState<LLMModel[]>([]);
  const [isLLMsLoading, setIsLLMsLoading] = useState<boolean>(true); // Added state
  const [selectedLLMId, setSelectedLLMId] = useState<string | null>(null);
  const [temperature, setTemperature] = useState<number>(0.7);

  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const [forceCollapseAll, setForceCollapseAll] = useState<boolean | undefined>(undefined);

  const [isCampaignConceptCollapsed, setIsCampaignConceptCollapsed] = useState<boolean>(true);
  const [isTocCollapsed, setIsTocCollapsed] = useState<boolean>(false);
  const [isAddSectionCollapsed, setIsAddSectionCollapsed] = useState<boolean>(true);
  const [isLLMDialogOpen, setIsLLMDialogOpen] = useState<boolean>(false);
  const [isBadgeImageModalOpen, setIsBadgeImageModalOpen] = useState(false);
  const [isSuggestedTitlesModalOpen, setIsSuggestedTitlesModalOpen] = useState<boolean>(false);

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [isAutoSavingLLMSettings, setIsAutoSavingLLMSettings] = useState<boolean>(false);
  const [autoSaveLLMSettingsError, setAutoSaveLLMSettingsError] = useState<string | null>(null);
  const [autoSaveLLMSettingsSuccess, setAutoSaveLLMSettingsSuccess] = useState<string | null>(null);
  const initialLoadCompleteRef = useRef(false);

  const [badgeUpdateLoading, setBadgeUpdateLoading] = useState(false);
  const [badgeUpdateError, setBadgeUpdateError] = useState<string | null>(null);
  const [campaignBadgeImage, setCampaignBadgeImage] = useState<string>('');

  const [isSeedingSections, setIsSeedingSections] = useState<boolean>(false);
  const [seedSectionsError, setSeedSectionsError] = useState<string | null>(null);
  const [autoPopulateSections, setAutoPopulateSections] = useState<boolean>(false);

  const [detailedProgressPercent, setDetailedProgressPercent] = useState<number>(0);
  const [detailedProgressCurrentTitle, setDetailedProgressCurrentTitle] = useState<string>('');
  const [isDetailedProgressVisible, setIsDetailedProgressVisible] = useState<boolean>(false);
  const eventSourceRef = useRef<(() => void) | null>(null);

  const [editableDisplayTOC, setEditableDisplayTOC] = useState<TOCEntry[]>([]);
  const [isSavingTOC, setIsSavingTOC] = useState<boolean>(false);
  const [tocSaveError, setTocSaveError] = useState<string | null>(null);
  const [tocSaveSuccess, setTocSaveSuccess] = useState<string | null>(null);
  const [isTOCEditorVisible, setIsTOCEditorVisible] = useState<boolean>(false);

  // State for Concept Editor
  const [isConceptEditorVisible, setIsConceptEditorVisible] = useState<boolean>(false);
  const [editableConcept, setEditableConcept] = useState<string>('');
  const [conceptSaveError, setConceptSaveError] = useState<string | null>(null);
  const [conceptSaveSuccess, setConceptSaveSuccess] = useState<string | null>(null);

  // Rename state for MoodBoardPanel visibility
  const [isMoodBoardPanelOpen, setIsMoodBoardPanelOpen] = useState<boolean>(false);
  // Remove thematicImageData state as MoodBoardPanel will use campaign.mood_board_image_urls directly
  // const [thematicImageData, setThematicImageData] = useState<Omit<ThematicImageDisplayProps, 'isVisible' | 'onClose'>>({
  //   imageUrl: null,
  //   promptUsed: null,
  //   isLoading: false,
  //   error: null,
  //   title: "Thematic Image" // Default title
  // });

  // State for Theme Editor
  const [themeData, setThemeData] = useState<CampaignThemeData>({});
  const [isSavingTheme, setIsSavingTheme] = useState<boolean>(false);
  const [editableMoodBoardUrls, setEditableMoodBoardUrls] = useState<string[]>([]);
  const [themeSaveError, setThemeSaveError] = useState<string | null>(null);
  const [themeSaveSuccess, setThemeSaveSuccess] = useState<string | null>(null);

  // State for Mood Board Auto-Save
  const [moodBoardDebounceTimer, setMoodBoardDebounceTimer] = useState<NodeJS.Timeout | null>(null);
  const [isAutoSavingMoodBoard, setIsAutoSavingMoodBoard] = useState(false);
  const [autoSaveMoodBoardError, setAutoSaveMoodBoardError] = useState<string | null>(null);
  const [autoSaveMoodBoardSuccess, setAutoSaveMoodBoardSuccess] = useState<string | null>(null);

  // State for generating image for mood board
  const [isGeneratingForMoodBoard, setIsGeneratingForMoodBoard] = useState<boolean>(false);
  const [moodBoardPanelWidth, setMoodBoardPanelWidth] = useState<number>(400); // Default width
  const [activeEditorTab, setActiveEditorTab] = useState<string>('Details');
  const [sectionToExpand, setSectionToExpand] = useState<string | null>(null);

  // State for manual concept generation
  const [isGeneratingConceptManually, setIsGeneratingConceptManually] = useState<boolean>(false);
  const [manualConceptError, setManualConceptError] = useState<string | null>(null);

  // State for Campaign Files (as per plan step 1)
  const [campaignFiles, setCampaignFiles] = useState<BlobFileMetadata[]>([]);
  const [campaignFilesLoading, setCampaignFilesLoading] = useState<boolean>(false);
  const [campaignFilesError, setCampaignFilesError] = useState<string | null>(null);
  const [prevCampaignIdForFiles, setPrevCampaignIdForFiles] = useState<string | null>(null);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState<boolean>(false); // State for image preview modal
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null); // State for image preview URL


  const handleTocLinkClick = useCallback((sectionIdFromLink: string | null) => {
    if (!sectionIdFromLink) return;

    const actualId = sectionIdFromLink.replace('section-container-', '');
    console.log(`TOC Link clicked for actual section ID: ${actualId}`);

    const targetTabName = "Sections";
    setSectionToExpand(actualId); // Set which section should ensure it's expanded

    if (activeEditorTab !== targetTabName) {
      setActiveEditorTab(targetTabName); // Switch tab if not already on it
      console.log(`Switched to tab: ${targetTabName}`);
      // The useEffect below will handle scrolling once the tab is active and section is flagged for expansion
    } else {
      // If already on the correct tab, the useEffect will still pick up the change in sectionToExpand
      // and perform the scroll.
    }
    // No direct scrolling here.
  }, [activeEditorTab, setActiveEditorTab, setSectionToExpand]);

  useEffect(() => {
    if (activeEditorTab === "Sections" && sectionToExpand) {
      // Use a microtask or a short timeout to allow DOM updates (tab switch, section expansion)
      // requestAnimationFrame is often good for this, but setTimeout can also work.
      const scrollTimer = setTimeout(() => {
        const elementId = `section-container-${sectionToExpand}`;
        const element = document.getElementById(elementId);

        if (element) {
          console.log(`Scrolling to and focusing element: ${elementId}`);
          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
          element.focus({ preventScroll: true });
        } else {
          console.warn(`Element with ID ${elementId} not found for scrolling.`);
        }

        // Reset sectionToExpand to allow user to manually collapse/expand again
        // and to prevent this effect from re-running unnecessarily.
        setSectionToExpand(null);
      }, 100); // 100ms delay, adjust if needed, or use requestAnimationFrame

      return () => clearTimeout(scrollTimer); // Cleanup timer
    }
  }, [activeEditorTab, sectionToExpand, setSectionToExpand]); // Dependencies

  const handleSetThematicImage = async (imageUrl: string, prompt: string) => {
    // This function now only handles setting the *main* thematic image for the campaign.
    // The MoodBoardPanel will display campaign.mood_board_image_urls.
    // The logic to auto-apply this to theme background is already within this function.

    if (!campaign || !campaign.id) {
      console.error("Campaign data is not available to save thematic image.");
      // thematicImageData state is removed, so can't update it here.
      // Perhaps set a general page error if needed:
      // setError("Campaign data not loaded, cannot save thematic image.");
      return;
    }

    const payload: campaignService.CampaignUpdatePayload = {
      thematic_image_url: imageUrl,
      thematic_image_prompt: prompt,
    };

    try {
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, payload);
      setCampaign(updatedCampaign); // Update main campaign state

      // If the panel was previously showing the old thematic image,
      // it will now be closed by default. User can reopen to see mood board.
      // setIsMoodBoardPanelOpen(true); // Or decide if it should auto-open for the new thematic image.

      setSaveSuccess("Campaign's main thematic image saved!");
      setTimeout(() => setSaveSuccess(null), 3000);

      // New Logic: Auto-apply to theme background and auto-save theme
      const newThematicImageUrl = updatedCampaign.thematic_image_url;
      if (newThematicImageUrl && campaign.id) { // Ensure campaign.id is available for the theme save
        const newThemeSettings = {
          ...themeData, // Current themeData state
          theme_background_image_url: newThematicImageUrl,
          theme_background_image_opacity: (themeData.theme_background_image_opacity === null || themeData.theme_background_image_opacity === undefined)
                                         ? 0.5 // Default opacity if not previously set for a background image
                                         : themeData.theme_background_image_opacity,
        };
        setThemeData(newThemeSettings); // Update local theme state
        applyThemeToDocument(newThemeSettings); // Apply visually

        // Auto-save this specific theme update to the backend
        const themeUpdatePayload: campaignService.CampaignUpdatePayload = {
             theme_background_image_url: newThemeSettings.theme_background_image_url,
             theme_background_image_opacity: newThemeSettings.theme_background_image_opacity,
        };
        try {
             await campaignService.updateCampaign(campaign.id, themeUpdatePayload); // Use campaign.id
             console.log("Theme background automatically updated and saved after main thematic image change.");
             // Optionally show a transient success message for this auto-save
             // setThemeSaveSuccess("Theme background updated with campaign image!");
             // setTimeout(() => setThemeSaveSuccess(null), 3000);
        } catch (themeSaveError) {
             console.error("Failed to auto-save theme background after main thematic image change:", themeSaveError);
             // setError("Failed to auto-save theme background. You may need to save manually via Theme tab.");
             // setTimeout(() => setError(null), 5000);
        }
      } else if (!newThematicImageUrl) {
        console.log("Campaign thematic image was cleared. Theme background image remains unchanged.");
      }

    } catch (err) {
      console.error("Failed to save thematic image:", err);
      setError("Failed to save campaign's main thematic image. Please check your connection and try again.");
      // Optional: Clear the error after some time
      // setTimeout(() => setError(null), 5000);
    } finally {
      // setIsPageLoading(false);
      // thematicImageData state was removed, so no cleanup needed for it here
    }
  };

  const handleMoodBoardResize = useCallback((newWidth: number) => {
    // Add constraints for min/max width if desired
    const minWidth = 250; // Example min width
    const maxWidth = 800; // Example max width
    let constrainedWidth = newWidth;
    if (newWidth < minWidth) constrainedWidth = minWidth;
    if (newWidth > maxWidth) constrainedWidth = maxWidth;
    setMoodBoardPanelWidth(constrainedWidth);
  }, []);

  const selectedLLMObject = useMemo(() => {
    if (availableLLMs.length > 0 && selectedLLMId) {
      return availableLLMs.find(llm => llm.id === selectedLLMId) as LLM | undefined;
    }
    return undefined;
  }, [selectedLLMId, availableLLMs]);

  const handleSetSelectedLLM = (llm: LLM | null) => {
    setSelectedLLMId(llm ? llm.id : null); // Corrected to 'llm.id'
  };
  
  const handleUpdateSectionContent = (sectionId: number, newContent: string) => {
    handleUpdateSection(sectionId, { content: newContent });
  };

  const handleUpdateSectionTitle = (sectionId: number, newTitle: string) => {
    handleUpdateSection(sectionId, { title: newTitle });
  };

  const ensureLLMSettingsSaved = useCallback(async (): Promise<boolean> => {
    if (!campaign || !campaignId) {
      setAutoSaveLLMSettingsError("Campaign data is not available to save LLM settings.");
      return false;
    }
    const llmSettingsChanged = selectedLLMId !== campaign.selected_llm_id || temperature !== campaign.temperature;
    if (llmSettingsChanged) {
      setIsPageLoading(true);
      setAutoSaveLLMSettingsError(null);
      setAutoSaveLLMSettingsSuccess(null);
      try {
        const payload: campaignService.CampaignUpdatePayload = {
          selected_llm_id: selectedLLMId || null,
          temperature: temperature,
        };
        const updatedCampaign = await campaignService.updateCampaign(campaign.id, payload);
        setCampaign(updatedCampaign);
        setAutoSaveLLMSettingsSuccess("LLM settings saved successfully.");
        setTimeout(() => setAutoSaveLLMSettingsSuccess(null), 3000);
        return true;
      } catch (err) {
        console.error("Failed to save LLM settings:", err);
        setAutoSaveLLMSettingsError("Failed to save LLM settings. Please try again.");
        setTimeout(() => setAutoSaveLLMSettingsError(null), 5000);
        return false;
      } finally {
        setIsPageLoading(false);
      }
    }
    return true;
  }, [campaign, campaignId, selectedLLMId, temperature]);

  const processedToc = useMemo(() => {
    if (!campaign || !campaign.display_toc || campaign.display_toc.length === 0) {
      return '';
    }
    const sectionTitleToIdMap = new Map(
      sections.filter(sec => sec.title).map(sec => [sec.title!.trim().toLowerCase(), `section-container-${sec.id}`])
    );
    return campaign.display_toc.map((tocEntry: TOCEntry) => {
      const title = tocEntry.title || "Untitled Section";
      const typeDisplay = tocEntry.type || 'N/A'; // Default if type is missing
      const cleanedTitle = title.trim().toLowerCase();
      const sectionId = sectionTitleToIdMap.get(cleanedTitle);
      if (sectionId && sections?.length > 0) {
        return `- [${title}](#${sectionId}) (Type: ${typeDisplay})`;
      }
      return `- ${title} (Type: ${typeDisplay})`;
    }).join('\n');
  }, [campaign, sections]);

  const handleSeedSectionsFromToc = async () => {
    const llmSettingsSaved = await ensureLLMSettingsSaved();
    if (!llmSettingsSaved) {
      setSeedSectionsError("Failed to save LLM settings before seeding. Please review settings and try again.");
      return;
    }
    if (!campaignId || !campaign?.display_toc) {
      setSeedSectionsError("Cannot create sections: Campaign ID is missing or no Table of Contents available.");
      return;
    }
    if (campaign.display_toc.length === 0) {
        setSeedSectionsError("Cannot seed sections from an empty Table of Contents.");
        return;
    }
    if (!window.confirm("This will delete all existing sections and create new ones based on the current Table of Contents. Are you sure you want to proceed?")) {
      return;
    }
    setSections([]);
    setSeedSectionsError(null);
    setIsSeedingSections(true);
    setIsDetailedProgressVisible(true);
    setDetailedProgressPercent(0);
    setDetailedProgressCurrentTitle('');
    const callbacks: SeedSectionsCallbacks = {
      onOpen: (event) => {
        console.log("SSE connection opened for seeding sections.", event);
        setIsPageLoading(false);
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
        setSaveSuccess(message || `Sections created successfully! Processed: ${totalProcessed}`);
        setTimeout(() => setSaveSuccess(null), 5000);
        eventSourceRef.current = null;
      },
      onError: (error) => {
        console.error("SSE Error:", error);
        setIsDetailedProgressVisible(false);
        setIsSeedingSections(false);
        setIsPageLoading(false);
        const errorMessage = (error as any)?.message || "An error occurred during section creation.";
        setSeedSectionsError(`SSE Error: ${errorMessage}`);
        eventSourceRef.current = null;
      }
    };
    if (campaignId) {
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
    return () => {
      if (eventSourceRef.current) {
        console.log("Aborting SSE connection on component unmount.");
        eventSourceRef.current();
        eventSourceRef.current = null;
      }
    };
  }, []);

  // useEffect for auto-saving mood board URLs
  useEffect(() => {
    if (!initialLoadCompleteRef.current || !campaignId || !campaign) {
      return;
    }
    if (JSON.stringify(editableMoodBoardUrls) === JSON.stringify(campaign.mood_board_image_urls || [])) {
      return;
    }
    if (moodBoardDebounceTimer) {
      clearTimeout(moodBoardDebounceTimer);
    }
    setIsAutoSavingMoodBoard(true);
    setAutoSaveMoodBoardError(null);
    setAutoSaveMoodBoardSuccess(null);
    const newTimer = setTimeout(async () => {
      if (!campaign || !campaign.id) {
          setIsAutoSavingMoodBoard(false);
          setAutoSaveMoodBoardError("Cannot auto-save mood board: Campaign data not available.");
          return;
      }
      try {
        // console.log('Auto-saving mood board URLs:', editableMoodBoardUrls); // Debug log removed
        const payload: campaignService.CampaignUpdatePayload = {
          mood_board_image_urls: editableMoodBoardUrls,
        };
        const updatedCampaign = await campaignService.updateCampaign(campaign.id, payload);
        setCampaign(updatedCampaign);
        setAutoSaveMoodBoardSuccess("Mood board auto-saved!");
        setTimeout(() => setAutoSaveMoodBoardSuccess(null), 3000);
      } catch (err) {
        console.error("Failed to auto-save mood board URLs:", err);
        setAutoSaveMoodBoardError("Failed to auto-save mood board. Changes might not be persisted.");
      } finally {
        setIsAutoSavingMoodBoard(false);
      }
    }, 1500);
    setMoodBoardDebounceTimer(newTimer);
    return () => {
      if (newTimer) {
        clearTimeout(newTimer);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editableMoodBoardUrls, campaign]); // Corrected dependencies: only what triggers the save. campaignId is in campaign. initialLoadCompleteRef is read directly. Setters are stable.

  // Effect to fetch campaign files when 'Files' tab is active or campaignId changes
  useEffect(() => {
    let isMounted = true;
    // console.log('[FilesEffect] Running. Tab:', activeEditorTab, 'CampaignID:', campaignId); // Removed

    const fetchCampaignFiles = async () => {
      if (!campaignId) {
        // console.log('[FilesEffect] No campaignId, resetting files state.'); // Removed
        if (isMounted) {
          setCampaignFiles([]);
          setCampaignFilesError(null);
          setPrevCampaignIdForFiles(null);
        }
        return;
      }

      if (activeEditorTab !== 'Files') {
        // console.log('[FilesEffect] Not on Files tab, skipping fetch.'); // Removed
        return;
      }

      const campaignChanged = campaignId !== prevCampaignIdForFiles;
      const initialLoadForThisCampaign = campaignFiles.length === 0 && (!campaignFilesError || prevCampaignIdForFiles !== campaignId);
      const shouldRetryAfterError = !!campaignFilesError && prevCampaignIdForFiles === campaignId;

      // console.log(`[FilesEffect] campaignChanged: ${campaignChanged}, initialLoad: ${initialLoadForThisCampaign}, shouldRetry: ${shouldRetryAfterError}, loading: ${campaignFilesLoading}`); // Removed
      // console.log(`[FilesEffect] current campaignFiles.length: ${campaignFiles.length}, campaignFilesError: ${campaignFilesError}, prevCampaignIdForFiles: ${prevCampaignIdForFiles}`); // Removed


      if ((campaignChanged || initialLoadForThisCampaign || shouldRetryAfterError) && !campaignFilesLoading) {
        // console.log(`[FilesEffect] Conditions met to fetch/re-fetch files for campaign ID: ${campaignId}.`); // Removed
        if (isMounted) {
          // console.log('[FilesEffect] Setting loading true.'); // Removed
          setCampaignFilesLoading(true);
          setCampaignFilesError(null);

          if (campaignChanged) {
            // console.log('[FilesEffect] Campaign ID changed. Clearing old files and setting prevCampaignId.'); // Removed
            setCampaignFiles([]);
            setPrevCampaignIdForFiles(campaignId);
          }
        }

        try {
          // console.log(`[FilesEffect] Attempting to fetch files for campaignId: ${campaignId}`); // Removed
          const files = await getCampaignFiles(campaignId);
          // console.log(`[FilesEffect] Successfully fetched files:`, files); // Removed
          if (isMounted) {
            // console.log('[FilesEffect] isMounted true, setting campaign files.'); // Removed
            setCampaignFiles(files);
            if (!campaignChanged) {
                 // console.log('[FilesEffect] Campaign ID did not change, ensuring prevCampaignIdForFiles is set.'); // Removed
                 setPrevCampaignIdForFiles(campaignId);
            }
          } else {
            // console.log('[FilesEffect] Not mounted after fetch, not setting campaign files.'); // Removed
          }
        } catch (err: any) {
          console.error(`[CampaignEditorPage] Error fetching campaign files for ${campaignId}:`, err); // Keep critical error logs
          if (isMounted) {
            // console.log('[FilesEffect] isMounted true, setting campaign files error.'); // Removed
            const errorMsg = err.message || 'Failed to load campaign files.';
            setCampaignFilesError(errorMsg);
          } else {
            // console.log('[FilesEffect] Not mounted after error, not setting campaign files error.'); // Removed
          }
        } finally {
          // console.log('[FilesEffect] Entering finally block.'); // Removed
          if (isMounted) {
            // console.log('[FilesEffect] isMounted true, setting loading false.'); // Removed
            setCampaignFilesLoading(false);
          } else {
            // console.log('[FilesEffect] Not mounted in finally, not setting loading false.'); // Removed
          }
        }
      } else {
        // console.log('[FilesEffect] Conditions not met for fetch or already loading.'); // Removed
      }
    };

    fetchCampaignFiles();

    return () => {
      // console.log('[FilesEffect] Cleanup. Setting isMounted to false for campaignId:', campaignId); // Removed
      isMounted = false;
    };
  }, [
    activeEditorTab, // Re-run if tab changes
    campaignId     // Re-run if campaignId changes
    // prevCampaignIdForFiles, campaignFiles, campaignFilesError, campaignFilesLoading
    // are internal to the effect's logic or set by it, so they should not be dependencies
    // that would cause the effect to cleanup and re-run when they change.
  ]);

  useEffect(() => {
    if (!campaignId) {
      setError('Campaign ID is missing.');
      setIsLoading(false);
      return;
    }
    const fetchInitialData = async () => {
      setIsLoading(true); // For overall page loading
      setError(null);

      // Specifically manage LLM loading state
      setIsLLMsLoading(true);

      try {
        // Fetch all data concurrently
        const [campaignDetails, campaignSectionsResponse, fetchedLLMs] = await Promise.all([
          campaignService.getCampaignById(campaignId),
          campaignService.getCampaignSections(campaignId),
          getAvailableLLMs().finally(() => setIsLLMsLoading(false)) // Set loading false when getAvailableLLMs finishes
        ]);

        setCampaign(campaignDetails);
        setEditableDisplayTOC(campaignDetails.display_toc || []);

        if (Array.isArray(campaignSectionsResponse)) {
            setSections(campaignSectionsResponse.sort((a, b) => a.order - b.order));
        } else {
            console.warn("Campaign sections data (campaignSectionsResponse) was not an array as expected:", campaignSectionsResponse);
            setSections([]);
        }
        setEditableTitle(campaignDetails.title);
        setEditableInitialPrompt(campaignDetails.initial_user_prompt || '');
        setCampaignBadgeImage(campaignDetails.badge_image_url || '');
        if (campaignDetails.temperature !== null && campaignDetails.temperature !== undefined) {
            setTemperature(campaignDetails.temperature);
        } else {
            setTemperature(0.7);
        }
        setAvailableLLMs(fetchedLLMs); // Set LLMs after fetch
        let newSelectedLLMIdToSave: string | null = null;
        setSelectedLLMId(campaignDetails.selected_llm_id || null); // Ensure it's null if backend sends empty or undefined

        if (!campaignDetails.selected_llm_id) { // Only try to set a default if none is set from backend
            const preferredModelIds = ["openai/gpt-4.1-nano", "openai/gpt-3.5-turbo", "openai/gpt-4", "gemini/gemini-pro"];
            let newSelectedLLMId: string | null = null; // Initialize to null
            for (const preferredId of preferredModelIds) {
                const foundModel = fetchedLLMs.find(m => m.id === preferredId);
                if (foundModel) { newSelectedLLMId = foundModel.id; break; }
            }
            if (!newSelectedLLMId) {
                const potentialChatModels = fetchedLLMs.filter(model => model.capabilities && (model.capabilities.includes("chat") || model.capabilities.includes("chat-adaptable")));
                if (potentialChatModels.length > 0) {
                    const firstChatModel = potentialChatModels[0];
                    if (firstChatModel) { newSelectedLLMId = firstChatModel.id; }
                }
            }
            // Removed: if (!newSelectedLLMId && fetchedLLMs.length > 0) { newSelectedLLMId = fetchedLLMs[0].id; }

            if (newSelectedLLMId) {
                setSelectedLLMId(newSelectedLLMId);
                // No need to check !campaignDetails.selected_llm_id again, we are in that block
                newSelectedLLMIdToSave = newSelectedLLMId;
            } else { // If no campaign LLM and no default found
                 setSelectedLLMId(null); // Explicitly set state to null
            }
        }
        // This check should be outside the `if (!campaignDetails.selected_llm_id)` block
        // if we intend to save a default even if one was loaded but then cleared by logic (though current logic doesn't do that)
        // For now, it's correct to only save if `newSelectedLLMIdToSave` was set, meaning a default was chosen AND none was previously set.
        if (newSelectedLLMIdToSave && campaignDetails.id) {
            setIsPageLoading(true);
            setAutoSaveLLMSettingsError(null);
            setAutoSaveLLMSettingsSuccess(null);
            try {
                const updatedCampaign = await campaignService.updateCampaign(campaignDetails.id, {
                    selected_llm_id: newSelectedLLMIdToSave,
                    temperature: temperature,
                });
                setCampaign(updatedCampaign);
                setAutoSaveLLMSettingsSuccess("Default LLM setting automatically saved.");
                setTimeout(() => setAutoSaveLLMSettingsSuccess(null), 3000);
            } catch (err) {
                console.error("Failed to save default LLM settings on initial load:", err);
                setAutoSaveLLMSettingsError("Failed to save default LLM choice. You may need to set it manually in Settings.");
            } finally {
                setIsPageLoading(false);
            }
        }

        // Load thematic image data if available - This part is removed as thematicImageData state is gone.
        // The MoodBoardPanel will directly use campaign.mood_board_image_urls.
        // If the panel should be open by default if there's a thematic image, that logic might need to be re-evaluated
        // based on whether campaign.thematic_image_url itself should cause the mood board to open.
        // For now, let's assume it opens based on user click.
        // if (campaignDetails.thematic_image_url) {
        //   setIsMoodBoardPanelOpen(true); // Example: open if thematic image exists, though this panel shows mood board items
        // }

        // Populate themeData for CampaignThemeEditor
        let currentThemeData: CampaignThemeData = { // Changed to let
          theme_primary_color: campaignDetails.theme_primary_color,
          theme_secondary_color: campaignDetails.theme_secondary_color,
          theme_background_color: campaignDetails.theme_background_color,
          theme_text_color: campaignDetails.theme_text_color,
          theme_font_family: campaignDetails.theme_font_family,
          theme_background_image_url: campaignDetails.theme_background_image_url,
          theme_background_image_opacity: campaignDetails.theme_background_image_opacity,
        };

        // Auto-apply campaign's thematic image to theme background if no theme background is set
        if (campaignDetails.thematic_image_url &&
            (currentThemeData.theme_background_image_url === null ||
             currentThemeData.theme_background_image_url === undefined ||
             currentThemeData.theme_background_image_url === '')) {
          currentThemeData.theme_background_image_url = campaignDetails.thematic_image_url;
          if (currentThemeData.theme_background_image_opacity === null || currentThemeData.theme_background_image_opacity === undefined) {
             currentThemeData.theme_background_image_opacity = 0.5; // Default opacity
          }
        }

        setThemeData(currentThemeData);
        applyThemeToDocument(currentThemeData); // Apply the potentially updated theme

        // Initialize MoodBoard URLs
        setEditableMoodBoardUrls(campaignDetails.mood_board_image_urls || []);

        initialLoadCompleteRef.current = true;
      } catch (err) {
        console.error('Failed to fetch initial campaign or LLM data:', err);
        setError('Failed to load initial data. Please try again later.');
        setIsLLMsLoading(false); // Ensure LLM loading is false on error too
      } finally {
        setIsLoading(false); // Overall page loading finishes
      }
    };
    fetchInitialData();

    // Cleanup function to remove theme when navigating away
    return () => {
      applyThemeToDocument(null); // Or reset to a default app theme
    };
  }, [campaignId]);

  useEffect(() => {
    if (!initialLoadCompleteRef.current || !campaignId || !campaign || isLoading) {
        return;
    }

    // Clear previous timer using the ref
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new timer and store its ID in the ref
    debounceTimerRef.current = setTimeout(async () => {
        if (!campaign || !campaign.id) { return; } // Check campaign again inside timeout
        // Condition to prevent saving if values haven't changed from what's in campaign
        if (selectedLLMId === campaign.selected_llm_id && temperature === campaign.temperature) {
          return;
        }

        console.log('Auto-saving LLM settings due to change in selectedLLMId or temperature.');
        setIsAutoSavingLLMSettings(true);
        setAutoSaveLLMSettingsError(null);
        setAutoSaveLLMSettingsSuccess(null);
        try {
          const payload: campaignService.CampaignUpdatePayload = {
            selected_llm_id: selectedLLMId || null,
            temperature: temperature,
          };
          const updatedCampaign = await campaignService.updateCampaign(campaign.id, payload);
          setCampaign(updatedCampaign); // This will update the campaign state
          setAutoSaveLLMSettingsSuccess("LLM settings auto-saved!");
          setTimeout(() => setAutoSaveLLMSettingsSuccess(null), 3000);
        } catch (err) {
          console.error("Failed to auto-save LLM settings:", err);
          setAutoSaveLLMSettingsError("Failed to auto-save LLM settings.");
          setTimeout(() => setAutoSaveLLMSettingsError(null), 5000);
        } finally {
          setIsAutoSavingLLMSettings(false);
        }
    }, 1500);

    // Cleanup function to clear the timer
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [selectedLLMId, temperature, campaignId, campaign, isLoading, setCampaign, setIsAutoSavingLLMSettings, setAutoSaveLLMSettingsError, setAutoSaveLLMSettingsSuccess]);

  // This useEffect triggers ensureLLMSettingsSaved when selectedLLMId changes after initial load
  useEffect(() => {
    if (initialLoadCompleteRef.current && campaign && selectedLLMId !== campaign.selected_llm_id) {
      ensureLLMSettingsSaved();
    }
  }, [selectedLLMId, campaign, ensureLLMSettingsSaved]);

  // This useEffect triggers ensureLLMSettingsSaved when temperature changes after initial load
  useEffect(() => {
    if (!initialLoadCompleteRef.current || !campaign) { return; }
    // Check if temperature is not null (or undefined) before comparing,
    // and ensure it has actually changed from the campaign's stored temperature.
    if (temperature !== null && temperature !== undefined && temperature !== campaign.temperature) {
      ensureLLMSettingsSaved();
    }
  }, [campaign, ensureLLMSettingsSaved, initialLoadCompleteRef, temperature]); // Added temperature

  // useEffect for auto-saving mood board URLs
  useEffect(() => {
    if (!initialLoadCompleteRef.current || !campaignId || !campaign) {
      return;
    }

    // Prevent saving if the urls haven't actually changed from what's in the campaign state
    if (JSON.stringify(editableMoodBoardUrls) === JSON.stringify(campaign.mood_board_image_urls || [])) {
      return;
    }

    if (moodBoardDebounceTimer) {
      clearTimeout(moodBoardDebounceTimer);
    }

    setIsAutoSavingMoodBoard(true);
    setAutoSaveMoodBoardError(null);
    setAutoSaveMoodBoardSuccess(null);

    const newTimer = setTimeout(async () => {
      if (!campaign || !campaign.id) {
          setIsAutoSavingMoodBoard(false);
          setAutoSaveMoodBoardError("Cannot auto-save mood board: Campaign data not available.");
          return;
      }
      try {
        console.log('Auto-saving mood board URLs:', editableMoodBoardUrls);
        const payload: campaignService.CampaignUpdatePayload = {
          mood_board_image_urls: editableMoodBoardUrls,
        };
        const updatedCampaign = await campaignService.updateCampaign(campaign.id, payload);
        setCampaign(updatedCampaign); // Update the main campaign state

        setAutoSaveMoodBoardSuccess("Mood board auto-saved!");
        setTimeout(() => setAutoSaveMoodBoardSuccess(null), 3000);
      } catch (err) {
        console.error("Failed to auto-save mood board URLs:", err);
        setAutoSaveMoodBoardError("Failed to auto-save mood board. Changes might not be persisted.");
        // Optionally, clear error after some time: setTimeout(() => setAutoSaveMoodBoardError(null), 5000);
      } finally {
        setIsAutoSavingMoodBoard(false);
      }
    }, 1500); // 1.5-second debounce delay

    setMoodBoardDebounceTimer(newTimer);

    return () => {
      if (newTimer) {
        clearTimeout(newTimer);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editableMoodBoardUrls, campaignId, campaign, setCampaign]); // initialLoadCompleteRef.current is not needed as a dep, effect runs when it's true. campaign contains mood_board_image_urls.

  const handleGenerateConceptManually = async () => {
    if (!campaignId || !campaign) {
      setManualConceptError("Campaign data not available.");
      return;
    }
    // Prefer initial_user_prompt if available, otherwise a generic prompt.
    const promptForConcept = campaign.initial_user_prompt || "Generate a compelling concept for this campaign.";

    setIsGeneratingConceptManually(true);
    setManualConceptError(null);
    setSaveSuccess(null); // Clear other save messages

    try {
      // This service function will need to be created in campaignService.ts
      // It will call a new API endpoint (e.g., POST /campaigns/{campaignId}/generate-concept)
      const updatedCampaign = await campaignService.generateCampaignConcept(campaignId, {
        prompt: promptForConcept,
        // Optionally pass selected_llm_id and temperature if the endpoint supports it
        // and if you want to use the campaign's current LLM settings
        model_id_with_prefix: campaign.selected_llm_id || undefined,
        // temperature: campaign.temperature || undefined, // API might use default
      });
      setCampaign(updatedCampaign);
      setEditableConcept(updatedCampaign.concept || ''); // Update editable concept if editor was open
      setSaveSuccess("Campaign concept generated successfully!");
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err: any) {
      console.error("Failed to generate concept manually:", err);
      const detail = err.response?.data?.detail || err.message || "Failed to generate concept.";
      setManualConceptError(detail);
      setTimeout(() => setManualConceptError(null), 5000);
    } finally {
      setIsGeneratingConceptManually(false);
    }
  };

  const handleCancelSeeding = async () => {
    if (eventSourceRef.current) {
      console.log("User cancelled section seeding. Aborting SSE.");
      eventSourceRef.current();
      eventSourceRef.current = null;
    }
    setIsSeedingSections(false);
    setIsDetailedProgressVisible(false);
    setDetailedProgressPercent(0);
    setDetailedProgressCurrentTitle('');
    setSeedSectionsError(null);
    setSaveSuccess("Section seeding cancelled by user.");
    setTimeout(() => setSaveSuccess(null), 3000);
  };

  const handleSaveChanges = async () => {
    if (!campaignId || !campaign) return;

    const moodBoardChanged = JSON.stringify(editableMoodBoardUrls.slice().sort()) !== JSON.stringify((campaign.mood_board_image_urls || []).slice().sort());
    const detailsChanged = editableTitle !== campaign.title ||
                           editableInitialPrompt !== (campaign.initial_user_prompt || '');
    // Include other fields if they are part of this save action, e.g., badge image
    // const badgeChanged = campaignBadgeImage !== (campaign.badge_image_url || '');

    if (!detailsChanged && !moodBoardChanged) { // Adjusted condition
      setSaveSuccess("No changes to save in details or mood board.");
      setTimeout(() => setSaveSuccess(null), 3000);
      return;
    }

    if (!editableTitle.trim()) {
      setSaveError("Title cannot be empty.");
      return;
    }
    setIsPageLoading(true);
    setSaveError(null);
    setSaveSuccess(null);
    try {
      const payload: campaignService.CampaignUpdatePayload = {
        title: editableTitle,
        initial_user_prompt: editableInitialPrompt,
        mood_board_image_urls: editableMoodBoardUrls,
        // Include other updatable fields from CampaignDetailsEditor if necessary
        // For example, if badge_image_url is managed here directly:
        // badge_image_url: campaignBadgeImage || null,
      };
      const updatedCampaign = await campaignService.updateCampaign(campaignId, payload);
      setCampaign(updatedCampaign);
      setEditableTitle(updatedCampaign.title);
      setEditableInitialPrompt(updatedCampaign.initial_user_prompt || '');
      setEditableMoodBoardUrls(updatedCampaign.mood_board_image_urls || []); // Update from response
      // If badge image was part of payload, update its state too:
      // setCampaignBadgeImage(updatedCampaign.badge_image_url || '');
      setSaveSuccess('Campaign details saved successfully!');
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err) {
      setSaveError('Failed to save changes.');
    } finally {
      setIsPageLoading(false);
    }
  };

  const handleUpdateSectionOrder = async (orderedSectionIds: number[]) => {
    if (!campaignId) return;
    const oldSections = [...sections];
    const newSections = orderedSectionIds.map((id, index) => {
      const section = sections.find(s => s.id === id);
      if (!section) throw new Error(`Section with id ${id} not found for reordering.`);
      return { ...section, order: index };
    }).sort((a,b) => a.order - b.order);
    setSections(newSections);
    setIsPageLoading(true);
    try {
      await campaignService.updateCampaignSectionOrder(campaignId, orderedSectionIds);
      setSaveSuccess("Section order saved successfully!");
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (error) {
      console.error("Failed to update section order:", error);
      setError("Failed to save section order. Please try again.");
      setSections(oldSections);
    } finally {
      setIsPageLoading(false);
    }
  };

  const handleBadgeImageGenerated = async (imageUrl: string) => {
    if (!campaign) {
      setBadgeUpdateError("No active campaign to update.");
      return;
    }
    if (!imageUrl || typeof imageUrl !== 'string') {
      setBadgeUpdateError("Invalid image URL received from generation modal.");
      setIsBadgeImageModalOpen(false);
      return;
    }
    setIsPageLoading(true);
    setBadgeUpdateLoading(true);
    setBadgeUpdateError(null);
    setIsBadgeImageModalOpen(false);
    try {
      const updatedCampaignData = { badge_image_url: imageUrl };
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      if (typeof setCampaign === 'function') {
          setCampaign(updatedCampaign);
          setCampaignBadgeImage(updatedCampaign.badge_image_url || '');
      } else {
          console.warn("setCampaign function is not available to update local state.");
      }
    } catch (error: any) {
      console.error("Failed to update badge image URL from modal:", error);
      const detail = error.response?.data?.detail || error.message || "Failed to update badge image from modal.";
      setBadgeUpdateError(detail);
      alert(`Error setting badge: ${detail}`);
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
        model_id_with_prefix: selectedLLMId || undefined,
      });
      setSections(prev => [...prev, newSection].sort((a, b) => a.order - b.order));
      setNewSectionTitle('');
      setNewSectionPrompt('');
      setAddSectionSuccess("New section added successfully!");
      setTimeout(() => setAddSectionSuccess(null), 3000);
    } catch (err: any) {
      console.error('Failed to add new section:', err);
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
    try {
      const updatedSection = await campaignService.updateCampaignSection(campaignId, sectionId, updatedData);
      setSections(prev => prev.map(sec => sec.id === sectionId ? updatedSection : sec));
    } catch (err) {
      console.error(`Error updating section ${sectionId}:`, err);
      setError(`Failed to save section ${sectionId}.`);
      setTimeout(() => setError(null), 5000);
      setIsPageLoading(false);
      throw err;
    } finally {
      setIsPageLoading(false);
    }
  };

  const handleUpdateSectionType = async (sectionId: number, newType: string) => {
    const originalSections = [...sections];
    setSections(prevSections =>
      prevSections.map(s => (s.id === sectionId ? { ...s, type: newType } : s))
    );
    try {
      if (!campaignId) throw new Error("Campaign ID not found");
      await campaignService.updateCampaignSection(campaignId, sectionId, { type: newType });
    } catch (error) {
      console.error("Failed to update section type:", error);
      setSections(originalSections);
      setError(`Failed to update type for section ${sectionId}. Please refresh or try again.`);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleGenerateTOC = async () => {
    if (!campaignId) return;
    if (campaign && campaign.display_toc && campaign.display_toc.length > 0) {
      if (!window.confirm("A Table of Contents already exists. Are you sure you want to regenerate it? This will overwrite the current TOC.")) {
        return;
      }
    }
    setIsPageLoading(true);
    setIsGeneratingTOC(true);
    setTocError(null);
    setSaveSuccess(null);
    try {
      const updatedCampaign = await campaignService.generateCampaignTOC(campaignId, {
        prompt: "Generate a table of contents for the campaign based on its concept."
      });
      setCampaign(updatedCampaign);
      setEditableDisplayTOC(updatedCampaign.display_toc || []);
      setSaveSuccess("Table of Contents generated successfully!");
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err) {
      setTocError('Failed to generate Table of Contents.');
    } finally {
      setIsGeneratingTOC(false);
      setIsPageLoading(false);
    }
  };

  const handleTOCEditorChange = (newTOC: TOCEntry[]) => {
    setEditableDisplayTOC(newTOC);
  };

  const handleTOCSaveChanges = async () => {
    if (!campaignId || !campaign) return;
    setIsSavingTOC(true);
    setTocSaveError(null);
    setTocSaveSuccess(null);
    try {
      const payload: campaignService.CampaignUpdatePayload = {
        display_toc: editableDisplayTOC,
        // homebrewery_toc is intentionally omitted to prevent accidental overwrite
        // when only display_toc is being edited.
      };
      const updatedCampaign = await campaignService.updateCampaign(campaignId, payload);
      setCampaign(updatedCampaign);
      setEditableDisplayTOC(updatedCampaign.display_toc || []);
      setTocSaveSuccess('Table of Contents saved successfully!');
      setTimeout(() => setTocSaveSuccess(null), 3000);
      setIsTOCEditorVisible(false); // Hide editor on successful save
    } catch (err) {
      console.error("Failed to save TOC:", err);
      setTocSaveError('Failed to save Table of Contents.');
      setTimeout(() => setTocSaveError(null), 5000);
    } finally {
      setIsSavingTOC(false);
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
      const response = await campaignService.generateCampaignTitles(campaignId, {
        prompt: "Generate alternative titles for the campaign."
      }, 5);
      setSuggestedTitles(response.titles);
      setIsSuggestedTitlesModalOpen(true);
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
  };

  const handleExportHomebrewery = async () => {
    if (!campaignId || !campaign) return;
    setIsPageLoading(true);
    setIsExporting(true);
    setExportError(null);
    setSaveSuccess(null);
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
      setTimeout(() => setExportError(null), 5000);
    } finally {
      setIsExporting(false);
      setIsPageLoading(false);
    }
  };

  const handleOpenBadgeImageModal = async () => {
    if (!campaign) return;
    setIsBadgeImageModalOpen(true);
  };

  const handleEditBadgeImageUrl = async () => {
    if (!campaign) return;
    const currentUrl = campaign.badge_image_url || "";
    const imageUrl = window.prompt("Enter or edit the image URL for the campaign badge:", currentUrl);
    if (imageUrl === null) return;
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
          setCampaignBadgeImage(updatedCampaign.badge_image_url || '');
      } else {
          console.warn("setCampaign function is not available to update local state.");
      }
    } catch (error: any) {
      console.error("Failed to update badge image URL via edit:", error);
      const detail = error.response?.data?.detail || error.message || "Failed to update badge image URL.";
      setBadgeUpdateError(detail);
      alert(`Error setting badge: ${detail}`);
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
      const updatedCampaignData = { badge_image_url: null };
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      if (typeof setCampaign === 'function') {
          setCampaign(updatedCampaign);
          setCampaignBadgeImage('');
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

  const handleThemeDataChange = (newThemeData: CampaignThemeData) => {
    setThemeData(newThemeData);
  };

  const handleSaveTheme = async () => {
    if (!campaignId || !campaign) return;
    setIsSavingTheme(true);
    setThemeSaveError(null);
    setThemeSaveSuccess(null);
    try {
      const themePayloadToSave: Partial<campaignService.CampaignUpdatePayload> = {};
      (Object.keys(themeData) as Array<keyof CampaignThemeData>).forEach(key => {
        if (themeData[key] !== undefined) {
          (themePayloadToSave as any)[key] = themeData[key];
        }
      });

      const updatedCampaign = await campaignService.updateCampaign(campaignId, themePayloadToSave);
      setCampaign(updatedCampaign); // Update the main campaign state
      const newThemeData: CampaignThemeData = { // Re-set themeData from the response
          theme_primary_color: updatedCampaign.theme_primary_color,
          theme_secondary_color: updatedCampaign.theme_secondary_color,
          theme_background_color: updatedCampaign.theme_background_color,
          theme_text_color: updatedCampaign.theme_text_color,
          theme_font_family: updatedCampaign.theme_font_family,
          theme_background_image_url: updatedCampaign.theme_background_image_url,
          theme_background_image_opacity: updatedCampaign.theme_background_image_opacity,
      };
      setThemeData(newThemeData);
      applyThemeToDocument(newThemeData); // APPLY THEME ON SAVE
      setThemeSaveSuccess('Theme settings saved successfully!');
      setTimeout(() => setThemeSaveSuccess(null), 3000);
    } catch (err) {
      setThemeSaveError('Failed to save theme settings.');
      console.error("Failed to save theme:", err);
      setTimeout(() => setThemeSaveError(null), 5000);
    } finally {
      setIsSavingTheme(false);
    }
  };

  const TocLinkRenderer = (props: any) => {
    const { href, children } = props;
    // href will be like "#section-container-123"
    const sectionId = href && href.startsWith('#') ? href.substring(1) : null;

    if (sectionId) {
      return (
        <a
          href={`#${sectionId}`} // Keep for right-click context menu, but prevent default click
          onClick={(e) => {
            e.preventDefault();
            handleTocLinkClick(sectionId);
          }}
          style={{ cursor: 'pointer' }}
        >
          {children}
        </a>
      );
    }
    // Fallback for non-section links if any (though TOC should only have section links)
    return <a href={href}>{children}</a>;
  };

  if (isLoading) return <LoadingSpinner />;
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
        onSuggestTitles={handleGenerateTitles}
        isGeneratingTitles={isGeneratingTitles}
        titlesError={titlesError}
        selectedLLMId={selectedLLMId}
        originalTitle={campaign.title}
        originalInitialPrompt={campaign.initial_user_prompt || ''}
        originalBadgeImageUrl={campaign.badge_image_url || ''}
        onOpenBadgeImageModal={handleOpenBadgeImageModal}
        onEditBadgeImageUrl={handleEditBadgeImageUrl}
        onRemoveBadgeImage={handleRemoveBadgeImage}
        badgeUpdateLoading={badgeUpdateLoading}
        badgeUpdateError={badgeUpdateError}
        // Mood Board Props
        editableMoodBoardUrls={editableMoodBoardUrls}
        // setEditableMoodBoardUrls={setEditableMoodBoardUrls} // Removed as CampaignDetailsEditor no longer uses it directly
        originalMoodBoardUrls={campaign?.mood_board_image_urls || []}
      />
      {saveError && <p className="error-message save-feedback">{saveError}</p>}
      {saveSuccess && <p className="success-message save-feedback">{saveSuccess}</p>}
      <section className="campaign-detail-section editor-section">
        {campaign.display_toc && (
          <h2 onClick={() => setIsTocCollapsed(!isTocCollapsed)} style={{ cursor: 'pointer' }}>
            {isTocCollapsed ? '▶' : '▼'} Table of Contents Display
          </h2>
        )}
        {(!campaign.display_toc || !isTocCollapsed) && (
          <div className="toc-controls-and-display" style={{ marginTop: '10px' }}>
            {campaign.display_toc && campaign.display_toc.length > 0 && (
              <ReactMarkdown
                components={{ a: TocLinkRenderer }}
              >
                {processedToc}
              </ReactMarkdown>
            )}
            {(!campaign.display_toc || campaign.display_toc.length === 0) && <p>No Table of Contents generated yet.</p>}
            <Button
              onClick={handleGenerateTOC}
              disabled={isGeneratingTOC || !selectedLLMId}
              className="action-button"
              style={{ marginTop: (campaign.display_toc && campaign.display_toc.length > 0) ? '10px' : '0' }}
              icon={<ListAltIcon />}
              tooltip={!selectedLLMId ? "Select an LLM model from the Settings tab first" : "Generate or re-generate the Table of Contents based on the campaign concept and sections"}
            >
              {isGeneratingTOC ? 'Generating TOC...' : ((campaign.display_toc && campaign.display_toc.length > 0) ? 'Re-generate Table of Contents' : 'Generate Table of Contents')}
            </Button>
            {tocError && <p className="error-message feedback-message" style={{ marginTop: '5px' }}>{tocError}</p>}

            {/* NEW "Edit Table of Contents" button */}
            {campaign.display_toc && campaign.display_toc.length > 0 && !isTOCEditorVisible && (
              <Button
                onClick={() => setIsTOCEditorVisible(true)}
                className="action-button"
                icon={<EditIcon />}
                style={{ marginTop: '10px', display: 'block', marginBottom: '15px' }}
                tooltip="Edit the Table of Contents entries"
              >
                Edit Table of Contents
              </Button>
            )}

            {(campaign.display_toc && campaign.display_toc.length > 0) && (
              <div style={{ marginTop: '15px' }}>
                {!isDetailedProgressVisible ? (
                  <>
                    <Button
                      onClick={handleSeedSectionsFromToc}
                      disabled={isSeedingSections || !(campaign.display_toc && campaign.display_toc.length > 0) }
                      className="action-button"
                      icon={<AddCircleOutlineIcon />}
                      tooltip="Parse the current Table of Contents and create campaign sections based on its structure. Optionally auto-populate content."
                    >
                      {isSeedingSections ? (autoPopulateSections ? 'Creating & Populating Sections...' : 'Creating Sections...') : 'Approve TOC & Create Sections'}
                    </Button>
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
                  <>
                    <DetailedProgressDisplay
                      percent={detailedProgressPercent}
                      currentTitle={detailedProgressCurrentTitle}
                      error={seedSectionsError}
                      title="Seeding Sections from Table of Contents..."
                    />
                    <Button
                      onClick={handleCancelSeeding}
                      className="action-button secondary-action-button"
                      style={{ marginTop: '10px' }}
                      icon={<CancelIcon />}
                      tooltip="Stop the section seeding process"
                      disabled={!isSeedingSections}
                    >
                      Cancel Seeding
                    </Button>
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </section>
      {isTOCEditorVisible && (
        <section className="campaign-detail-section editor-section" style={{ marginTop: '20px' }}>
          <TOCEditor
            toc={editableDisplayTOC}
            onTOCChange={handleTOCEditorChange}
          />
          <Button
            onClick={handleTOCSaveChanges}
            disabled={isSavingTOC}
            variant="primary"
            style={{ marginTop: '10px' }}
          >
            {isSavingTOC ? 'Saving TOC...' : 'Save Table of Contents Changes'}
          </Button>
          <Button
              onClick={() => setIsTOCEditorVisible(false)}
              variant="secondary" // Corrected variant
              style={{ marginTop: '10px', marginLeft: '10px' }}
          >
              Done Editing TOC
          </Button>
        </section>
      )}
    {/* Moved messages START */}
    {tocSaveError && <p className="error-message feedback-message">{tocSaveError}</p>}
    {tocSaveSuccess && <p className="success-message feedback-message">{tocSaveSuccess}</p>}
    {/* Moved messages END */}
      <div className="action-group export-action-group editor-section">
        <Button onClick={handleExportHomebrewery} disabled={isExporting} className="llm-button export-button" icon={<PublishIcon />} tooltip="Export the campaign content as Markdown formatted for Homebrewery">
          {isExporting ? 'Exporting...' : 'Export to Homebrewery'}
        </Button>
        {exportError && <p className="error-message llm-feedback">{exportError}</p>}
      </div>
    </>
  );

  const sectionsTabContent = (
    <>
      <div className="section-display-controls editor-section">
        <h3>Section Display</h3>
        <Button onClick={() => setForceCollapseAll(true)} className="action-button" icon={<UnfoldLessIcon />} tooltip="Collapse all campaign sections">
          Collapse All Sections
        </Button>
        <Button onClick={() => setForceCollapseAll(false)} className="action-button" icon={<UnfoldMoreIcon />} tooltip="Expand all campaign sections">
          Expand All Sections
        </Button>
        <Button
          onClick={() => setIsAddSectionCollapsed(!isAddSectionCollapsed)}
          disabled={!campaign?.concept?.trim()}
          className="action-button"
          icon={<AddCircleOutlineIcon />}
          tooltip={!campaign?.concept?.trim() ? "Please define and save a campaign concept first." : "Add a new section to the campaign"}
        >
          Add New Section
        </Button>
      </div>
      {!isAddSectionCollapsed && campaign?.concept?.trim() && (
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
            <Button type="submit" disabled={isAddingSection || !selectedLLMId || !campaign?.concept?.trim()} className="action-button add-section-button" icon={<AddCircleOutlineIcon />} tooltip={!campaign?.concept?.trim() ? "Please define and save a campaign concept first." : (!selectedLLMId ? "Please select an LLM in settings." : "Add this new section to the campaign")}>
              {isAddingSection ? 'Adding Section...' : 'Confirm & Add Section'}
            </Button>
            <Button type="button" onClick={() => setIsAddSectionCollapsed(true)} className="action-button secondary-action-button" style={{marginLeft: '10px'}} icon={<CancelIcon />} tooltip="Cancel adding a new section">
              Cancel
            </Button>
          </form>
        </div>
      )}
      <CampaignSectionEditor
        campaignId={campaignId!}
        sections={sections}
        setSections={setSections}
        handleDeleteSection={handleDeleteSection}
        handleUpdateSectionContent={handleUpdateSectionContent}
        handleUpdateSectionTitle={handleUpdateSectionTitle}
        handleUpdateSectionType={handleUpdateSectionType}
        onUpdateSectionOrder={handleUpdateSectionOrder}
        forceCollapseAllSections={forceCollapseAll}
        expandSectionId={sectionToExpand} // Add this new prop
        onSetThematicImageForSection={handleSetThematicImage}
      />
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
      {isLLMsLoading ? (
        <div className="editor-section" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
          <LoadingSpinner />
          <Typography sx={{ ml: 2 }}>Loading LLM models...</Typography>
        </div>
      ) : selectedLLMObject && availableLLMs.length > 0 ? (
        <CampaignLLMSettings
          selectedLLM={selectedLLMObject}
          setSelectedLLM={handleSetSelectedLLM}
          temperature={temperature}
          setTemperature={setTemperature}
          availableLLMs={availableLLMs.map(m => ({...m, name: m.name || m.id})) as LLM[]}
        />
      ) : !selectedLLMObject && availableLLMs.length > 0 ? (
        <div className="editor-section">
          <p>No LLM model currently selected for the campaign.</p>
          <Button onClick={() => setIsLLMDialogOpen(true)} className="action-button" icon={<SettingsSuggestIcon />} tooltip="Select the primary Language Model for campaign generation tasks">
            Select LLM Model
          </Button>
        </div>
      ) : ( // This covers availableLLMs.length === 0 && !isLLMsLoading
        <div className="editor-section">
          <Typography>No LLM models available. Please check LLM provider configurations.</Typography>
        </div>
      )}
      <div className="llm-autosave-feedback editor-section feedback-messages">
        {isAutoSavingLLMSettings && <p className="feedback-message saving-indicator">Auto-saving LLM settings...</p>}
        {autoSaveLLMSettingsError && <p className="error-message feedback-message">{autoSaveLLMSettingsError}</p>}
        {autoSaveLLMSettingsSuccess && <p className="success-message feedback-message">{autoSaveLLMSettingsSuccess}</p>}
      </div>
      {tocError && <p className="error-message llm-feedback editor-section">{tocError}</p>}
    </>
  );

  // Placeholder for Files tab content
  const filesTabContent = (
    <div className="editor-section">
      <Typography variant="h5" gutterBottom>Campaign Files</Typography>
      {campaignFilesLoading && <LoadingSpinner />}
      {campaignFilesError && <p className="error-message">{campaignFilesError}</p>}
      {!campaignFilesLoading && !campaignFilesError && campaignFiles.length === 0 && (
        <p>No files found for this campaign.</p>
      )}
      {!campaignFilesLoading && !campaignFilesError && campaignFiles.length > 0 && (
        <ul style={{ listStyleType: 'none', paddingLeft: 0 }}>
          {campaignFiles.map(file => {
            const extension = file.name.split('.').pop()?.toLowerCase() || '';
            const isImage = ['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(extension);
            const displayType = extension.toUpperCase();

            return (
              <li key={file.name} style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                {isImage ? (
                  <img
                    src={file.url}
                    alt={file.name}
                    style={{
                      width: '30px',
                      height: '30px',
                      objectFit: 'contain',
                      marginRight: '10px',
                      border: '1px solid #eee',
                      cursor: 'pointer' // Add cursor pointer for clickable images
                    }}
                    onClick={() => {
                      setPreviewImageUrl(file.url);
                      setIsPreviewModalOpen(true);
                    }}
                  />
                ) : (
                  <span
                    style={{
                      display: 'inline-block',
                      width: '30px',
                      height: '30px',
                      marginRight: '10px',
                      border: '1px solid #eee',
                      backgroundColor: '#f0f0f0',
                      textAlign: 'center',
                      lineHeight: '30px',
                      fontSize: '10px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    title={displayType}
                  >
                    {displayType || 'FILE'}
                  </span>
                )}
                <a href={file.url} target="_blank" rel="noopener noreferrer">{file.name}</a>
                <span style={{ marginLeft: '8px', fontSize: '0.8em', color: '#777' }}>({(file.size / 1024).toFixed(2)} KB)</span>
                {/* Basic Delete Button - Functionality to be added */}
                <Button
                  onClick={async () => {
                    // Confirmation dialog
                    if (window.confirm(`Are you sure you want to delete "${file.name}"? This action cannot be undone.`)) {
                      try {
                        if (!campaignId) {
                          console.error("Campaign ID is missing, cannot delete file.");
                          setCampaignFilesError("Campaign ID is missing, cannot delete file.");
                          return;
                        }
                        // console.log(`Attempting to delete file: ${file.blob_name} for campaign ${campaignId}`); // Changed file.name to file.blob_name
                        await campaignService.deleteCampaignFile(campaignId, file.blob_name); // Use file.blob_name
                        // console.log(`File "${file.blob_name}" deleted successfully from backend.`); // Changed file.name to file.blob_name
                        // Refresh file list or remove from local state
                        setCampaignFiles(prevFiles => prevFiles.filter(f => f.blob_name !== file.blob_name)); // Use blob_name for filtering
                        // console.log("Local file list updated."); // Removed
                      } catch (err: any) {
                        console.error(`Failed to delete file "${file.name}":`, err);
                        setCampaignFilesError(`Failed to delete ${file.name}: ${err.message || 'Unknown error'}`);
                        // Optionally, clear the error after some time
                        // setTimeout(() => setCampaignFilesError(null), 5000);
                      }
                    }
                  }}
                  variant="danger"
                  size="sm"
                  style={{ marginLeft: 'auto', padding: '2px 6px' }} // Pushes button to the right, minimal padding
                  tooltip={`Delete ${file.name}`}
                >
                  Delete
                </Button>
              </li>
            );
          })}
        </ul>
      )}
      {/* TODO: Add UI for file upload/management */}
    </div>
  );

  const tabItems: TabItem[] = [
    { name: 'Details', content: detailsTabContent },
    { name: 'Sections', content: sectionsTabContent, disabled: !campaign?.concept?.trim() },
    {
      name: 'Theme',
      content: (
        <CampaignThemeEditor
          themeData={themeData}
          onThemeDataChange={handleThemeDataChange}
          onSaveTheme={handleSaveTheme}
          isSaving={isSavingTheme}
          saveError={themeSaveError}
          saveSuccess={themeSaveSuccess}
          currentThematicImageUrl={campaign?.thematic_image_url} // Pass it here
        />
      )
    },
    { name: 'Settings', content: settingsTabContent },
    { name: 'Files', content: filesTabContent }, // Added Files tab
  ];

  return (
    <div className="campaign-editor-page">
      {isPageLoading && <LoadingSpinner />}
      <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'flex-end', paddingRight: '1rem' }}>
        <Button
          onClick={() => setIsMoodBoardPanelOpen(!isMoodBoardPanelOpen)}
          icon={<ImageIcon />}
          tooltip={isMoodBoardPanelOpen ? 'Hide Mood Board Panel' : 'Show Mood Board Panel'}
          variant="outline-secondary"
        >
          {isMoodBoardPanelOpen ? 'Hide Mood Board' : 'Show Mood Board'}
        </Button>
        {/* Example Auto-save feedback display area */}
        {isAutoSavingMoodBoard && <p className="feedback-message saving-indicator" style={{marginRight: '10px', fontSize: '0.8em'}}>Auto-saving mood board...</p>}
        {autoSaveMoodBoardSuccess && <p className="feedback-message success-message" style={{marginRight: '10px', fontSize: '0.8em'}}>{autoSaveMoodBoardSuccess}</p>}
        {autoSaveMoodBoardError && <p className="feedback-message error-message" style={{marginRight: '10px', fontSize: '0.8em'}}>{autoSaveMoodBoardError}</p>}
      </div>
      {campaign && campaign.title && (
        <h1 className="campaign-main-title">{campaign.title}</h1>
      )}

      {/* Manual Concept Generation Button Area */}
      {campaign && !campaign.concept && !isConceptEditorVisible && (
        <section className="campaign-detail-section editor-section page-level-concept generate-concept-area">
          <Typography variant="body1" sx={{ mb: 1 }}>
            This campaign does not have an AI-generated concept yet.
          </Typography>
          <Button
            onClick={handleGenerateConceptManually}
            disabled={isGeneratingConceptManually || !campaign.selected_llm_id}
            variant="primary"
            icon={<SettingsSuggestIcon />}
            tooltip={!campaign.selected_llm_id ? "Select an LLM model from the Settings tab first" : "Generate the campaign concept using AI"}
          >
            {isGeneratingConceptManually ? 'Generating Concept...' : 'Generate Campaign Concept'}
          </Button>
          {manualConceptError && <p className="error-message feedback-message" style={{ marginTop: '10px' }}>{manualConceptError}</p>}
        </section>
      )}

      {campaign && campaign.concept && !isConceptEditorVisible && (
        <section className="campaign-detail-section read-only-section editor-section page-level-concept">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 onClick={() => setIsCampaignConceptCollapsed(!isCampaignConceptCollapsed)} style={{ cursor: 'pointer', marginBottom: '0.5rem' }}>
              {isCampaignConceptCollapsed ? '▶' : '▼'} Campaign Concept
            </h2>
            <Button
              onClick={() => {
                setEditableConcept(campaign.concept || '');
                setIsConceptEditorVisible(true);
                setIsCampaignConceptCollapsed(false); // Ensure section is expanded
                setConceptSaveError(null);
                setConceptSaveSuccess(null);
              }}
              icon={<EditIcon />}
              style={{minWidth: 'auto', padding: '4px', marginLeft: '10px'}}
              tooltip="Edit Campaign Concept"
            >
              Edit
            </Button>
          </div>
          {!isCampaignConceptCollapsed && (
            <div className="concept-content">
              <ReactMarkdown>{campaign.concept}</ReactMarkdown>
            </div>
          )}
        </section>
      )}

      {isConceptEditorVisible && campaign && (
        <section className="campaign-detail-section editor-section page-level-concept edit-concept-section card-like">
          <h2>Edit Campaign Concept</h2>
          <TextField
            label="Campaign Concept"
            multiline
            rows={6}
            fullWidth
            value={editableConcept}
            onChange={(e) => setEditableConcept(e.target.value)}
            variant="outlined"
            margin="normal"
            helperText={conceptSaveError ? conceptSaveError : (conceptSaveSuccess ? conceptSaveSuccess : "Enter the core concept for your campaign.")}
            error={!!conceptSaveError}
            sx={{
                '& .MuiFormHelperText-root': {
                    color: conceptSaveError ? 'error.main' : (conceptSaveSuccess ? 'success.main' : 'text.secondary'),
                },
            }}
          />
          <div className="action-group" style={{ marginTop: '10px', display: 'flex', gap: '10px' }}>
            <Button
              onClick={async () => {
                if (!campaignId || !campaign) return;
                setIsPageLoading(true);
                setConceptSaveError(null);
                setConceptSaveSuccess(null);
                try {
                  const updatedCampaign = await campaignService.updateCampaign(campaignId, { concept: editableConcept });
                  setCampaign(updatedCampaign);
                  setConceptSaveSuccess("Campaign concept updated successfully!");
                  setTimeout(() => setConceptSaveSuccess(null), 3000);
                  setIsConceptEditorVisible(false);
                } catch (err) {
                  console.error("Failed to save concept:", err);
                  setConceptSaveError("Failed to save concept. Please try again.");
                  setTimeout(() => setConceptSaveError(null), 5000);
                } finally {
                  setIsPageLoading(false);
                }
              }}
              variant="primary"
              icon={<SaveIcon />}
              disabled={isPageLoading || editableConcept === campaign.concept}
            >
              Save Concept
            </Button>
            <Button
              onClick={() => {
                setIsConceptEditorVisible(false);
                setConceptSaveError(null); // Clear any previous errors
                // editableConcept doesn't need reset, will be re-init on next open
              }}
              variant="secondary"
              icon={<CancelIcon />}
              disabled={isPageLoading}
            >
              Cancel
            </Button>
          </div>
        </section>
      )}

      <Tabs
        tabs={tabItems}
        activeTabName={activeEditorTab}
        onTabChange={setActiveEditorTab}
      />
      {isMoodBoardPanelOpen && (
        <div
          className="mood-board-side-panel"
          style={{ width: `${moodBoardPanelWidth}px` }} // Apply dynamic width
        >
          {/* Close button is now part of MoodBoardPanel's internal structure if desired, or keep here */}
          {/* For simplicity, MoodBoardPanel's onClose is used */}
          <MoodBoardPanel
            moodBoardUrls={editableMoodBoardUrls} // Use the state variable
            isLoading={false} // Moodboard URLs are part of campaign data
            error={null}    // Errors for mood board fetching not handled here
            isVisible={isMoodBoardPanelOpen}
            onClose={() => setIsMoodBoardPanelOpen(false)}
            title="Mood Board"
            onUpdateMoodBoardUrls={setEditableMoodBoardUrls} // Pass the state setter
            campaignId={campaignId!} // Pass campaignId to MoodBoardPanel
            onRequestOpenGenerateImageModal={() => setIsGeneratingForMoodBoard(true)} // New callback
            // Add these lines:
            currentPanelWidth={moodBoardPanelWidth}
            onResize={handleMoodBoardResize}
          />
        </div>
      )}
      <LLMSelectionDialog
        isOpen={isLLMDialogOpen}
        currentModelId={selectedLLMId}
        onModelSelect={(modelId) => {
          if (modelId !== null) { setSelectedLLMId(modelId); }
          setIsLLMDialogOpen(false);
        }}
        onClose={() => setIsLLMDialogOpen(false)}
      />
      <ImageGenerationModal
        isOpen={isBadgeImageModalOpen}
        onClose={() => setIsBadgeImageModalOpen(false)}
        onImageSuccessfullyGenerated={handleBadgeImageGenerated}
        onSetAsThematic={handleSetThematicImage}
        primaryActionText="Set as Badge Image"
        autoApplyDefault={true}
        campaignId={campaignId} // Pass campaignId
      />
      <SuggestedTitlesModal
        isOpen={isSuggestedTitlesModalOpen}
        onClose={() => { setIsSuggestedTitlesModalOpen(false); }}
        titles={suggestedTitles || []}
        onSelectTitle={handleTitleSelected}
      />
      {/* New ImageGenerationModal for MoodBoard */}
      <ImageGenerationModal
        isOpen={isGeneratingForMoodBoard}
        onClose={() => setIsGeneratingForMoodBoard(false)}
        onImageSuccessfullyGenerated={(imageUrl, promptUsed) => {
          setEditableMoodBoardUrls(prevUrls => [...prevUrls, imageUrl]);
          // Optionally, log or show success for adding to mood board
          console.log("Image generated and added to mood board:", imageUrl, "Prompt used:", promptUsed);
          setIsGeneratingForMoodBoard(false); // Close this modal
        }}
        onSetAsThematic={() => {
          // This modal instance is for mood board, not main thematic image.
          // Could potentially offer to set as thematic as a secondary action,
          // but for now, it's a no-op in this context.
          console.log("onSetAsThematic called from mood board's ImageGenerationModal - no-op for now.");
        }}
        primaryActionText="Add to Mood Board" // Customize text for this instance
        autoApplyDefault={true} // Assume adding to mood board is the default desired action
        campaignId={campaignId} // Pass campaignId
        // selectedLLMId={selectedLLMId} // If the modal needs LLM context (check modal props)
      />
      <ImagePreviewModal
        isOpen={isPreviewModalOpen}
        onClose={() => setIsPreviewModalOpen(false)}
        imageUrl={previewImageUrl}
      />
    </div>
  );
};
export default CampaignEditorPage;

// Note: The redundant LLMModel type alias (campaignService.ModelInfo) was already addressed by using LLMModel from llmService.
// Removed generateNavLinksFromToc function
// Ensured handleUpdateSectionType is defined and passed correctly
// Ensured TOC existence check in handleGenerateTOC uses .length
// Ensured ensureLLMSettingsSaved is wrapped in useCallback and dependencies are correct for useEffects calling it.
// Corrected error message in handleSaveChanges.
// Added TOCEditor and related state/handlers.
// Initialized editableDisplayTOC in useEffect and handleGenerateTOC.
// Changed type of campaign and sections state variables to use direct imports.
// Added EditIcon import and "Edit Table of Contents" button with conditional rendering.
// Conditionally render TOCEditor section and added "Done Editing TOC" button.
    // Note: For the moodBoardDebounceTimer useEffect (around line 572 in original request, now ~line 600),
    // adding moodBoardDebounceTimer to its own dependency array would cause an infinite loop.
    // The current dependencies [editableMoodBoardUrls, campaignId, campaign, setCampaign] are correct
    // for triggering the debounce logic. The timer ID itself is an implementation detail managed by the effect.
    // No change will be made to that dependency array based on this understanding.
