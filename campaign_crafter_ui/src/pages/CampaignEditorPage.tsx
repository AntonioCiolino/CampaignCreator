import React, { useState, useEffect, FormEvent, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import LLMSelectionDialog from '../components/modals/LLMSelectionDialog';
import * as campaignService from '../services/campaignService';
import { getAvailableLLMs, LLMModel } from '../services/llmService'; // Corrected import
import CampaignSectionView from '../components/CampaignSectionView';
import ReactMarkdown from 'react-markdown';
import './CampaignEditorPage.css'; 

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
  const [isCampaignDetailsCollapsed, setIsCampaignDetailsCollapsed] = useState<boolean>(true); // Default to true

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

  if (isLoading) return <p className="loading-message">Loading campaign details...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!campaign) return <p className="error-message">Campaign not found.</p>;

  return (
    <div className="campaign-editor-page">
      <div className="campaign-main-details-section editor-section">
        <h2 onClick={() => setIsCampaignDetailsCollapsed(!isCampaignDetailsCollapsed)} style={{ cursor: 'pointer' }}>
          {isCampaignDetailsCollapsed ? '▶' : '▼'} Campaign Details & Overview
        </h2>
        {!isCampaignDetailsCollapsed && (
          <>
            <header className="campaign-header editor-section">
              <label htmlFor="campaignTitle" className="form-label">Campaign Title:</label>
              <input type="text" id="campaignTitle" className="form-input form-input-title" value={editableTitle} onChange={(e) => setEditableTitle(e.target.value)} />
            </header>

            <section className="campaign-detail-section editor-section">
              <label htmlFor="campaignInitialPrompt" className="form-label">Initial User Prompt:</label>
              <textarea id="campaignInitialPrompt" className="form-textarea" value={editableInitialPrompt} onChange={(e) => setEditableInitialPrompt(e.target.value)} rows={5} />
            </section>

            <div className="save-actions editor-section">
              <button onClick={handleSaveChanges} disabled={isSaving || !hasChanges} className="save-button main-save-button">
                {isSaving ? 'Saving Details...' : 'Save Campaign Details'}
              </button>
              {saveError && <p className="error-message save-feedback">{saveError}</p>}
              {saveSuccess && <p className="success-message save-feedback">{saveSuccess}</p>}
            </div>

            {campaign.concept && (
              <section className="campaign-detail-section read-only-section">
                <h2>Campaign Concept (Read-Only)</h2>
                <div className="concept-content"><ReactMarkdown>{campaign.concept}</ReactMarkdown></div>
              </section>
            )}
            {campaign.toc && (
              <section className="campaign-detail-section read-only-section">
                <h2>Table of Contents (Read-Only)</h2>
                <div className="toc-content"><ReactMarkdown>{processedToc}</ReactMarkdown></div>
              </section>
            )}
          </>
        )}
      </div>

      <div className="llm-settings-and-actions editor-section">
        <h3 onClick={() => setIsLLMSettingsCollapsed(!isLLMSettingsCollapsed)} style={{ cursor: 'pointer' }}>
          {isLLMSettingsCollapsed ? '▶' : '▼'} LLM Settings & Actions
        </h3>
        {!isLLMSettingsCollapsed && (
          <>
            <div className="llm-controls">
              <div className="form-group">
                <label>Selected LLM Model:</label>
                <div className="selected-llm-display">
                  <span>{selectedLLMId ? (availableLLMs.find(m => m.id === selectedLLMId)?.name || selectedLLMId) : 'None Selected'}</span>
                  <button onClick={() => setIsLLMDialogOpen(true)} className="button-link change-llm-button">
                    (Change)
                  </button>
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="temperatureRange">Temperature: {temperature.toFixed(1)}</label>
            <input type="range" id="temperatureRange" min="0" max="2" step="0.1" value={temperature} onChange={(e) => setTemperature(parseFloat(e.target.value))} className="form-range"/>
          </div>
        </div>
        <div className="llm-actions">
          <div className="action-group">
            <button onClick={handleGenerateTOC} disabled={isGeneratingTOC || !campaign?.concept || !selectedLLMId} className="llm-button">
              {isGeneratingTOC ? 'Generating TOC...' : (campaign?.toc ? 'Regenerate Table of Contents' : 'Generate Table of Contents')}
            </button>
            {tocError && <p className="error-message llm-feedback">{tocError}</p>}
          </div>
          <div className="action-group">
            <button onClick={handleGenerateTitles} disabled={isGeneratingTitles || !campaign?.concept || !selectedLLMId} className="llm-button">
              {isGeneratingTitles ? 'Generating Titles...' : 'Suggest Campaign Titles'}
            </button>
            {titlesError && <p className="error-message llm-feedback">{titlesError}</p>}
          </div>
        </div>
        {/* Export Button within LLM Settings/Actions or a new Export section */}
        <div className="action-group export-action-group"> 
          <button onClick={handleExportHomebrewery} disabled={isExporting} className="llm-button export-button">
            {isExporting ? 'Exporting...' : 'Export to Homebrewery'}
          </button>
          {exportError && <p className="error-message llm-feedback">{exportError}</p>}
        </div>
          </>
        )}
      </div>
      
      {suggestedTitles && suggestedTitles.length > 0 && (
        <section className="suggested-titles-section editor-section">
          <h3>Suggested Titles:</h3>
          <ul className="titles-list">
            {suggestedTitles.map((title, index) => (<li key={index} className="title-item">{title}</li>))}
          </ul>
          <button onClick={() => setSuggestedTitles(null)} className="dismiss-titles-button">Dismiss</button>
        </section>
      )}

      {/* Section Display Controls */}
      <div className="section-display-controls editor-section">
        <h3>Section Display</h3>
        <button onClick={() => setForceCollapseAll(true)} className="action-button">Collapse All Sections</button>
        <button onClick={() => setForceCollapseAll(false)} className="action-button">Expand All Sections</button>
        <button onClick={() => setForceCollapseAll(undefined)} className="action-button secondary-action-button">Enable Individual Toggling</button>
      </div>

      <section className="campaign-sections-list read-only-section">
        <h2>Campaign Sections</h2>
        {sections.length > 0 ? (
          sections.map((section) => (
            <div key={section.id} id={`section-container-${section.id}`} className="section-wrapper">
              <CampaignSectionView
                section={section}
                onSave={handleUpdateSection}
                isSaving={savingSectionId === section.id}
                saveError={sectionSaveError[section.id] || null}
                onDelete={handleDeleteSection} // Added onDelete prop
                forceCollapse={forceCollapseAll} // Pass the forceCollapseAll state
              />
            </div>
          ))
        ) : (<p>No sections available for this campaign yet.</p>)}
      </section>
      
      <LLMSelectionDialog
        isOpen={isLLMDialogOpen}
        currentModelId={selectedLLMId}
        onModelSelect={(modelId) => {
          if (modelId !== null) { // Ensure a model is actually selected
            setSelectedLLMId(modelId);
          }
          setIsLLMDialogOpen(false);
        }}
        onClose={() => setIsLLMDialogOpen(false)}
      />

      <div className="editor-actions add-section-area editor-section">
        <h3 onClick={() => setIsAddSectionCollapsed(!isAddSectionCollapsed)} style={{ cursor: 'pointer' }}>
          {isAddSectionCollapsed ? '▶' : '▼'} Add New Section
        </h3>
        {!isAddSectionCollapsed && (
          <>
            <form onSubmit={handleAddSection} className="add-section-form">
              <div className="form-group">
                <label htmlFor="newSectionTitle">Section Title (Optional):</label>
                <input type="text" id="newSectionTitle" className="form-input" value={newSectionTitle} onChange={(e) => setNewSectionTitle(e.target.value)} placeholder="E.g., Chapter 1: The Discovery" />
              </div>
              <div className="form-group">
                <label htmlFor="newSectionPrompt">Section Prompt (Optional):</label>
                <textarea id="newSectionPrompt" className="form-textarea" value={newSectionPrompt} onChange={(e) => setNewSectionPrompt(e.target.value)} rows={3} placeholder="E.g., Start with the players finding a mysterious map..." />
              </div>
              {addSectionError && <p className="error-message feedback-message">{addSectionError}</p>}
              {addSectionSuccess && <p className="success-message feedback-message">{addSectionSuccess}</p>}
              <button type="submit" disabled={isAddingSection || !selectedLLMId} className="action-button add-section-button">
                {isAddingSection ? 'Adding Section...' : 'Add Section with Selected LLM'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default CampaignEditorPage;

// Note: The redundant LLMModel type alias (campaignService.ModelInfo) was already addressed by using LLMModel from llmService.
