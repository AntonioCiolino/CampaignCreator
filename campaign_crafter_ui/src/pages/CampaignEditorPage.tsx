import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'; // FormEvent already removed by previous step, this ensures it.
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import LoadingSpinner from '../components/common/LoadingSpinner';
import LLMSelectionDialog from '../components/modals/LLMSelectionDialog';
import ImageGenerationModal from '../components/modals/ImageGenerationModal/ImageGenerationModal';
import SuggestedTitlesModal from '../components/modals/SuggestedTitlesModal';
import AddSectionModal from '../components/modals/AddSectionModal'; // Import AddSectionModal
import * as campaignService from '../services/campaignService';
import { getCampaignFiles } from '../services/campaignService';
import {
    Campaign,
    CampaignSection,
    TOCEntry,
    SeedSectionsProgressEvent,
    SeedSectionsCallbacks,
    CampaignUpdatePayload, // Direct import
    CampaignSectionUpdatePayload, // Direct import for handleUpdateSection
    CampaignSectionCreatePayload
} from '../types/campaignTypes';
import { getAvailableLLMs, LLMModel } from '../services/llmService';
import ReactMarkdown from 'react-markdown';
import './CampaignEditorPage.css';
import Button from '../components/common/Button';
import ImagePreviewModal from '../components/modals/ImagePreviewModal';

import ListAltIcon from '@mui/icons-material/ListAlt';
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore';
import UnfoldLessIcon from '@mui/icons-material/UnfoldLess';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import CancelIcon from '@mui/icons-material/Cancel';
import SettingsSuggestIcon from '@mui/icons-material/SettingsSuggest';
import PublishIcon from '@mui/icons-material/Publish';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import ImageIcon from '@mui/icons-material/Image';
import MoodBoardPanel from '../components/common/MoodBoardPanel';

