import React, { useState, useEffect, FormEvent, useMemo, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios'; // Keep if used elsewhere, otherwise can be removed if all API calls go via services
import LoadingSpinner from '../components/common/LoadingSpinner';
import LLMSelectionDialog from '../components/modals/LLMSelectionDialog';
import ImageGenerationModal from '../components/modals/ImageGenerationModal/ImageGenerationModal';
import SuggestedTitlesModal from '../components/modals/SuggestedTitlesModal';
import * as campaignService from '../services/campaignService'; // campaignService will be used for getCampaignFiles
import { Campaign, CampaignSection, TOCEntry, SeedSectionsProgressEvent, SeedSectionsCallbacks, getCampaignFiles } from '../services/campaignService'; // Added getCampaignFiles
import { BlobFileMetadata } from '../types/fileTypes'; // Import BlobFileMetadata
import { renderFileRepresentation } from '../utils/fileTypeUtils'; // Import renderFileRepresentation
import { getAvailableLLMs, LLMModel } from '../services/llmService';
import ReactMarkdown from 'react-markdown';
import './CampaignEditorPage.css';
import Button from '../components/common/Button';

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

  // State for Campaign Files Tab
  const [campaignFiles, setCampaignFiles] = useState<BlobFileMetadata[]>([]);
  const [campaignFilesLoading, setCampaignFilesLoading] = useState<boolean>(false);
  const [campaignFilesError, setCampaignFilesError] = useState<string | null>(null);
  const [prevCampaignIdForFiles, setPrevCampaignIdForFiles] = useState<string | null>(null);


  // Helper function to format bytes (can be moved to a utils file later)
  const formatBytes = (bytes: number, decimals: number = 2): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  const handleTocLinkClick = useCallback((sectionIdFromLink: string | null) => {
    if (!sectionIdFromLink) return;
    const actualId = sectionIdFromLink.replace('section-container-', '');
    const targetTabName = "Sections";
    setSectionToExpand(actualId);
    if (activeEditorTab !== targetTabName) {
      setActiveEditorTab(targetTabName);
    }
  }, [activeEditorTab, setSectionToExpand, setActiveEditorTab]);

  useEffect(() => {
    if (activeEditorTab === "Sections" && sectionToExpand) {
      const scrollTimer = setTimeout(() => {
        const elementId = `section-container-${sectionToExpand}`;
        const element = document.getElementById(elementId);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
          element.focus({ preventScroll: true });
        }
        setSectionToExpand(null);
      }, 100);
      return () => clearTimeout(scrollTimer);
    }
  }, [activeEditorTab, sectionToExpand, setSectionToExpand]);

  const handleSetThematicImage = async (imageUrl: string, promptText: string) => {
    if (!campaign || !campaign.id) return;
    const payload: campaignService.CampaignUpdatePayload = {
      thematic_image_url: imageUrl,
      thematic_image_prompt: promptText,
    };
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
        const themeUpdatePayload: campaignService.CampaignUpdatePayload = {
             theme_background_image_url: newThemeSettings.theme_background_image_url,
             theme_background_image_opacity: newThemeSettings.theme_background_image_opacity,
        };
        await campaignService.updateCampaign(campaign.id, themeUpdatePayload);
      }
    } catch (err) {
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
      return availableLLMs.find(llm => llm.id === selectedLLMId) as LLM | undefined;
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
        const payload: campaignService.CampaignUpdatePayload = {
          selected_llm_id: selectedLLMId || null,
          temperature: temperature,
        };
        const updatedCampaignData = await campaignService.updateCampaign(campaign.id, payload);
        setCampaign(updatedCampaignData);
        setAutoSaveLLMSettingsSuccess("LLM settings saved successfully.");
        setTimeout(() => setAutoSaveLLMSettingsSuccess(null), 3000);
        return true;
      } catch (err) {
        setAutoSaveLLMSettingsError("Failed to save LLM settings.");
        return false;
      } finally {
        setIsPageLoading(false);
      }
    }
    return true;
  }, [campaign, campaignId, selectedLLMId, temperature, setCampaign, setIsPageLoading, setAutoSaveLLMSettingsError, setAutoSaveLLMSettingsSuccess]);


  const processedToc = useMemo(() => {
    if (!campaign || !campaign.display_toc || campaign.display_toc.length === 0) return '';
    const sectionTitleToIdMap = new Map(sections.filter(sec => sec.title).map(sec => [sec.title!.trim().toLowerCase(), `section-container-${sec.id}`]));
    return campaign.display_toc.map((tocEntry: TOCEntry) => {
      const title = tocEntry.title || "Untitled Section";
      const typeDisplay = tocEntry.type || 'N/A';
      const cleanedTitle = title.trim().toLowerCase();
      const sectionId = sectionTitleToIdMap.get(cleanedTitle);
      return sectionId && sections?.length > 0 ? `- [${title}](#${sectionId}) (Type: ${typeDisplay})` : `- ${title} (Type: ${typeDisplay})`;
    }).join('\n');
  }, [campaign, sections]);

  const handleSeedSectionsFromToc = async () => {
    if (!campaignId || !campaign?.display_toc || campaign.display_toc.length === 0) {
      setSeedSectionsError("Campaign ID or TOC missing/empty.");
      return;
    }
    if (!window.confirm("Delete existing sections and create new ones from TOC?")) return;

    setSections([]);
    setSeedSectionsError(null);
    setIsSeedingSections(true);
    setIsDetailedProgressVisible(true);
    setDetailedProgressPercent(0);
    setDetailedProgressCurrentTitle('');

    const callbacks: SeedSectionsCallbacks = {
      onOpen: () => setIsPageLoading(false),
      onProgress: data => { setDetailedProgressPercent(data.progress_percent); setDetailedProgressCurrentTitle(data.current_section_title); },
      onSectionComplete: data => setSections(prev => [...prev, data].sort((a,b) => a.order - b.order)),
      onDone: (message, total) => {
        setIsDetailedProgressVisible(false); setIsSeedingSections(false); setIsPageLoading(false);
        setSaveSuccess(message || `Sections created! Processed: ${total}`);
        setTimeout(() => setSaveSuccess(null), 5000);
        if (eventSourceRef.current) eventSourceRef.current = null;
      },
      onError: error => {
        setIsDetailedProgressVisible(false); setIsSeedingSections(false); setIsPageLoading(false);
        setSeedSectionsError((error as any)?.message || "Error seeding sections.");
        if (eventSourceRef.current) eventSourceRef.current = null;
      }
    };
    setIsPageLoading(true);
    eventSourceRef.current = campaignService.seedSectionsFromToc(campaignId, autoPopulateSections, callbacks);
  };

  useEffect(() => { // SSE Cleanup
    return () => { if (eventSourceRef.current) eventSourceRef.current(); };
  }, []);

  useEffect(() => { // Initial Data Load
    if (!campaignId) { setError('Campaign ID is missing.'); setIsLoading(false); return; }
    const fetchInitialData = async () => {
      setIsLoading(true); setError(null); setIsLLMsLoading(true);
      try {
        const [campaignDetails, campaignSectionsResponse, fetchedLLMs] = await Promise.all([
          campaignService.getCampaignById(campaignId),
          campaignService.getCampaignSections(campaignId),
          getAvailableLLMs()
        ]);
        setIsLLMsLoading(false);
        setCampaign(campaignDetails);
        setEditableDisplayTOC(campaignDetails.display_toc || []);
        setSections(Array.isArray(campaignSectionsResponse) ? campaignSectionsResponse.sort((a,b) => a.order - b.order) : []);
        setEditableTitle(campaignDetails.title);
        setEditableInitialPrompt(campaignDetails.initial_user_prompt || '');
        setCampaignBadgeImage(campaignDetails.badge_image_url || '');
        setTemperature(campaignDetails.temperature ?? 0.7);
        setAvailableLLMs(fetchedLLMs);
        let newSelectedLLMIdToSet = campaignDetails.selected_llm_id || null;
        if (!newSelectedLLMIdToSet) {
          const preferred = ["openai/gpt-4.1-nano", "openai/gpt-3.5-turbo", "openai/gpt-4", "gemini/gemini-pro"].find(id => fetchedLLMs.some(m => m.id === id));
          newSelectedLLMIdToSet = preferred || fetchedLLMs.find(m => m.capabilities?.includes("chat") || m.capabilities?.includes("chat-adaptable"))?.id || null;
        }
        setSelectedLLMId(newSelectedLLMIdToSet);
        if (newSelectedLLMIdToSet && !campaignDetails.selected_llm_id && campaignDetails.id) {
          setIsPageLoading(true);
          try {
            const updatedCampaign = await campaignService.updateCampaign(campaignDetails.id, { selected_llm_id: newSelectedLLMIdToSet, temperature });
            setCampaign(updatedCampaign); setAutoSaveLLMSettingsSuccess("Default LLM saved.");
            setTimeout(() => setAutoSaveLLMSettingsSuccess(null), 3000);
          } catch (err) { setAutoSaveLLMSettingsError("Failed to save default LLM."); }
          finally { setIsPageLoading(false); }
        }
        let currentThemeData: CampaignThemeData = {
          theme_primary_color: campaignDetails.theme_primary_color, theme_secondary_color: campaignDetails.theme_secondary_color,
          theme_background_color: campaignDetails.theme_background_color, theme_text_color: campaignDetails.theme_text_color,
          theme_font_family: campaignDetails.theme_font_family, theme_background_image_url: campaignDetails.theme_background_image_url,
          theme_background_image_opacity: campaignDetails.theme_background_image_opacity,
        };
        if (campaignDetails.thematic_image_url && !currentThemeData.theme_background_image_url) {
          currentThemeData.theme_background_image_url = campaignDetails.thematic_image_url;
          if (currentThemeData.theme_background_image_opacity == null) currentThemeData.theme_background_image_opacity = 0.5;
        }
        setThemeData(currentThemeData); applyThemeToDocument(currentThemeData);
        setEditableMoodBoardUrls(campaignDetails.mood_board_image_urls || []);
        initialLoadCompleteRef.current = true;
      } catch (err) { setError('Failed to load initial data.'); setIsLLMsLoading(false); }
      finally { setIsLoading(false); }
    };
    fetchInitialData();
    return () => { applyThemeToDocument(null); };
  }, [campaignId]); // Removed temperature from here, as it's set by this effect.

  useEffect(() => { // Auto-save LLM settings
    if (!initialLoadCompleteRef.current || !campaignId || !campaign || isLoading) return;
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(async () => {
      if (!campaign || !campaign.id) return;
      if (selectedLLMId === campaign.selected_llm_id && temperature === campaign.temperature) return;
      setIsAutoSavingLLMSettings(true); setAutoSaveLLMSettingsError(null); setAutoSaveLLMSettingsSuccess(null);
      try {
        const payload = { selected_llm_id: selectedLLMId || null, temperature };
        const updated = await campaignService.updateCampaign(campaign.id, payload);
        setCampaign(updated); setAutoSaveLLMSettingsSuccess("LLM settings auto-saved!");
        setTimeout(() => setAutoSaveLLMSettingsSuccess(null), 3000);
      } catch (err) { setAutoSaveLLMSettingsError("Failed to auto-save LLM settings."); }
      finally { setIsAutoSavingLLMSettings(false); }
    }, 1500);
    return () => { if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current); };
  }, [selectedLLMId, temperature, campaignId, campaign, isLoading, setCampaign, setIsAutoSavingLLMSettings, setAutoSaveLLMSettingsError, setAutoSaveLLMSettingsSuccess ]);


  useEffect(() => { // ensureLLMSettingsSaved on selectedLLMId change
    if (initialLoadCompleteRef.current && campaign && selectedLLMId !== campaign.selected_llm_id) {
      ensureLLMSettingsSaved();
    }
  }, [selectedLLMId, campaign, ensureLLMSettingsSaved]);

  useEffect(() => { // ensureLLMSettingsSaved on temperature change
    if (initialLoadCompleteRef.current && campaign && temperature !== null && temperature !== undefined && temperature !== campaign.temperature) {
      ensureLLMSettingsSaved();
    }
  }, [temperature, campaign, ensureLLMSettingsSaved]);


  // useEffect for auto-saving mood board URLs
  useEffect(() => {
    if (!initialLoadCompleteRef.current || !campaignId || !campaign) return;
    if (JSON.stringify(editableMoodBoardUrls) === JSON.stringify(campaign.mood_board_image_urls || [])) return;
    if (moodBoardDebounceTimer) clearTimeout(moodBoardDebounceTimer);
    setIsAutoSavingMoodBoard(true); setAutoSaveMoodBoardError(null); setAutoSaveMoodBoardSuccess(null);
    const newTimer = setTimeout(async () => {
      if (!campaign || !campaign.id) {
        setIsAutoSavingMoodBoard(false); setAutoSaveMoodBoardError("Campaign data missing for mood board save."); return;
      }
      try {
        const payload = { mood_board_image_urls: editableMoodBoardUrls };
        const updated = await campaignService.updateCampaign(campaign.id, payload);
        setCampaign(updated); setAutoSaveMoodBoardSuccess("Mood board auto-saved!");
        setTimeout(() => setAutoSaveMoodBoardSuccess(null), 3000);
      } catch (err) { setAutoSaveMoodBoardError("Failed to auto-save mood board."); }
      finally { setIsAutoSavingMoodBoard(false); }
    }, 1500);
    setMoodBoardDebounceTimer(newTimer);
    return () => { if (newTimer) clearTimeout(newTimer); };
  }, [editableMoodBoardUrls, campaignId, campaign, setCampaign, moodBoardDebounceTimer, initialLoadCompleteRef, setIsAutoSavingMoodBoard, setAutoSaveMoodBoardError, setAutoSaveMoodBoardSuccess, setMoodBoardDebounceTimer]);

  // Effect to fetch campaign files when 'Files' tab is active or campaignId changes
  useEffect(() => {
    let isMounted = true;
    const fetchCampaignFiles = async () => {
      if (!campaignId) {
        if (isMounted) { setCampaignFiles([]); setCampaignFilesError(null); setPrevCampaignIdForFiles(null); }
        return;
      }
      if (activeEditorTab !== 'Files') return;

      const campaignChanged = campaignId !== prevCampaignIdForFiles;
      const initialLoadForThisCampaign = campaignFiles.length === 0 && !campaignFilesError && prevCampaignIdForFiles !== campaignId;

      if ((campaignChanged || initialLoadForThisCampaign) && !campaignFilesLoading) {
        if (isMounted) {
          setCampaignFilesLoading(true); setCampaignFilesError(null);
          if (campaignChanged && campaignFiles.length > 0) setCampaignFiles([]);
        }
        try {
          if (campaignChanged && isMounted) setPrevCampaignIdForFiles(campaignId);
          const files = await getCampaignFiles(campaignId);
          if (isMounted) {
            setCampaignFiles(files);
            if (!campaignChanged) setPrevCampaignIdForFiles(campaignId);
          }
        } catch (err: any) {
          if (isMounted) setCampaignFilesError(err.message || 'Failed to load files.');
        } finally {
          if (isMounted) setCampaignFilesLoading(false);
        }
      }
    };
    fetchCampaignFiles();
    return () => { isMounted = false; };
  }, [activeEditorTab, campaignId, prevCampaignIdForFiles, campaignFilesLoading, campaignFilesError, campaignFiles.length, setCampaignFiles, setCampaignFilesError, setCampaignFilesLoading, setPrevCampaignIdForFiles]);

  // ... (rest of the component, including handlers, tab definitions, and return statement)
  // Ensure all handlers like handleGenerateConceptManually, handleCancelSeeding, etc., are defined before being used.
  // The tab definitions (detailsTabContent, sectionsTabContent, etc.) and the main return statement follow.

  // If `isLoading` (for initial campaign data) is true, show main loader
  if (isLoading) return <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh'}}><LoadingSpinner /><Typography sx={{ml:2}}>Loading Campaign Data...</Typography></div>;
  if (error) return <p className="error-message" style={{textAlign: 'center', marginTop: '20px'}}>{error}</p>;
  if (!campaign) return <p className="error-message" style={{textAlign: 'center', marginTop: '20px'}}>Campaign not found. It might have been deleted or an error occurred.</p>;


  // Define tab content variables before tabItems array
  const detailsTabContent = (
    <>
      <CampaignDetailsEditor
        editableTitle={editableTitle}
        setEditableTitle={setEditableTitle}
        initialPrompt={editableInitialPrompt}
        setInitialPrompt={setEditableInitialPrompt}
        campaignBadgeImage={campaignBadgeImage}
        setCampaignBadgeImage={setCampaignBadgeImage}
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
              <ReactMarkdown components={{ a: TocLinkRenderer }}>{processedToc}</ReactMarkdown>
            )}
            {(!campaign.display_toc || campaign.display_toc.length === 0) && <p>No Table of Contents generated yet.</p>}
            <Button
              onClick={handleGenerateTOC}
              disabled={isGeneratingTOC || !selectedLLMId}
              className="action-button"
              style={{ marginTop: (campaign.display_toc && campaign.display_toc.length > 0) ? '10px' : '0' }}
              icon={<ListAltIcon />}
              tooltip={!selectedLLMId ? "Select an LLM model from Settings tab" : "Generate TOC"}
            >
              {isGeneratingTOC ? 'Generating...' : (campaign.display_toc && campaign.display_toc.length > 0 ? 'Re-generate TOC' : 'Generate TOC')}
            </Button>
            {tocError && <p className="error-message feedback-message" style={{ marginTop: '5px' }}>{tocError}</p>}
            {campaign.display_toc && campaign.display_toc.length > 0 && !isTOCEditorVisible && (
              <Button onClick={() => setIsTOCEditorVisible(true)} icon={<EditIcon />} style={{ marginTop: '10px', display: 'block', marginBottom: '15px' }}>Edit TOC</Button>
            )}
            {campaign.display_toc && campaign.display_toc.length > 0 && (
              <div style={{ marginTop: '15px' }}>
                {!isDetailedProgressVisible ? (
                  <>
                    <Button onClick={handleSeedSectionsFromToc} disabled={isSeedingSections} icon={<AddCircleOutlineIcon />}>
                      {isSeedingSections ? (autoPopulateSections ? 'Creating & Populating...' : 'Creating Sections...') : 'Approve TOC & Create Sections'}
                    </Button>
                    {!isDetailedProgressVisible && seedSectionsError && <p className="error-message feedback-message" style={{ marginTop: '5px' }}>{seedSectionsError}</p>}
                    <div style={{ marginTop: '10px', marginBottom: '10px' }}>
                      <label htmlFor="autoPopulateCheckbox" style={{ marginRight: '8px' }}>Auto-populate sections:</label>
                      <input type="checkbox" id="autoPopulateCheckbox" checked={autoPopulateSections} onChange={e => setAutoPopulateSections(e.target.checked)} disabled={isSeedingSections} />
                    </div>
                  </>
                ) : (
                  <>
                    <DetailedProgressDisplay percent={detailedProgressPercent} currentTitle={detailedProgressCurrentTitle} error={seedSectionsError} title="Seeding Sections..." />
                    <Button onClick={handleCancelSeeding} style={{ marginTop: '10px' }} icon={<CancelIcon />} disabled={!isSeedingSections}>Cancel</Button>
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </section>
      {isTOCEditorVisible && (
        <section className="campaign-detail-section editor-section" style={{ marginTop: '20px' }}>
          <TOCEditor toc={editableDisplayTOC} onTOCChange={handleTOCEditorChange} />
          <Button onClick={handleTOCSaveChanges} disabled={isSavingTOC} variant="primary" style={{ marginTop: '10px' }}>
            {isSavingTOC ? 'Saving TOC...' : 'Save TOC Changes'}
          </Button>
          <Button onClick={() => setIsTOCEditorVisible(false)} variant="secondary" style={{ marginTop: '10px', marginLeft: '10px' }}>Done Editing TOC</Button>
        </section>
      )}
      {tocSaveError && <p className="error-message feedback-message">{tocSaveError}</p>}
      {tocSaveSuccess && <p className="success-message feedback-message">{tocSaveSuccess}</p>}
      <div className="action-group export-action-group editor-section">
        <Button onClick={handleExportHomebrewery} disabled={isExporting} icon={<PublishIcon />}>
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
        <Button onClick={() => setForceCollapseAll(true)} icon={<UnfoldLessIcon />}>Collapse All</Button>
        <Button onClick={() => setForceCollapseAll(false)} icon={<UnfoldMoreIcon />}>Expand All</Button>
        <Button onClick={() => setIsAddSectionCollapsed(!isAddSectionCollapsed)} disabled={!campaign?.concept?.trim()} icon={<AddCircleOutlineIcon />}>
          Add New Section
        </Button>
      </div>
      {!isAddSectionCollapsed && campaign?.concept?.trim() && (
        <div className="editor-actions add-section-area editor-section card-like" style={{ marginTop: '20px' }}>
          <h3>Add New Section</h3>
          <form onSubmit={handleAddSection} className="add-section-form">
            <div className="form-group">
              <label htmlFor="newSectionTitle">Title (Optional):</label>
              <input type="text" id="newSectionTitle" value={newSectionTitle} onChange={e => setNewSectionTitle(e.target.value)} />
            </div>
            <div className="form-group">
              <label htmlFor="newSectionPrompt">Prompt (Optional):</label>
              <textarea id="newSectionPrompt" value={newSectionPrompt} onChange={e => setNewSectionPrompt(e.target.value)} rows={3} />
            </div>
            {selectedLLMObject && <p>Using LLM: <strong>{selectedLLMObject.name}</strong></p>}
            {addSectionError && <p className="error-message feedback-message">{addSectionError}</p>}
            {addSectionSuccess && <p className="success-message feedback-message">{addSectionSuccess}</p>}
            <Button type="submit" disabled={isAddingSection || !selectedLLMId || !campaign?.concept?.trim()} icon={<AddCircleOutlineIcon />}>
              {isAddingSection ? 'Adding...' : 'Confirm & Add'}
            </Button>
            <Button type="button" onClick={() => setIsAddSectionCollapsed(true)} icon={<CancelIcon />} style={{marginLeft: '10px'}}>Cancel</Button>
          </form>
        </div>
      )}
      <CampaignSectionEditor
        campaignId={campaignId!} sections={sections} setSections={setSections}
        handleDeleteSection={handleDeleteSection} handleUpdateSectionContent={handleUpdateSectionContent}
        handleUpdateSectionTitle={handleUpdateSectionTitle} handleUpdateSectionType={handleUpdateSectionType}
        onUpdateSectionOrder={handleUpdateSectionOrder} forceCollapseAllSections={forceCollapseAll}
        expandSectionId={sectionToExpand} onSetThematicImageForSection={handleSetThematicImage}
      />
      {!campaign?.concept?.trim() && (
        <div className="editor-section user-message card-like" style={{ marginTop: '20px', padding: '15px', textAlign: 'center' }}>
          <Typography variant="h6" color="textSecondary">Define concept in 'Details' tab first.</Typography>
        </div>
      )}
    </>
  );

  const settingsTabContent = (
    <>
      {isLLMsLoading ? (
        <div className="editor-section" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
          <LoadingSpinner /><Typography sx={{ ml: 2 }}>Loading LLMs...</Typography>
        </div>
      ) : selectedLLMObject && availableLLMs.length > 0 ? (
        <CampaignLLMSettings
          selectedLLM={selectedLLMObject} setSelectedLLM={handleSetSelectedLLM}
          temperature={temperature} setTemperature={setTemperature}
          availableLLMs={availableLLMs.map(m => ({...m, name: m.name || m.id})) as LLM[]}
        />
      ) : !selectedLLMObject && availableLLMs.length > 0 ? (
        <div className="editor-section">
          <p>No LLM selected.</p>
          <Button onClick={() => setIsLLMDialogOpen(true)} icon={<SettingsSuggestIcon />}>Select LLM</Button>
        </div>
      ) : (
        <div className="editor-section"><Typography>No LLMs available.</Typography></div>
      )}
      <div className="llm-autosave-feedback editor-section feedback-messages">
        {isAutoSavingLLMSettings && <p className="feedback-message saving-indicator">Auto-saving LLM settings...</p>}
        {autoSaveLLMSettingsError && <p className="error-message feedback-message">{autoSaveLLMSettingsError}</p>}
        {autoSaveLLMSettingsSuccess && <p className="success-message feedback-message">{autoSaveLLMSettingsSuccess}</p>}
      </div>
      {tocError && <p className="error-message llm-feedback editor-section">{tocError}</p>}
    </>
  );

  // Define filesTabContent before tabItems array
  const filesTabContent = (
    <div className="editor-section campaign-files-tab">
      <h3>Campaign Files</h3>
      {campaignFilesLoading && (
        <div className="spinner-container files-loading-spinner" style={{ marginTop: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <LoadingSpinner />
          <p>Loading campaign files...</p>
        </div>
      )}
      {campaignFilesError && <div className="message error" style={{ marginTop: '20px' }}>{campaignFilesError}</div>}
      {!campaignFilesLoading && !campaignFilesError && campaignFiles.length === 0 && (
        <p style={{ marginTop: '20px' }}>No files found for this campaign.</p>
      )}
      {!campaignFilesLoading && !campaignFilesError && campaignFiles.length > 0 && (
        <ul className="user-files-list">
          {campaignFiles.map((file) => (
            <li key={file.name + file.last_modified} className="user-file-item">
              <span className="file-icon-container">
                {renderFileRepresentation(file)}
              </span>
              <a href={file.url} target="_blank" rel="noopener noreferrer" className="user-file-link" title={`Click to open ${file.name}`}>
                {file.name}
              </a>
              <span className="file-metadata">
                ({formatBytes(file.size)}
                {file.content_type && `, ${file.content_type}`}
                , Last Modified: {new Date(file.last_modified).toLocaleDateString()})
              </span>
            </li>
          ))}
        </ul>
      )}
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
          currentThematicImageUrl={campaign?.thematic_image_url}
        />
      )
    },
    { name: 'Settings', content: settingsTabContent },
  ];
  tabItems.push({ name: 'Files', content: filesTabContent });


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
        {isAutoSavingMoodBoard && <p className="feedback-message saving-indicator" style={{marginRight: '10px', fontSize: '0.8em'}}>Auto-saving...</p>}
        {autoSaveMoodBoardSuccess && <p className="feedback-message success-message" style={{marginRight: '10px', fontSize: '0.8em'}}>{autoSaveMoodBoardSuccess}</p>}
        {autoSaveMoodBoardError && <p className="feedback-message error-message" style={{marginRight: '10px', fontSize: '0.8em'}}>{autoSaveMoodBoardError}</p>}
      </div>
      {campaign && campaign.title && (
        <h1 className="campaign-main-title">{campaign.title}</h1>
      )}

      {campaign && !campaign.concept && !isConceptEditorVisible && (
        <section className="campaign-detail-section editor-section page-level-concept generate-concept-area">
          <Typography variant="body1" sx={{ mb: 1 }}>This campaign needs a concept.</Typography>
          <Button onClick={handleGenerateConceptManually} disabled={isGeneratingConceptManually || !campaign.selected_llm_id} variant="primary" icon={<SettingsSuggestIcon />}>
            {isGeneratingConceptManually ? 'Generating...' : 'Generate Concept'}
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
            <Button onClick={() => { setEditableConcept(campaign.concept || ''); setIsConceptEditorVisible(true); setIsCampaignConceptCollapsed(false); setConceptSaveError(null); setConceptSaveSuccess(null);}} icon={<EditIcon />} style={{minWidth: 'auto', padding: '4px', marginLeft: '10px'}} tooltip="Edit Concept">Edit</Button>
          </div>
          {!isCampaignConceptCollapsed && <div className="concept-content"><ReactMarkdown>{campaign.concept}</ReactMarkdown></div>}
        </section>
      )}

      {isConceptEditorVisible && campaign && (
        <section className="campaign-detail-section editor-section page-level-concept edit-concept-section card-like">
          <h2>Edit Campaign Concept</h2>
          <TextField
            label="Campaign Concept" multiline rows={6} fullWidth value={editableConcept}
            onChange={e => setEditableConcept(e.target.value)} variant="outlined" margin="normal"
            helperText={conceptSaveError || conceptSaveSuccess || "Enter the core concept."}
            error={!!conceptSaveError}
            sx={{ '& .MuiFormHelperText-root': { color: conceptSaveError ? 'error.main' : (conceptSaveSuccess ? 'success.main' : 'text.secondary'),}}}
          />
          <div className="action-group" style={{ marginTop: '10px', display: 'flex', gap: '10px' }}>
            <Button onClick={async () => {
                if (!campaignId || !campaign) return; setIsPageLoading(true); setConceptSaveError(null); setConceptSaveSuccess(null);
                try {
                  const updated = await campaignService.updateCampaign(campaignId, { concept: editableConcept });
                  setCampaign(updated); setConceptSaveSuccess("Concept updated!"); setTimeout(() => setConceptSaveSuccess(null), 3000);
                  setIsConceptEditorVisible(false);
                } catch (err) { setConceptSaveError("Failed to save concept."); }
                finally { setIsPageLoading(false); }
              }} variant="primary" icon={<SaveIcon />} disabled={isPageLoading || editableConcept === campaign.concept}>Save Concept</Button>
            <Button onClick={() => { setIsConceptEditorVisible(false); setConceptSaveError(null); }} variant="secondary" icon={<CancelIcon />} disabled={isPageLoading}>Cancel</Button>
          </div>
        </section>
      )}

      <Tabs tabs={tabItems} activeTabName={activeEditorTab} onTabChange={setActiveEditorTab} />

      {isMoodBoardPanelOpen && (
        <div className="mood-board-side-panel" style={{ width: `${moodBoardPanelWidth}px` }}>
          <MoodBoardPanel
            moodBoardUrls={editableMoodBoardUrls} isLoading={false} error={null}
            isVisible={isMoodBoardPanelOpen} onClose={() => setIsMoodBoardPanelOpen(false)}
            title="Mood Board" onUpdateMoodBoardUrls={setEditableMoodBoardUrls}
            campaignId={campaignId!} onRequestOpenGenerateImageModal={() => setIsGeneratingForMoodBoard(true)}
            currentPanelWidth={moodBoardPanelWidth} onResize={handleMoodBoardResize}
          />
        </div>
      )}

      <LLMSelectionDialog
        isOpen={isLLMDialogOpen} currentModelId={selectedLLMId}
        onModelSelect={modelId => { if (modelId) setSelectedLLMId(modelId); setIsLLMDialogOpen(false); }}
        onClose={() => setIsLLMDialogOpen(false)}
      />
      <ImageGenerationModal
        isOpen={isBadgeImageModalOpen} onClose={() => setIsBadgeImageModalOpen(false)}
        onImageSuccessfullyGenerated={handleBadgeImageGenerated} onSetAsThematic={handleSetThematicImage}
        primaryActionText="Set as Badge Image" autoApplyDefault={true}
      />
      <SuggestedTitlesModal
        isOpen={isSuggestedTitlesModalOpen} onClose={() => setIsSuggestedTitlesModalOpen(false)}
        titles={suggestedTitles || []} onSelectTitle={handleTitleSelected}
      />
      <ImageGenerationModal
        isOpen={isGeneratingForMoodBoard} onClose={() => setIsGeneratingForMoodBoard(false)}
        onImageSuccessfullyGenerated={(imageUrl, promptUsed) => {
          setEditableMoodBoardUrls(prev => [...prev, imageUrl]);
          setIsGeneratingForMoodBoard(false);
        }}
        onSetAsThematic={() => { /* No-op for mood board context */ }}
        primaryActionText="Add to Mood Board" autoApplyDefault={true}
      />
    </div>
  );
};
export default CampaignEditorPage;

[end of campaign_crafter_ui/src/pages/CampaignEditorPage.tsx]
