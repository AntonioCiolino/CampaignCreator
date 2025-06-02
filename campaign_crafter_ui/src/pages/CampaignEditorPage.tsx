import React, { useState, useEffect, FormEvent, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import LLMSelectionDialog from '../components/modals/LLMSelectionDialog';
import ImageGenerationModal from '../components/modals/ImageGenerationModal/ImageGenerationModal';
import * as campaignService from '../services/campaignService';
import { getAvailableLLMs, LLMModel } from '../services/llmService';
// CampaignSectionView will be used by CampaignSectionEditor
// import CampaignSectionView from '../components/CampaignSectionView'; 
import ReactMarkdown from 'react-markdown';
import './CampaignEditorPage.css';

// New Component Imports
import CampaignDetailsEditor from '../components/campaign_editor/CampaignDetailsEditor';
import CampaignLLMSettings from '../components/campaign_editor/CampaignLLMSettings';
import CampaignSectionEditor from '../components/campaign_editor/CampaignSectionEditor';
import { LLMModel as LLM } from '../services/llmService'; // Corrected LLM import
import Tabs, { TabItem } from '../components/common/Tabs'; // Import Tabs component
import { Box, Typography } from '@mui/material'; // For layout within tabs if needed

const CampaignEditorPage: React.FC = () => {
  const { campaignId } = useParams<{ campaignId: string }>();
  const [campaign, setCampaign] = useState<campaignService.Campaign | null>(null);
  const [sections, setSections] = useState<campaignService.CampaignSection[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Editable campaign details
  const [editableTitle, setEditableTitle] = useState<string>('');
  const [editableInitialPrompt, setEditableInitialPrompt] = useState<string>('');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Section-specific saving
  const [savingSectionId, setSavingSectionId] = useState<number | null>(null);
  const [sectionSaveError, setSectionSaveError] = useState<{ [key: number]: string | null }>({});

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
  const [isLLMSettingsCollapsed, setIsLLMSettingsCollapsed] = useState<boolean>(false);
  const [isAddSectionCollapsed, setIsAddSectionCollapsed] = useState<boolean>(true);
  const [isLLMDialogOpen, setIsLLMDialogOpen] = useState<boolean>(false);
  // isCampaignDetailsCollapsed will be managed by the new component or removed if not needed at page level
  const [isBadgeImageModalOpen, setIsBadgeImageModalOpen] = useState(false); // Added for modal

  // State for badge image updates
  // badgeUpdateLoading, setBadgeUpdateLoading, badgeUpdateError, setBadgeUpdateError will be managed by CampaignDetailsEditor (or passed to it)
  // For now, we keep them here if they are used by functions like handleBadgeImageGenerated that remain in this file.
  const [badgeUpdateLoading, setBadgeUpdateLoading] = useState(false);
  const [badgeUpdateError, setBadgeUpdateError] = useState<string | null>(null);

  // campaignBadgeImage and setCampaignBadgeImage for CampaignDetailsEditor
  // This state is initialized from `campaign.badge_image_url` in useEffect
  const [campaignBadgeImage, setCampaignBadgeImage] = useState<string>('');

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
    if (!campaign?.toc || !sections?.length) {
      return campaign?.toc || '';
    }
    const tocLines = campaign.toc.split('\n');
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
  }, [campaign?.toc, sections]);

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

        setAvailableLLMs(fetchedLLMs); // fetchedLLMs is now LLMModel[]

        // This filter should now work correctly with LLMModel type
        const potentialChatModels = fetchedLLMs.filter(model =>
            model.capabilities && (model.capabilities.includes("chat") || model.capabilities.includes("chat-adaptable"))
        );

        if (potentialChatModels.length > 0) {
            let defaultChatModel = potentialChatModels.find(m => m.id === "openai/gpt-3.5-turbo");
            if (!defaultChatModel) {
                defaultChatModel = potentialChatModels.find(m => m.id === "openai/gpt-4");
            }
            if (!defaultChatModel) {
                defaultChatModel = potentialChatModels.find(m => m.id === "gemini/gemini-pro");
            }
            if (!defaultChatModel) {
                defaultChatModel = potentialChatModels[0];
            }
            setSelectedLLMId(defaultChatModel.id);
        } else if (fetchedLLMs.length > 0) {
            setSelectedLLMId(fetchedLLMs[0].id);
        } else {
            setSelectedLLMId('');
        }
      } catch (err) {
        console.error('Failed to fetch initial campaign or LLM data:', err);
        setError('Failed to load initial data. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchInitialData();
  }, [campaignId]);

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
    setIsSaving(true);
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
      setIsSaving(false);
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

    try {
      await campaignService.updateCampaignSectionOrder(campaignId, orderedSectionIds);
      setSaveSuccess("Section order saved successfully!"); // Provide feedback
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (error) {
      console.error("Failed to update section order:", error);
      setError("Failed to save section order. Please try again."); // Show error feedback
      setSections(oldSections); // Revert optimistic update on error
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

    setBadgeUpdateLoading(true);
    setBadgeUpdateError(null);
    setIsBadgeImageModalOpen(false); // Close modal immediately

    try {
      const updatedCampaignData = { badge_image_url: imageUrl };
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      
      if (typeof setCampaign === 'function') { // setCampaign should be available from useState [campaign, setCampaign]
          setCampaign(updatedCampaign);
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
    }
  };

  const handleDeleteSection = async (sectionId: number) => {
    if (!campaignId) return;

    if (window.confirm(`Are you sure you want to delete section ${sectionId}? This action cannot be undone.`)) {
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
    }
  };

  const handleUpdateSection = async (sectionId: number, updatedData: campaignService.CampaignSectionUpdatePayload) => {
    if (!campaignId) return;
    setSavingSectionId(sectionId);
    setSectionSaveError(prev => ({ ...prev, [sectionId]: null }));
    try {
      const updatedSection = await campaignService.updateCampaignSection(campaignId, sectionId, updatedData);
      setSections(prev => prev.map(sec => sec.id === sectionId ? updatedSection : sec));
    } catch (err) {
      setSectionSaveError(prev => ({ ...prev, [sectionId]: 'Failed to save section.' }));
      throw err;
    } finally {
      setSavingSectionId(null);
    }
  };

  const handleGenerateTOC = async () => {
    if (!campaignId) return;
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
    }
  };

  const handleGenerateTitles = async () => {
    if (!campaignId) return;
    setIsGeneratingTitles(true);
    setTitlesError(null);
    setSuggestedTitles(null);
    setSaveSuccess(null);
    try {
      const response = await campaignService.generateCampaignTitles(campaignId, {}, 5);
      setSuggestedTitles(response.titles);
      setSaveSuccess("Suggested titles generated successfully!");
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err) {
      setTitlesError('Failed to generate titles.');
    } finally {
      setIsGeneratingTitles(false);
    }
  };
  
  const hasChanges = campaign ? (editableTitle !== campaign.title || editableInitialPrompt !== (campaign.initial_user_prompt || '')) : false;

  const handleExportHomebrewery = async () => {
    if (!campaignId || !campaign) return;

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
    
    setBadgeUpdateLoading(true);
    setBadgeUpdateError(null);
    try {
      const updatedCampaignData = { badge_image_url: imageUrl.trim() === "" ? null : imageUrl.trim() };
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      
      if (typeof setCampaign === 'function') { 
          setCampaign(updatedCampaign);
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
    }
  };

  const handleRemoveBadgeImage = async () => {
    if (!campaign || !campaign.badge_image_url) return;

    if (!window.confirm("Are you sure you want to remove the campaign badge image?")) return;

    setBadgeUpdateLoading(true);
    setBadgeUpdateError(null);
    try {
      const updatedCampaignData = { badge_image_url: null }; // Set to null to remove
      const updatedCampaign = await campaignService.updateCampaign(campaign.id, updatedCampaignData);
      
      if (typeof setCampaign === 'function') {
          setCampaign(updatedCampaign);
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
    }
  };


  if (isLoading) return <p className="loading-message">Loading campaign details...</p>;
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
      />
      {/* Global save error/success can be shown here or above tabs */}
      {saveError && <p className="error-message save-feedback">{saveError}</p>}
      {saveSuccess && <p className="success-message save-feedback">{saveSuccess}</p>}

      <div className="campaign-badge-area editor-section">
        <h3>Campaign Badge Actions</h3>
        {campaign.badge_image_url && (
          <Box sx={{ mt: 1, mb: 1, textAlign: 'center' }}>
            <Typography variant="caption" display="block" gutterBottom>
              Current Badge:
            </Typography>
            <img
              src={campaign.badge_image_url}
              alt="Campaign Badge"
              style={{ maxWidth: '100px', maxHeight: '100px', border: '1px solid #ccc' }}
            />
          </Box>
        )}
        <div className="campaign-badge-actions">
          <button onClick={handleOpenBadgeImageModal} disabled={badgeUpdateLoading} className="action-button">
            {badgeUpdateLoading ? "Processing..." : "Generate New Badge"}
          </button>
          <button onClick={handleEditBadgeImageUrl} disabled={badgeUpdateLoading} className="action-button secondary-action-button">
            {badgeUpdateLoading ? "Processing..." : "Edit Badge URL"}
          </button>
          {campaign?.badge_image_url && (
            <button
              onClick={handleRemoveBadgeImage}
              disabled={badgeUpdateLoading || !campaign?.badge_image_url}
              className="action-button remove-button"
            >
              {badgeUpdateLoading ? "Removing..." : "Remove Badge"}
            </button>
          )}
        </div>
        {badgeUpdateError && <p className="error-message feedback-message">{badgeUpdateError}</p>}
      </div>

      {campaign.concept && (
        <section className="campaign-detail-section read-only-section editor-section">
          <h2>Campaign Concept (Read-Only)</h2>
          <div className="concept-content"><ReactMarkdown>{campaign.concept}</ReactMarkdown></div>
        </section>
      )}
      {campaign.toc && (
        <section className="campaign-detail-section read-only-section editor-section">
          <h2>Table of Contents (Read-Only)</h2>
          <div className="toc-content"><ReactMarkdown>{processedToc}</ReactMarkdown></div>
        </section>
      )}
    </>
  );

  const sectionsTabContent = (
    <>
      <div className="section-display-controls editor-section">
        <h3>Section Display</h3>
        <button onClick={() => setForceCollapseAll(true)} className="action-button">Collapse All Sections</button>
        <button onClick={() => setForceCollapseAll(false)} className="action-button">Expand All Sections</button>
        <button onClick={() => setForceCollapseAll(undefined)} className="action-button secondary-action-button">Enable Individual Toggling</button>
      </div>
      <CampaignSectionEditor
        sections={sections}
        setSections={setSections}
        handleAddNewSection={() => setIsAddSectionCollapsed(false)}
        handleDeleteSection={handleDeleteSection}
        handleUpdateSectionContent={handleUpdateSectionContent}
        handleUpdateSectionTitle={handleUpdateSectionTitle}
        onUpdateSectionOrder={handleUpdateSectionOrder} // Pass the new handler
        // TODO: Pass savingSectionId, sectionSaveError, forceCollapseAll if CSE is updated to use them
      />
      {!isAddSectionCollapsed && (
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
            <button type="submit" disabled={isAddingSection || !selectedLLMId} className="action-button add-section-button">
              {isAddingSection ? 'Adding Section...' : 'Confirm & Add Section'}
            </button>
            <button type="button" onClick={() => setIsAddSectionCollapsed(true)} className="action-button secondary-action-button" style={{marginLeft: '10px'}}>
              Cancel
            </button>
          </form>
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
          isGeneratingTOC={isGeneratingTOC}
          handleGenerateTOC={handleGenerateTOC}
          isGeneratingTitles={isGeneratingTitles}
          handleGenerateTitles={handleGenerateTitles}
          availableLLMs={availableLLMs.map(m => ({...m, name: m.name || m.id})) as LLM[]}
        />
      ) : (
        <div className="editor-section">
          <p>Loading LLM settings or no LLMs available...</p>
          {!selectedLLMId && availableLLMs.length > 0 && (
            <button onClick={() => setIsLLMDialogOpen(true)} className="action-button">
              Select Initial LLM Model
            </button>
          )}
        </div>
      )}
      {/* LLM related errors can be shown within this tab or globally */}
      {tocError && <p className="error-message llm-feedback editor-section">{tocError}</p>}
      {titlesError && <p className="error-message llm-feedback editor-section">{titlesError}</p>}

      {suggestedTitles && suggestedTitles.length > 0 && (
        <section className="suggested-titles-section editor-section">
          <h3>Suggested Titles:</h3>
          <ul className="titles-list">
            {suggestedTitles.map((title, index) => (<li key={index} className="title-item">{title}</li>))}
          </ul>
          <button onClick={() => setSuggestedTitles(null)} className="dismiss-titles-button">Dismiss</button>
        </section>
      )}

      <div className="action-group export-action-group editor-section"> 
        <button onClick={handleExportHomebrewery} disabled={isExporting} className="llm-button export-button">
          {isExporting ? 'Exporting...' : 'Export to Homebrewery'}
        </button>
        {exportError && <p className="error-message llm-feedback">{exportError}</p>}
      </div>
    </>
  );

  const tabItems: TabItem[] = [
    { name: 'Details', content: detailsTabContent },
    { name: 'Sections', content: sectionsTabContent },
    { name: 'Settings', content: settingsTabContent },
  ];

  return (
    <div className="campaign-editor-page">
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
    </div>
  );
};

export default CampaignEditorPage;

// Note: The redundant LLMModel type alias (campaignService.ModelInfo) was already addressed by using LLMModel from llmService.
