import React, { useState, useEffect, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import * as campaignService from '../services/campaignService';
import CampaignCard from '../components/CampaignCard';
import Button from '../components/common/Button'; // Import new Button
import Input from '../components/common/Input';   // Import new Input
import './DashboardPage.css'; 

const DashboardPage: React.FC = () => {
  const [campaigns, setCampaigns] = useState<campaignService.Campaign[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // For new campaign form
  const [newCampaignTitle, setNewCampaignTitle] = useState<string>('');
  const [newCampaignPrompt, setNewCampaignPrompt] = useState<string>('');
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
    if (!newCampaignTitle.trim()) { // Prompt can be optional for initial creation based on some designs
      setCreateError('Campaign title is required.');
      return;
    }
    // Reset error if only prompt was missing and title is now filled
    if (createError === 'Campaign title is required.' && newCampaignTitle.trim()) {
        setCreateError(null);
    }


    try {
      setIsCreating(true);
      setCreateError(null);
      const newCampaignData: campaignService.CampaignCreatePayload = {
        title: newCampaignTitle,
        initial_user_prompt: newCampaignPrompt, // Prompt is optional in payload if backend handles it
        // model_id_with_prefix_for_concept can be added here if LLMSelector is part of this form
      };
      const createdCampaign = await campaignService.createCampaign(newCampaignData);
      navigate(`/campaign/${createdCampaign.id}`); // Navigate to the editor or detail page
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
    // Consider a more visually appealing loading state, e.g., a spinner component
    return <div className="container"><p>Loading campaigns...</p></div>;
  }

  if (error) {
    // Use a more prominent error display, perhaps an Alert component if created
    return <div className="container"><p className="error-message" style={{textAlign: 'center'}}>{error}</p></div>;
  }

  return (
    <div className="dashboard-page container"> {/* Added .container for consistent padding/max-width */}
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
            // error={createError && createError.includes("title") ? createError : undefined} // More specific error handling possible
          />
          
          <div className="form-group"> {/* Keep form-group for textarea structure */}
            <label htmlFor="newCampaignPrompt" className="form-label">Initial Prompt (Optional):</label>
            <textarea
              id="newCampaignPrompt"
              name="newCampaignPrompt"
              value={newCampaignPrompt}
              onChange={(e) => setNewCampaignPrompt(e.target.value)}
              rows={4} // Adjusted rows
              placeholder="Describe the core idea or starting point for your campaign..."
              className="form-textarea" // Use global style from App.css
            />
          </div>

          {/* TODO: Add LLMSelector here if users should choose a model for initial concept generation */}

          {createError && <p className="error-message create-error">{createError}</p>}
          
          <Button 
            type="submit" 
            disabled={isCreating} 
            variant="success" // Use success variant for create
            className="create-button" // Keep existing class if it has specific layout styles in DashboardPage.css
          >
            {isCreating ? 'Creating...' : 'Create Campaign & Start Editing'}
          </Button>
        </form>
      </section>

      <section className="campaign-list-section">
        <h1>Your Campaigns</h1>
        {campaigns.length === 0 && !isLoading ? ( // Ensure not loading before showing "no campaigns"
          <p>No campaigns yet. Create one above to get started!</p>
        ) : (
          <ul className="campaign-list">
            {campaigns.map((campaign) => (
              <CampaignCard key={campaign.id} campaign={campaign} />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;