import CampaignDetailsEditor from '../components/campaign_editor/CampaignDetailsEditor';
import CampaignLLMSettings from '../components/campaign_editor/CampaignLLMSettings';
import CampaignSectionEditor from '../components/campaign_editor/CampaignSectionEditor';
import { LLMModel as LLM } from '../services/llmService';
import Tabs, { TabItem } from '../components/common/Tabs';
import { Typography, TextField, List, ListItem, ListItemAvatar, Avatar, ListItemText, IconButton, Box, FormControl, InputLabel, Select, MenuItem, Paper, Divider } from '@mui/material';
import LinkOffIcon from '@mui/icons-material/LinkOff';
import DetailedProgressDisplay from '../components/common/DetailedProgressDisplay';
import TOCEditor from '../components/campaign_editor/TOCEditor';
import CampaignThemeEditor, { CampaignThemeData } from '../components/campaign_editor/CampaignThemeEditor';
import { applyThemeToDocument } from '../utils/themeUtils';
import { BlobFileMetadata } from '../types/fileTypes';
import * as characterService from '../services/characterService';
import { Character as FrontendCharacter } from '../types/characterTypes';

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

  // const [isAddingSection, setIsAddingSection] = useState<boolean>(false); // Removed as not used in JSX
  // const [addSectionError, setAddSectionError] = useState<string | null>(null); // Removed as not used in JSX
  // const [addSectionSuccess, setAddSectionSuccess] = useState<string | null>(null); // Removed as not used in JSX

  const [availableLLMs, setAvailableLLMs] = useState<LLMModel[]>([]);
  const [isLLMsLoading, setIsLLMsLoading] = useState<boolean>(true);
  const [selectedLLMId, setSelectedLLMId] = useState<string | null>(null);
  const [temperature, setTemperature] = useState<number>(0.7);

  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const [forceCollapseAll, setForceCollapseAll] = useState<boolean>(true); // Initialize to true

  const [isCampaignConceptCollapsed, setIsCampaignConceptCollapsed] = useState<boolean>(true);
  const [isTocCollapsed, setIsTocCollapsed] = useState<boolean>(false);
  const [isLLMDialogOpen, setIsLLMDialogOpen] = useState<boolean>(false);
  const [isBadgeImageModalOpen, setIsBadgeImageModalOpen] = useState(false);
  const [isSuggestedTitlesModalOpen, setIsSuggestedTitlesModalOpen] = useState<boolean>(false);
  const [isAddSectionModalOpen, setIsAddSectionModalOpen] = useState<boolean>(false); // State for AddSectionModal

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

  const [isConceptEditorVisible, setIsConceptEditorVisible] = useState<boolean>(false);
  const [editableConcept, setEditableConcept] = useState<string>('');
  const [conceptSaveError, setConceptSaveError] = useState<string | null>(null);
  const [conceptSaveSuccess, setConceptSaveSuccess] = useState<string | null>(null);

  const [isMoodBoardPanelOpen, setIsMoodBoardPanelOpen] = useState<boolean>(false);
  const [themeData, setThemeData] = useState<CampaignThemeData>({});
  const [isSavingTheme, setIsSavingTheme] = useState<boolean>(false);
  const [editableMoodBoardUrls, setEditableMoodBoardUrls] = useState<string[]>([]);
  const [themeSaveError, setThemeSaveError] = useState<string | null>(null);
  const [themeSaveSuccess, setThemeSaveSuccess] = useState<string | null>(null);

  const [moodBoardDebounceTimer, setMoodBoardDebounceTimer] = useState<NodeJS.Timeout | null>(null);
  const [isAutoSavingMoodBoard, setIsAutoSavingMoodBoard] = useState(false);
  const [autoSaveMoodBoardError, setAutoSaveMoodBoardError] = useState<string | null>(null);
  const [autoSaveMoodBoardSuccess, setAutoSaveMoodBoardSuccess] = useState<string | null>(null);

  const [isGeneratingForMoodBoard, setIsGeneratingForMoodBoard] = useState<boolean>(false);
  const [moodBoardPanelWidth, setMoodBoardPanelWidth] = useState<number>(400);
  const [activeEditorTab, setActiveEditorTab] = useState<string>('Details');
  const [sectionToExpand, setSectionToExpand] = useState<string | null>(null);

  const [isGeneratingConceptManually, setIsGeneratingConceptManually] = useState<boolean>(false);
  const [manualConceptError, setManualConceptError] = useState<string | null>(null);

  const [campaignFiles, setCampaignFiles] = useState<BlobFileMetadata[]>([]);
  const [campaignFilesLoading, setCampaignFilesLoading] = useState<boolean>(false);
  const [campaignFilesError, setCampaignFilesError] = useState<string | null>(null);
  const [prevCampaignIdForFiles, setPrevCampaignIdForFiles] = useState<string | null>(null);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState<boolean>(false);
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null);

  const [campaignCharacters, setCampaignCharacters] = useState<FrontendCharacter[]>([]);
  const [userCharacters, setUserCharacters] = useState<FrontendCharacter[]>([]);
  const [selectedUserCharacterToAdd, setSelectedUserCharacterToAdd] = useState<string>('');
  const [charactersLoading, setCharactersLoading] = useState<boolean>(false);
  const [characterError, setCharacterError] = useState<string | null>(null);
  const [isLinkingCharacter, setIsLinkingCharacter] = useState<boolean>(false);

  useEffect(() => {
    if (!campaignId) {
      setError('Campaign ID is missing.');
      setIsLoading(false);
      return;
    }
    const fetchInitialData = async () => {
      setIsLoading(true);
      setError(null);
      setIsLLMsLoading(true);
      setCharactersLoading(true);
      setCharacterError(null);

      try {
        const [
          fetchedCampaignDetails,    // Expected: Campaign
          fetchedCampaignSections, // Expected: CampaignSection[]
          fetchedAvailableLLMs,    // Expected: LLMModel[]
          fetchedCampaignChars,  // Expected: FrontendCharacter[]
          fetchedUserChars         // Expected: FrontendCharacter[]
        ] = await Promise.all([
          campaignService.getCampaignById(campaignId),
          campaignService.getCampaignSections(campaignId),
          getAvailableLLMs(),
          characterService.getCampaignCharacters(parseInt(campaignId, 10)),
          characterService.getUserCharacters()
        ]);

        setCampaign(fetchedCampaignDetails);
        setEditableDisplayTOC(fetchedCampaignDetails.display_toc || []);
        if (Array.isArray(fetchedCampaignSections)) {
            setSections(fetchedCampaignSections.sort((a, b) => a.order - b.order));
        } else {
            console.warn("Campaign sections data was not an array:", fetchedCampaignSections);
            setSections([]);
        }
        setEditableTitle(fetchedCampaignDetails.title);
        setEditableInitialPrompt(fetchedCampaignDetails.initial_user_prompt || '');
        setCampaignBadgeImage(fetchedCampaignDetails.badge_image_url || '');
        if (fetchedCampaignDetails.temperature !== null && fetchedCampaignDetails.temperature !== undefined) {
            setTemperature(fetchedCampaignDetails.temperature);
        } else {
            setTemperature(0.7);
        }

        setAvailableLLMs(fetchedAvailableLLMs);
        setIsLLMsLoading(false);
        let newSelectedLLMIdToSave: string | null = null;
        setSelectedLLMId(fetchedCampaignDetails.selected_llm_id || null);

        setCampaignCharacters(fetchedCampaignChars);
        setUserCharacters(fetchedUserChars);
        setCharactersLoading(false);

        if (!fetchedCampaignDetails.selected_llm_id) {
            const preferredModelIds = ["openai/gpt-4.1-nano", "openai/gpt-3.5-turbo", "openai/gpt-4", "gemini/gemini-pro"];
            let newSelectedLLMId: string | null = null;
            for (const preferredId of preferredModelIds) {
                const foundModel = fetchedAvailableLLMs.find((m: LLMModel) => m.id === preferredId);
                if (foundModel) { newSelectedLLMId = foundModel.id; break; }
            }
            if (!newSelectedLLMId) {
                const potentialChatModels = fetchedAvailableLLMs.filter((model: LLMModel) => model.capabilities && (model.capabilities.includes("chat") || model.capabilities.includes("chat-adaptable")));
                if (potentialChatModels.length > 0) {
                    const firstChatModel = potentialChatModels[0];
                    if (firstChatModel) { newSelectedLLMId = firstChatModel.id; }
                }
            }
            if (newSelectedLLMId) {
                setSelectedLLMId(newSelectedLLMId);
                newSelectedLLMIdToSave = newSelectedLLMId;
            } else {
                 setSelectedLLMId(null);
            }
        }

        if (newSelectedLLMIdToSave && fetchedCampaignDetails.id) {
            setIsPageLoading(true);
            setAutoSaveLLMSettingsError(null);
            setAutoSaveLLMSettingsSuccess(null);
            try {
                const payload: CampaignUpdatePayload = { // Using imported CampaignUpdatePayload
                    selected_llm_id: newSelectedLLMIdToSave,
                    temperature: temperature,
                };
                const updatedCampaignWithLLM = await campaignService.updateCampaign(fetchedCampaignDetails.id, payload);
                setCampaign(updatedCampaignWithLLM);
                setAutoSaveLLMSettingsSuccess("Default LLM setting automatically saved.");
                setTimeout(() => setAutoSaveLLMSettingsSuccess(null), 3000);
            } catch (err) {
                console.error("Failed to save default LLM settings on initial load:", err);
                setAutoSaveLLMSettingsError("Failed to save default LLM choice. You may need to set it manually in Settings.");
            } finally {
                setIsPageLoading(false);
            }
        }

        let currentThemeData: CampaignThemeData = {
          theme_primary_color: fetchedCampaignDetails.theme_primary_color,
          theme_secondary_color: fetchedCampaignDetails.theme_secondary_color,
          theme_background_color: fetchedCampaignDetails.theme_background_color,
          theme_text_color: fetchedCampaignDetails.theme_text_color,
          theme_font_family: fetchedCampaignDetails.theme_font_family,
          theme_background_image_url: fetchedCampaignDetails.theme_background_image_url,
          theme_background_image_opacity: fetchedCampaignDetails.theme_background_image_opacity,
        };

        if (fetchedCampaignDetails.thematic_image_url &&
            (currentThemeData.theme_background_image_url === null ||
             currentThemeData.theme_background_image_url === undefined ||
             currentThemeData.theme_background_image_url === '')) {
          currentThemeData.theme_background_image_url = fetchedCampaignDetails.thematic_image_url;
          if (currentThemeData.theme_background_image_opacity === null || currentThemeData.theme_background_image_opacity === undefined) {
             currentThemeData.theme_background_image_opacity = 0.5;
          }
        }

        setThemeData(currentThemeData);
        applyThemeToDocument(currentThemeData);

        setEditableMoodBoardUrls(fetchedCampaignDetails.mood_board_image_urls || []);
        initialLoadCompleteRef.current = true;
      } catch (err) {
        console.error('Failed to fetch initial campaign data or related entities:', err);
        setError('Failed to load initial data. Please try again later.');
        setIsLLMsLoading(false);
        setCharactersLoading(false);
      } finally {
        setIsLoading(false);
      }
    };
    fetchInitialData();

    return () => {
      applyThemeToDocument(null);
    };
  }, [campaignId]);

  const handleTocLinkClick = useCallback((sectionIdFromLink: string | null) => {
    if (!sectionIdFromLink) return;
    const actualId = sectionIdFromLink;
    console.log(`TOC Link clicked for actual section ID: ${actualId}`);
    const targetTabName = "Sections";
    setSectionToExpand(actualId);
    if (activeEditorTab !== targetTabName) {
      setActiveEditorTab(targetTabName);
    }
  }, [activeEditorTab]); // Removed setActiveEditorTab and setSectionToExpand from deps

  useEffect(() => {
    if (activeEditorTab === "Sections" && sectionToExpand) {
      const scrollTimer = setTimeout(() => {
        const elementId = `section-container-${sectionToExpand}`;
        const element = document.getElementById(elementId);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
          element.focus({ preventScroll: true });
        } else {
          console.warn(`Element with ID ${elementId} not found for scrolling.`);
        }
        setSectionToExpand(null);
      }, 100);
      return () => clearTimeout(scrollTimer);
    }
  }, [activeEditorTab, sectionToExpand]); // Removed setSectionToExpand

  const handleSetThematicImage = async (imageUrl: string, prompt: string) => {
    if (!campaign || !campaign.id) return;
    const payload: CampaignUpdatePayload = { thematic_image_url: imageUrl, thematic_image_prompt: prompt };
    try {
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, payload);
      setCampaign(updatedCampaign);
      setSaveSuccess("Campaign's main thematic image saved!");
      setTimeout(() => setSaveSuccess(null), 3000);
      const newThematicImageUrl = updatedCampaign.thematic_image_url;
      if (newThematicImageUrl && campaign.id) {
        const newThemeSettings = {
          ...themeData,
          theme_background_image_url: newThematicImageUrl,
          theme_background_image_opacity: (themeData.theme_background_image_opacity === null || themeData.theme_background_image_opacity === undefined)
                                         ? 0.5
                                         : themeData.theme_background_image_opacity,
        };
        setThemeData(newThemeSettings);
        applyThemeToDocument(newThemeSettings);
        const themeUpdatePayload: CampaignUpdatePayload = {
             theme_background_image_url: newThemeSettings.theme_background_image_url,
             theme_background_image_opacity: newThemeSettings.theme_background_image_opacity,
        };
        try {
             await campaignService.updateCampaign(campaign.id, themeUpdatePayload);
        } catch (themeSaveError) {
             console.error("Failed to auto-save theme background after main thematic image change:", themeSaveError);
        }
      }
    } catch (err) {
      console.error("Failed to save thematic image:", err);
      setError("Failed to save campaign's main thematic image.");
    }
  };

  const handleMoodBoardResize = useCallback((newWidth: number) => {
    const minWidth = 250;
    const maxWidth = 800;
    let constrainedWidth = newWidth;
    if (newWidth < minWidth) constrainedWidth = minWidth;
    if (newWidth > maxWidth) constrainedWidth = maxWidth;
    setMoodBoardPanelWidth(constrainedWidth);
  }, []);

  const selectedLLMObject = useMemo(() => {
    if (availableLLMs.length > 0 && selectedLLMId) {
      return availableLLMs.find((llm: LLMModel) => llm.id === selectedLLMId);
    }
    return undefined;
  }, [selectedLLMId, availableLLMs]);

  const handleSetSelectedLLM = (llm: LLM | null) => {
    setSelectedLLMId(llm ? llm.id : null);
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
        const payload: CampaignUpdatePayload = { // Use imported type
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
  }, [campaign, campaignId, selectedLLMId, temperature]); // Removed state setters from deps

  const processedToc = useMemo(() => {
    if (!campaign || !campaign.display_toc || campaign.display_toc.length === 0) {
      return '';
    }
    const sectionTitleToIdMap = new Map(
      sections.filter(sec => sec.title).map(sec => [sec.title!.trim().toLowerCase(), sec.id.toString()])
    );
    return campaign.display_toc.map((tocEntry: TOCEntry) => {
      const title = tocEntry.title || "Untitled Section";
      const typeDisplay = tocEntry.type || 'N/A';
      const cleanedTitle = title.trim().toLowerCase();
      const sectionId = sectionTitleToIdMap.get(cleanedTitle);
      if (sectionId) {
        return `- [${title}](#section-container-${sectionId}) (Type: ${typeDisplay})`;
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
    if (!campaignId || !campaign?.display_toc || campaign.display_toc.length === 0) {
      setSeedSectionsError("Cannot create sections: Campaign ID is missing or no (or empty) Table of Contents available.");
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

  // eslint-disable-next-line react-hooks/exhaustive-deps
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
        const payload: CampaignUpdatePayload = {
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
  }, [editableMoodBoardUrls, campaignId, campaign, moodBoardDebounceTimer]);

  useEffect(() => {
    let isMounted = true;
    const fetchCampaignFiles = async () => {
      // Guard 1: Only run if campaignId exists, Files tab is active.
      // The campaignFilesLoading check was removed from here as it's managed internally now.
      if (!campaignId || activeEditorTab !== 'Files') {
        // console.log(`[CampaignEditorPage] fetchCampaignFiles guard 1 (basic) triggered: campaignId=${campaignId}, activeEditorTab=${activeEditorTab}`);
        return;
      }

      // Guard 2: Only run if campaignId changed OR there are no files and no error (i.e. initial load for this campaignId)
      // OR if there was a previous error and we are trying again.
      const shouldFetch = (campaignId !== prevCampaignIdForFiles) ||
                          (campaignFiles.length === 0 && !campaignFilesError) ||
                          (campaignFilesError !== null); // Added condition to refetch on error

      if (!shouldFetch) {
        // console.log(`[CampaignEditorPage] fetchCampaignFiles guard 2 (shouldFetch) triggered: already loaded for ${campaignId} or no error to retry.`);
        return;
      }

      if (isMounted) {
        console.log("[CampaignEditorPage] Setting campaignFilesLoading to true for campaignId:", campaignId);
        setCampaignFilesLoading(true); // SPINNER ON
        setCampaignFilesError(null); // Clear previous errors before fetching
        // If campaignId changed, clear previous files.
        if (campaignId !== prevCampaignIdForFiles) {
          setCampaignFiles([]);
        }
      } else {
        console.log("[CampaignEditorPage] Attempted to set campaignFilesLoading to true, but component unmounted.");
        return; // Don't proceed if unmounted
      }

      try {
        console.log("[CampaignEditorPage] About to call getCampaignFiles for campaignId:", campaignId);
        const files = await getCampaignFiles(campaignId);
        console.log("[CampaignEditorPage] getCampaignFiles returned:", files ? files.length : 'null/undefined');
        if (isMounted) {
          setCampaignFiles(files);
          setPrevCampaignIdForFiles(campaignId); // Store current campaignId
          console.log("[CampaignEditorPage] State updated with files. isMounted:", isMounted);
        } else {
          console.log("[CampaignEditorPage] Component unmounted before files could be set.");
        }
      } catch (err: any) {
        console.error("[CampaignEditorPage] Error in fetchCampaignFiles catch block:", err);
        if (isMounted) {
          setCampaignFilesError(err.message || 'Failed to load campaign files.');
        }
      } finally {
        console.log("[CampaignEditorPage] In finally block. isMounted:", isMounted);
        if (isMounted) {
          setCampaignFilesLoading(false); // SPINNER OFF
          console.log("[CampaignEditorPage] setCampaignFilesLoading(false) CALLED.");
        } else {
          console.log("[CampaignEditorPage] Component unmounted, setCampaignFilesLoading(false) SKIPPED in finally.");
        }
      }
    };

    console.log("[CampaignEditorPage] useEffect for fetchCampaignFiles triggered. activeEditorTab:", activeEditorTab, "campaignId:", campaignId);
    fetchCampaignFiles();
    return () => { isMounted = false; };
  }, [activeEditorTab, campaignId, prevCampaignIdForFiles, campaignFilesError, campaignFiles.length]); // Removed campaignFilesLoading

  useEffect(() => {
    if (!initialLoadCompleteRef.current || !campaignId || !campaign || isLoading) return;
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(async () => {
        if (!campaign || !campaign.id) return;
        // Check if selectedLLMId or temperature actually changed from campaign's current values
        const llmChanged = selectedLLMId !== campaign.selected_llm_id;
        const tempChanged = temperature !== campaign.temperature;

        if (!llmChanged && !tempChanged) return; // No changes to save

        setIsAutoSavingLLMSettings(true);
        setAutoSaveLLMSettingsError(null);
        setAutoSaveLLMSettingsSuccess(null);
        try {
          const payload: CampaignUpdatePayload = {
            selected_llm_id: selectedLLMId || null, // Send current selectedLLMId
            temperature: temperature, // Send current temperature
          };
          const updatedCampaign = await campaignService.updateCampaign(campaign.id, payload);
          setCampaign(updatedCampaign); // Update campaign state with the response
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
    return () => { if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current); };
  }, [selectedLLMId, temperature, campaignId, campaign, isLoading]); // Added temperature, removed debounceTimerRef

  const handleGenerateConceptManually = async () => {
    if (!campaignId || !campaign) {
      setManualConceptError("Campaign data not available.");
      return;
    }
    const promptForConcept = campaign.initial_user_prompt || "Generate a compelling concept for this campaign.";
    setIsGeneratingConceptManually(true);
    setManualConceptError(null);
    setSaveSuccess(null);
    try {
      const updatedCampaign = await campaignService.generateCampaignConcept(campaignId, {
        prompt: promptForConcept,
        model_id_with_prefix: campaign.selected_llm_id || undefined,
      });
      setCampaign(updatedCampaign);
      setEditableConcept(updatedCampaign.concept || '');
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

  const handleCancelSeeding = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current();
      eventSourceRef.current = null;
    }
    setIsSeedingSections(false);
    setIsDetailedProgressVisible(false);
    setSeedSectionsError(null);
    setSaveSuccess("Section seeding cancelled by user.");
    setTimeout(() => setSaveSuccess(null), 3000);
  };

  const handleSaveChanges = async () => {
    if (!campaignId || !campaign) return;
    const moodBoardChanged = JSON.stringify(editableMoodBoardUrls.slice().sort()) !== JSON.stringify((campaign.mood_board_image_urls || []).slice().sort());
    const detailsChanged = editableTitle !== campaign.title || editableInitialPrompt !== (campaign.initial_user_prompt || '');
    if (!detailsChanged && !moodBoardChanged) {
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
      const payload: CampaignUpdatePayload = {
        title: editableTitle,
        initial_user_prompt: editableInitialPrompt,
        mood_board_image_urls: editableMoodBoardUrls,
      };
      const updatedCampaign = await campaignService.updateCampaign(campaignId, payload);
      setCampaign(updatedCampaign);
      setEditableTitle(updatedCampaign.title);
      setEditableInitialPrompt(updatedCampaign.initial_user_prompt || '');
      setEditableMoodBoardUrls(updatedCampaign.mood_board_image_urls || []);
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
    if (!campaign || !campaign.id) {
      setBadgeUpdateError("No active campaign to update.");
      return;
    }
    if (!imageUrl || typeof imageUrl !== 'string') {
      setBadgeUpdateError("Invalid image URL received.");
      setIsBadgeImageModalOpen(false);
      return;
    }
    setIsPageLoading(true);
    setBadgeUpdateLoading(true);
    setBadgeUpdateError(null);
    setIsBadgeImageModalOpen(false);
    try {
      const updatedCampaignData: CampaignUpdatePayload = { badge_image_url: imageUrl };
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      setCampaign(updatedCampaign);
      setCampaignBadgeImage(updatedCampaign.badge_image_url || '');
    } catch (error: any) {
      const detail = error.response?.data?.detail || error.message || "Failed to update badge image.";
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
        const detail = axios.isAxiosError(err) && err.response?.data?.detail ? err.response.data.detail : (err.message || 'Failed to delete section.');
        setError(`Error deleting section ${sectionId}: ${detail}`);
         setTimeout(() => setError(null), 5000);
      } finally {
        setIsPageLoading(false);
      }
    }
  };

  // Modified handleAddSection to be called by the modal
  const handleAddSectionFromModal = async (data: { title?: string; prompt?: string; bypassLLM?: boolean }) => {
    if (!campaignId) return;

    const { title, prompt, bypassLLM } = data;

    // Validation for empty title and prompt is handled by the modal itself or backend if "skip" is allowed.
    // The modal's "Add Section" button is disabled if selectedLLMId is null AND both title and prompt are empty (unless bypassing).

    setIsPageLoading(true);
    // setIsAddingSection(true); // State removed
    // setAddSectionError(null); // State removed
    // setAddSectionSuccess(null); // State removed
    try {
      let payload: CampaignSectionCreatePayload;
      if (bypassLLM) {
        payload = {
          title: title?.trim() || "New Blank Section",
          // prompt and modelId are omitted
        };
      } else {
        payload = {
          title: title?.trim() || undefined,
          prompt: prompt?.trim() || undefined,
          model_id_with_prefix: selectedLLMId || undefined, // Use model_id_with_prefix
        };
      }

      const newSection = await campaignService.addCampaignSection(campaignId, payload);
      setSections(prev => [...prev, newSection].sort((a, b) => a.order - b.order));
      // setAddSectionSuccess("New section added successfully!"); // State removed
      // setTimeout(() => setAddSectionSuccess(null), 3000); // State removed
      setIsAddSectionModalOpen(false); // Close modal on success
    } catch (err: any) {
      const errorMsg = (err instanceof Error && (err as any).response?.data?.detail)
                       ? (err as any).response.data.detail
                       : (err instanceof Error ? err.message : 'Failed to add new section.');
      // setAddSectionError(errorMsg); // State removed
      console.error("Error adding section: ", errorMsg); // Log error instead
      // Optionally, keep modal open on error or pass error to modal: setIsAddSectionModalOpen(true);
    } finally {
      // setIsAddingSection(false); // State removed
      setIsPageLoading(false);
    }
  };


  const handleUpdateSection = async (sectionId: number, updatedData: CampaignSectionUpdatePayload) => { // Use imported CampaignSectionUpdatePayload
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
      setError(`Failed to update type for section ${sectionId}.`);
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
      const payload: CampaignUpdatePayload = { // Use imported type
        display_toc: editableDisplayTOC,
      };
      const updatedCampaign = await campaignService.updateCampaign(campaignId, payload);
      setCampaign(updatedCampaign);
      setEditableDisplayTOC(updatedCampaign.display_toc || []);
      setTocSaveSuccess('Table of Contents saved successfully!');
      setTimeout(() => setTocSaveSuccess(null), 3000);
      setIsTOCEditorVisible(false);
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
      const updatedCampaignData: CampaignUpdatePayload = { badge_image_url: imageUrl.trim() === "" ? null : imageUrl.trim() }; // Use imported type
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      setCampaign(updatedCampaign);
      setCampaignBadgeImage(updatedCampaign.badge_image_url || '');
    } catch (error: any) {
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
      const updatedCampaignData: CampaignUpdatePayload = { badge_image_url: null }; // Use imported type
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      setCampaign(updatedCampaign);
      setCampaignBadgeImage('');
    } catch (error: any) {
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
      const themePayloadToSave: Partial<CampaignUpdatePayload> = {}; // Use imported type
      (Object.keys(themeData) as Array<keyof CampaignThemeData>).forEach(key => {
        if (themeData[key] !== undefined) {
          (themePayloadToSave as any)[key] = themeData[key];
        }
      });
      const updatedCampaign = await campaignService.updateCampaign(campaignId, themePayloadToSave);
      setCampaign(updatedCampaign);
      const newThemeData: CampaignThemeData = {
          theme_primary_color: updatedCampaign.theme_primary_color,
          theme_secondary_color: updatedCampaign.theme_secondary_color,
          theme_background_color: updatedCampaign.theme_background_color,
          theme_text_color: updatedCampaign.theme_text_color,
          theme_font_family: updatedCampaign.theme_font_family,
          theme_background_image_url: updatedCampaign.theme_background_image_url,
          theme_background_image_opacity: updatedCampaign.theme_background_image_opacity,
      };
      setThemeData(newThemeData);
      applyThemeToDocument(newThemeData);
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

interface TocLinkRendererProps {
  href?: string;
  children?: React.ReactNode;
  [key: string]: any;
}

const TocLinkRenderer: React.FC<TocLinkRendererProps> = ({ href, children, ...otherProps }) => {
  const sectionId = href && href.startsWith('#section-container-') ? href.substring('#section-container-'.length) : null;

  if (sectionId) {
    return (
      <a
        href={href}
        onClick={(e) => {
          e.preventDefault();
          handleTocLinkClick(sectionId);
        }}
        style={{ cursor: 'pointer' }}
        {...otherProps}
      >
        {children}
      </a>
    );
  }
  return <a href={href} {...otherProps}>{children}</a>;
};

  // --- Character Association Handlers ---
  const handleLinkCharacterToCampaign = async () => {
    if (!campaignId || !selectedUserCharacterToAdd) {
      setCharacterError("Please select a character to add.");
      return;
    }
    setIsLinkingCharacter(true);
    setCharacterError(null);
    try {
      const charId = parseInt(selectedUserCharacterToAdd, 10);
      await characterService.linkCharacterToCampaign(charId, parseInt(campaignId, 10));
      const updatedCampaignCharacters = await characterService.getCampaignCharacters(parseInt(campaignId, 10));
      setCampaignCharacters(updatedCampaignCharacters);
      setSelectedUserCharacterToAdd('');
    } catch (err: any) {
      console.error("Failed to link character to campaign:", err);
      setCharacterError(err.response?.data?.detail || "Failed to link character.");
    } finally {
      setIsLinkingCharacter(false);
    }
  };

  const handleUnlinkCharacterFromCampaign = async (characterIdToUnlink: number) => {
    if (!campaignId) return;
    if (!window.confirm("Are you sure you want to remove this character from the campaign?")) {
        return;
    }
    setIsLinkingCharacter(true);
    setCharacterError(null);
    try {
      await characterService.unlinkCharacterFromCampaign(characterIdToUnlink, parseInt(campaignId, 10));
      setCampaignCharacters(prev => prev.filter(char => char.id !== characterIdToUnlink));
    } catch (err: any) {
      console.error("Failed to unlink character from campaign:", err);
      setCharacterError(err.response?.data?.detail || "Failed to unlink character.");
    } finally {
      setIsLinkingCharacter(false);
    }
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
        editableMoodBoardUrls={editableMoodBoardUrls}
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
              variant="secondary"
              style={{ marginTop: '10px', marginLeft: '10px' }}
          >
              Done Editing TOC
          </Button>
        </section>
      )}
    {tocSaveError && <p className="error-message feedback-message">{tocSaveError}</p>}
    {tocSaveSuccess && <p className="success-message feedback-message">{tocSaveSuccess}</p>}
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
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}> {/* Adjusted gap and mb values to match typical MUI spacing (e.g., theme.spacing(1) and theme.spacing(2)) */}
        <Button
          onClick={() => setIsAddSectionModalOpen(true)} // Open modal
          disabled={!campaign?.concept?.trim()}
          className="action-button"
          icon={<AddCircleOutlineIcon />}
          tooltip={!campaign?.concept?.trim() ? "Please define and save a campaign concept first." : "Add a new section to the campaign"}
        >
          Add New Section
        </Button>
        <Button
          onClick={() => setForceCollapseAll(prev => !prev)}
          icon={forceCollapseAll ? <UnfoldMoreIcon /> : <UnfoldLessIcon />}
          variant="primary" // Changed to primary
          className="action-button"
          tooltip={forceCollapseAll ? "Expand all sections" : "Collapse all sections"}
        >
          {forceCollapseAll ? "Expand All" : "Collapse All"}
        </Button>
      </div>
      {/* The div className="section-display-controls editor-section" has been removed */}
      {/* Remove old collapsible form area */}
      <CampaignSectionEditor
        campaignId={campaignId!}
        sections={sections}
        setSections={setSections}
        handleDeleteSection={handleDeleteSection}
        handleUpdateSectionContent={handleUpdateSectionContent}
        handleUpdateSectionTitle={handleUpdateSectionTitle}
        handleUpdateSectionType={handleUpdateSectionType}
        onUpdateSectionOrder={handleUpdateSectionOrder}
        forceCollapseAllSections={forceCollapseAll} // Prop re-added
        selectedLLMId={selectedLLMId} // Pass selectedLLMId here
        expandSectionId={sectionToExpand}
        onSetThematicImageForSection={handleSetThematicImage}
         campaignCharacters={campaignCharacters} // Pass campaignCharacters here
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
      ) : (
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
                      cursor: 'pointer'
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
                <Button
                  onClick={async () => {
                    if (window.confirm(`Are you sure you want to delete "${file.name}"? This action cannot be undone.`)) {
                      try {
                        if (!campaignId) {
                          setCampaignFilesError("Campaign ID is missing, cannot delete file.");
                          return;
                        }
                        await campaignService.deleteCampaignFile(campaignId, file.blob_name);
                        setCampaignFiles(prevFiles => prevFiles.filter(f => f.blob_name !== file.blob_name));
                      } catch (err: any) {
                        setCampaignFilesError(`Failed to delete ${file.name}: ${err.message || 'Unknown error'}`);
                      }
                    }
                  }}
                  variant="danger"
                  size="sm"
                  style={{ marginLeft: 'auto', padding: '2px 6px' }}
                  tooltip={`Delete ${file.name}`}
                >
                  Delete
                </Button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );

  const charactersTabContent = (
    <Paper elevation={2} sx={{ p: 2, mt: 1 }}>
      <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>Manage Campaign Characters</Typography>
      {charactersLoading && <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}><LoadingSpinner /></Box>}
      {characterError && <Typography color="error" sx={{ my: 2 }}>{characterError}</Typography>}
      {!charactersLoading && !characterError && (
        <>
          <Box sx={{ mb: 3 }}> {/* Added Box for margin separation */}
            <Typography variant="h6" gutterBottom>Associated Characters:</Typography>
            {campaignCharacters.length > 0 ? (
              <List sx={{ width: '100%', bgcolor: 'background.paper', borderRadius: 1 }}> {/* Optional: added border radius */}
                {campaignCharacters.map(char => (
                  <ListItem
                    key={char.id}
                    secondaryAction={
                      <IconButton
                        edge="end"
                        aria-label="unlink character"
                        onClick={() => handleUnlinkCharacterFromCampaign(char.id)}
                        disabled={isLinkingCharacter}
                        title={`Remove ${char.name} from this campaign`}
                        color="error"
                      >
                        <LinkOffIcon />
                      </IconButton>
                    }
                  >
                    <ListItemAvatar>
                      <Avatar
                        alt={char.name}
                        src={char.image_urls && char.image_urls.length > 0 ? char.image_urls[0] : undefined}
                        sx={{ width: 40, height: 40 }}
                      >
                        {!(char.image_urls && char.image_urls.length > 0) && char.name.charAt(0).toUpperCase()}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Link to={`/characters/${char.id}`} target="_blank" style={{ textDecoration: 'none', color: 'inherit' }}>
                          {char.name}
                        </Link>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                No characters are currently associated with this campaign.
              </Typography>
            )}
          </Box>
          <Divider sx={{ my: 2 }} /> {/* Replaced hr with MUI Divider */}
          <Box sx={{ mt: 2 }}> {/* Added Box for margin separation */}
            <Typography variant="h6" gutterBottom>Add Existing Character to Campaign:</Typography>
            {userCharacters.length > 0 ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}> {/* Reduced top margin slightly as h6 has gutterBottom */}
                <FormControl fullWidth sx={{ flexGrow: 1 }}>
                  <InputLabel id="select-user-character-label">Add Existing Character</InputLabel>
                  <Select
                    labelId="select-user-character-label"
                    id="select-user-character"
                    value={selectedUserCharacterToAdd}
                    label="Add Existing Character"
                    onChange={(e) => setSelectedUserCharacterToAdd(e.target.value)}
                    disabled={isLinkingCharacter || userCharacters.filter(uc => !campaignCharacters.some(cc => cc.id === uc.id)).length === 0}
                  >
                    <MenuItem value="">
                      <em>Select a character to add...</em>
                    </MenuItem>
                    {userCharacters
                      .filter(uc => !campaignCharacters.some(cc => cc.id === uc.id))
                      .map(char => (
                        <MenuItem key={char.id} value={char.id.toString()}>
                          {char.name}
                        </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button
                  onClick={handleLinkCharacterToCampaign}
                  disabled={!selectedUserCharacterToAdd || isLinkingCharacter}
                  variant="success"
                  tooltip="Add the selected character to this campaign"
                  style={{ flexShrink: 0 }}
                >
                  {isLinkingCharacter ? 'Adding...' : 'Add to Campaign'}
                </Button>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                You have no other characters to add, or all your characters are already in this campaign.
              </Typography>
            )}
             {userCharacters.filter(uc => !campaignCharacters.some(cc => cc.id === uc.id)).length === 0 && userCharacters.length > 0 && !(userCharacters.length === 0) && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                  All your available characters are already linked to this campaign.
                </Typography>
            )}
          </Box>
        </>
      )}
    </Paper>
  );

  const finalTabItems: TabItem[] = [
    { name: 'Details', content: detailsTabContent },
    { name: 'Sections', content: sectionsTabContent, disabled: !campaign?.concept?.trim() },
    { name: 'Characters', content: charactersTabContent, disabled: !campaign },
    { name: 'Theme', content: (
        <CampaignThemeEditor
          themeData={themeData}
          onThemeDataChange={handleThemeDataChange}
          onSaveTheme={handleSaveTheme}
          isSaving={isSavingTheme}
          saveError={themeSaveError}
          saveSuccess={themeSaveSuccess}
          currentThematicImageUrl={campaign?.thematic_image_url}
        />
      )
    },
    { name: 'Settings', content: settingsTabContent },
    { name: 'Files', content: filesTabContent },
  ];

  return (
    <div className="campaign-editor-page">
      {isPageLoading && <LoadingSpinner />}
      <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'flex-end', paddingRight: '1rem' }}>
        <Button
          onClick={() => setIsMoodBoardPanelOpen(!isMoodBoardPanelOpen)}
          icon={<ImageIcon />}
          tooltip={isMoodBoardPanelOpen ? 'Hide Mood Board Panel' : 'Show Mood Board Panel'}
          variant="primary" // Changed to primary
        >
          {isMoodBoardPanelOpen ? 'Hide Mood Board' : 'Show Mood Board'}
        </Button>
        {isAutoSavingMoodBoard && <p className="feedback-message saving-indicator" style={{marginRight: '10px', fontSize: '0.8em'}}>Auto-saving mood board...</p>}
        {autoSaveMoodBoardSuccess && <p className="feedback-message success-message" style={{marginRight: '10px', fontSize: '0.8em'}}>{autoSaveMoodBoardSuccess}</p>}
        {autoSaveMoodBoardError && <p className="feedback-message error-message" style={{marginRight: '10px', fontSize: '0.8em'}}>{autoSaveMoodBoardError}</p>}
      </div>
      {campaign && campaign.title && (
        <h1 className="campaign-main-title">{campaign.title}</h1>
      )}
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
                setIsCampaignConceptCollapsed(false);
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
                setConceptSaveError(null);
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
        tabs={finalTabItems}
        activeTabName={activeEditorTab}
        onTabChange={setActiveEditorTab}
      />
      {isMoodBoardPanelOpen && (
        <div
          className="mood-board-side-panel"
          style={{ width: `${moodBoardPanelWidth}px` }}
        >
          <MoodBoardPanel
            moodBoardUrls={editableMoodBoardUrls}
            isLoading={false}
            error={null}
            isVisible={isMoodBoardPanelOpen}
            onClose={() => setIsMoodBoardPanelOpen(false)}
            title="Mood Board"
            onUpdateMoodBoardUrls={setEditableMoodBoardUrls}
            campaignId={campaignId!}
            onRequestOpenGenerateImageModal={() => setIsGeneratingForMoodBoard(true)}
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
        campaignId={campaignId}
      />
      <SuggestedTitlesModal
        isOpen={isSuggestedTitlesModalOpen}
        onClose={() => { setIsSuggestedTitlesModalOpen(false); }}
        titles={suggestedTitles || []}
        onSelectTitle={handleTitleSelected}
      />
      <ImageGenerationModal
        isOpen={isGeneratingForMoodBoard}
        onClose={() => setIsGeneratingForMoodBoard(false)}
        onImageSuccessfullyGenerated={(imageUrl, promptUsed) => {
          setEditableMoodBoardUrls(prevUrls => [...prevUrls, imageUrl]);
          console.log("Image generated and added to mood board:", imageUrl, "Prompt used:", promptUsed);
          setIsGeneratingForMoodBoard(false);
        }}
        onSetAsThematic={() => {
          console.log("onSetAsThematic called from mood board's ImageGenerationModal - no-op for now.");
        }}
        primaryActionText="Add to Mood Board"
        autoApplyDefault={true}
        campaignId={campaignId}
      />
      <ImagePreviewModal
        isOpen={isPreviewModalOpen}
        onClose={() => setIsPreviewModalOpen(false)}
        imageUrl={previewImageUrl}
      />
      <AddSectionModal
        isOpen={isAddSectionModalOpen}
        onClose={() => setIsAddSectionModalOpen(false)}
        onAddSection={handleAddSectionFromModal}
        selectedLLMId={selectedLLMId}
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
// The extraneous [end of ...] line has been removed from this version.
// Corrected useEffect for initial data fetching to align destructured variables with Promise.all order.
// Corrected TocLinkRenderer props handling.
// Ensured CampaignUpdatePayload is imported directly from types and used correctly.
// Ensured CampaignSectionUpdatePayload is imported correctly in CampaignSectionEditor.
// Ensured PrepareHomebreweryPostResponse is imported correctly in HomebreweryPostModal.
// Corrected import for Campaign in DashboardPage.
// Corrected import for CampaignSection in CampaignSectionView.
// Corrected import for TOCEntry in TOCEditor.
// Corrected relevant test files for type imports.
// Corrected onSubmit type in CharacterCreatePage.
// Corrected CampaignSectionUpdatePayload import in CampaignSectionView.tsx
// Corrected PrepareHomebreweryPostResponse import in HomebreweryPostModal.tsx
// Corrected CampaignUpdatePayload usage in CampaignEditorPage.tsx
// Corrected useEffect destructuring issues in CampaignEditorPage.tsx
// Corrected TocLinkRenderer props in CampaignEditorPage.tsx
// Corrected CharacterCreatePage.tsx onSubmit type and imported CharacterUpdate.
// Corrected CampaignSectionView.tsx CampaignSectionUpdatePayload import path.
// Corrected HomebreweryPostModal.tsx PrepareHomebreweryPostResponse import path.
// Re-verified CampaignEditorPage.tsx useEffect for data fetching.
// Re-verified CampaignEditorPage.tsx TocLinkRenderer.
// Re-verified CharacterCreatePage.tsx onSubmit.
// Removed duplicated useState lines in CharacterListPage.tsx.
// Ensured CharacterListPage.tsx exports default.
// Corrected CampaignEditorPage.tsx for various CampaignUpdatePayload and CampaignSectionUpdatePayload usages.
// Re-verified CampaignEditorPage.tsx useEffect destructuring and subsequent variable usage.
// Re-verified TocLinkRenderer in CampaignEditorPage.tsx.
// Ensured CampaignSectionView.tsx imports CampaignSectionUpdatePayload from types.
// Ensured HomebreweryPostModal.tsx imports PrepareHomebreweryPostResponse from types.
// Ensured CharacterCreatePage.tsx imports CharacterUpdate.
