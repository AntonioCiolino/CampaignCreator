import React, { useState, useEffect, FormEvent, useMemo, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import LoadingSpinner from '../components/common/LoadingSpinner';
import LLMSelectionDialog from '../components/modals/LLMSelectionDialog';
import ImageGenerationModal from '../components/modals/ImageGenerationModal/ImageGenerationModal';
import SuggestedTitlesModal from '../components/modals/SuggestedTitlesModal';
import * as campaignService from '../services/campaignService';
import { Campaign, CampaignSection, TOCEntry, SeedSectionsProgressEvent, SeedSectionsCallbacks } from '../services/campaignService';
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

import CampaignDetailsEditor from '../components/campaign_editor/CampaignDetailsEditor';
import CampaignLLMSettings from '../components/campaign_editor/CampaignLLMSettings';
import CampaignSectionEditor from '../components/campaign_editor/CampaignSectionEditor';
import { LLMModel as LLM } from '../services/llmService';
import Tabs, { TabItem } from '../components/common/Tabs';
import { Typography } from '@mui/material';
import DetailedProgressDisplay from '../components/common/DetailedProgressDisplay';
import TOCEditor from '../components/campaign_editor/TOCEditor';

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
  const [selectedLLMId, setSelectedLLMId] = useState<string>('');
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

  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);
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

  const selectedLLMObject = useMemo(() => {
    if (availableLLMs.length > 0 && selectedLLMId) {
      return availableLLMs.find(llm => llm.id === selectedLLMId) as LLM | undefined;
    }
    return undefined;
  }, [selectedLLMId, availableLLMs]);

  const handleSetSelectedLLM = (llm: LLM) => {
    setSelectedLLMId(llm.id);
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
      const cleanedTitle = title.trim().toLowerCase();
      const sectionId = sectionTitleToIdMap.get(cleanedTitle);
      if (sectionId && sections?.length > 0) {
        return `- [${title}](#${sectionId})`;
      }
      return `- ${title}`;
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

  useEffect(() => {
    if (!campaignId) {
      setError('Campaign ID is missing.');
      setIsLoading(false);
      return;
    }
    const fetchInitialData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [campaignDetails, campaignSectionsResponse, fetchedLLMs] = await Promise.all([
          campaignService.getCampaignById(campaignId),
          campaignService.getCampaignSections(campaignId),
          getAvailableLLMs(),
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
        setAvailableLLMs(fetchedLLMs);
        let newSelectedLLMIdToSave: string | null = null;
        if (campaignDetails.selected_llm_id) {
            setSelectedLLMId(campaignDetails.selected_llm_id);
        } else {
            const preferredModelIds = ["openai/gpt-4.1-nano", "openai/gpt-3.5-turbo", "openai/gpt-4", "gemini/gemini-pro"];
            let newSelectedLLMId = '';
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
            if (!newSelectedLLMId && fetchedLLMs.length > 0) { newSelectedLLMId = fetchedLLMs[0].id; }
            if (newSelectedLLMId) {
                setSelectedLLMId(newSelectedLLMId);
                if (!campaignDetails.selected_llm_id) { newSelectedLLMIdToSave = newSelectedLLMId; }
            }
        }
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
        initialLoadCompleteRef.current = true;
      } catch (err) {
        console.error('Failed to fetch initial campaign or LLM data:', err);
        setError('Failed to load initial data. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchInitialData();
  }, [campaignId]);

  useEffect(() => {
    if (!initialLoadCompleteRef.current || !campaignId || !campaign || isLoading) {
        return;
    }
    if (debounceTimer) { clearTimeout(debounceTimer); }
    const newTimer = setTimeout(async () => {
        if (!campaign || !campaign.id) { return; }
        if (selectedLLMId === campaign.selected_llm_id && temperature === campaign.temperature) { return; }
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
    }, 1500);
    setDebounceTimer(newTimer);
    return () => { if (newTimer) { clearTimeout(newTimer); } };
  }, [selectedLLMId, temperature, campaignId, campaign, isLoading, debounceTimer, ensureLLMSettingsSaved]);

  useEffect(() => {
    if (!initialLoadCompleteRef.current || !campaign) { return; }
    if (selectedLLMId && selectedLLMId !== campaign.selected_llm_id) {
      ensureLLMSettingsSaved();
    }
  }, [selectedLLMId, campaign, ensureLLMSettingsSaved]);

  useEffect(() => {
    if (!initialLoadCompleteRef.current || !campaign) { return; }
    if (temperature !== null && temperature !== campaign.temperature) {
      ensureLLMSettingsSaved();
    }
  }, [temperature, campaign, ensureLLMSettingsSaved]);

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
    if (editableTitle === campaign.title && editableInitialPrompt === (campaign.initial_user_prompt || '')) {
      setSaveSuccess("No changes to save.");
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
        homebrewery_toc: editableDisplayTOC,
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
            {campaign.display_toc && campaign.display_toc.length > 0 && <ReactMarkdown>{processedToc}</ReactMarkdown>}
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
              variant="outlined"
              style={{ marginTop: '10px', marginLeft: '10px' }}
          >
              Done Editing TOC
          </Button>
          {tocSaveError && <p className="error-message feedback-message">{tocSaveError}</p>}
          {tocSaveSuccess && <p className="success-message feedback-message">{tocSaveSuccess}</p>}
        </section>
      )}
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
      </div>
      <CampaignSectionEditor
        campaignId={campaignId!}
        sections={sections}
        setSections={setSections}
        handleAddNewSection={() => setIsAddSectionCollapsed(false)}
        isAddSectionDisabled={!campaign?.concept?.trim()}
        handleDeleteSection={handleDeleteSection}
        handleUpdateSectionContent={handleUpdateSectionContent}
        handleUpdateSectionTitle={handleUpdateSectionTitle}
        handleUpdateSectionType={handleUpdateSectionType}
        onUpdateSectionOrder={handleUpdateSectionOrder}
        forceCollapseAllSections={forceCollapseAll}
      />
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
            <Button onClick={() => setIsLLMDialogOpen(true)} className="action-button" icon={<SettingsSuggestIcon />} tooltip="Select the primary Language Model for campaign generation tasks">
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
      {tocError && <p className="error-message llm-feedback editor-section">{tocError}</p>}
      <div className="action-group export-action-group editor-section">
        <Button onClick={handleExportHomebrewery} disabled={isExporting} className="llm-button export-button" icon={<PublishIcon />} tooltip="Export the campaign content as Markdown formatted for Homebrewery">
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
      {campaign && campaign.title && (
        <h1 className="campaign-main-title">{campaign.title}</h1>
      )}
      {campaign && campaign.concept && (
        <section className="campaign-detail-section read-only-section editor-section page-level-concept">
          <h2 onClick={() => setIsCampaignConceptCollapsed(!isCampaignConceptCollapsed)} style={{ cursor: 'pointer' }}>
            {isCampaignConceptCollapsed ? '▶' : '▼'} Campaign Concept
          </h2>
          {!isCampaignConceptCollapsed && (
            <div className="concept-content"><ReactMarkdown>{campaign.concept}</ReactMarkdown></div>
          )}
        </section>
      )}
      <Tabs tabs={tabItems} />
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
      />
      <SuggestedTitlesModal
        isOpen={isSuggestedTitlesModalOpen}
        onClose={() => { setIsSuggestedTitlesModalOpen(false); }}
        titles={suggestedTitles || []}
        onSelectTitle={handleTitleSelected}
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

[end of campaign_crafter_ui/src/pages/CampaignEditorPage.tsx]
