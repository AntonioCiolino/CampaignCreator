import React, { useState, useEffect, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import * as campaignService from '../services/campaignService';
import CampaignCard from '../components/CampaignCard';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Checkbox from '../components/common/Checkbox'; // Import Checkbox component
import './DashboardPage.css'; 
import { Campaign, CampaignCreatePayload } from '../types/campaignTypes'; // Corrected import

const DashboardPage: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]); // Use imported Campaign type
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // For new campaign form
  const [newCampaignTitle, setNewCampaignTitle] = useState<string>('');
  const [newCampaignPrompt, setNewCampaignPrompt] = useState<string>('');
  const [skipConceptGeneration, setSkipConceptGeneration] = useState<boolean>(false); // New state for the checkbox
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const fetchedCampaigns = await campaignService.getAllCampaigns();
        setCampaigns(fetchedCampaigns);
      } catch (err) {
        console.error('Failed to fetch campaigns:', err);
        setError('Failed to load campaigns. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchCampaigns();
  }, []);

  const handleCreateCampaign = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newCampaignTitle.trim()) {
      setCreateError('Campaign title is required.');
      return;
    }
    if (createError === 'Campaign title is required.' && newCampaignTitle.trim()) {
        setCreateError(null);
    }

    try {
      setIsCreating(true);
      setCreateError(null);
      const newCampaignData: CampaignCreatePayload = { // Use imported CampaignCreatePayload type
        title: newCampaignTitle,
        initial_user_prompt: skipConceptGeneration ? undefined : newCampaignPrompt, // Send undefined if skipping
        skip_concept_generation: skipConceptGeneration, // Add the new flag
        // model_id_with_prefix_for_concept can be added here if LLMSelector is part of this form
      };
      const createdCampaign = await campaignService.createCampaign(newCampaignData);
      navigate(`/campaign/${createdCampaign.id}`);
    } catch (err) {
      console.error('Failed to create campaign:', err);
      const errorMessage = (err instanceof Error && (err as any).response?.data?.detail) 
                           ? (err as any).response.data.detail
                           : 'Failed to create campaign. Please try again.';
      setCreateError(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  if (isLoading) {
    return <div className="container"><p>Loading campaigns...</p></div>;
  }

  if (error) {
    return <div className="container"><p className="error-message" style={{textAlign: 'center'}}>{error}</p></div>;
  }

  return (
    <div className="dashboard-page container">
      <section className="campaign-list-section">
        <h1>Your Campaigns</h1>
        {campaigns.length === 0 && !isLoading ? (
          <p>No campaigns yet. Create one below to get started!</p>
        ) : (
          <ul className="campaign-list">
            {campaigns.map((campaign) => (
              <CampaignCard key={campaign.id} campaign={campaign} />
            ))}
          </ul>
        )}
      </section>

      <section className="create-campaign-section">
        <h2>Create New Campaign</h2>
        <form onSubmit={handleCreateCampaign} className="create-campaign-form">
          <Input
            id="newCampaignTitle"
            name="newCampaignTitle"
            label="Campaign Title:"
            value={newCampaignTitle}
            onChange={(e) => setNewCampaignTitle(e.target.value)}
            placeholder="Enter the title for your new campaign"
            required
          />
          
          <div className="form-group">
            <label htmlFor="newCampaignPrompt" className="form-label">Initial Prompt (Optional if skipping AI concept):</label>
            <textarea
              id="newCampaignPrompt"
              name="newCampaignPrompt"
              value={newCampaignPrompt}
              onChange={(e) => setNewCampaignPrompt(e.target.value)}
              rows={4}
              placeholder="Describe the core idea or starting point for your campaign..."
              className="form-textarea"
              disabled={skipConceptGeneration} // Disable if skipping generation
            />
          </div>

          <Checkbox
            id="skipConceptGeneration"
            label="Skip initial AI concept generation"
            checked={skipConceptGeneration}
            onChange={(e) => setSkipConceptGeneration(e.target.checked)}
            className="skip-concept-checkbox" // Added for specific styling if needed
          />

          {/* TODO: Add LLMSelector here if users should choose a model for initial concept generation,
                       and ensure it's disabled if skipConceptGeneration is true. */}

          {createError && <p className="error-message create-error">{createError}</p>}
          
          <Button 
            type="submit" 
            disabled={isCreating} 
            variant="success"
            className="create-button"
          >
            {isCreating ? 'Creating...' : 'Create Campaign & Start Editing'}
          </Button>
        </form>
      </section>
    </div>
  );
};

export default DashboardPage;
