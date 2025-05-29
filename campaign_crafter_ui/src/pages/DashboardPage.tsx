import React, { useState, useEffect, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import * as campaignService from '../services/campaignService'; // Import the service
import './DashboardPage.css'; // Create this file for styling

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

  // Fetch campaigns on mount
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

  // Handle new campaign creation
  const handleCreateCampaign = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newCampaignTitle.trim() || !newCampaignPrompt.trim()) {
      setCreateError('Both title and initial prompt are required.');
      return;
    }

    try {
      setIsCreating(true);
      setCreateError(null);
      const newCampaignData: campaignService.CampaignCreatePayload = {
        title: newCampaignTitle,
        initial_user_prompt: newCampaignPrompt,
      };
      const createdCampaign = await campaignService.createCampaign(newCampaignData);
      
      // Option 1: Refresh list (simple for now)
      // setCampaigns(prevCampaigns => [...prevCampaigns, createdCampaign]); 
      // setNewCampaignTitle('');
      // setNewCampaignPrompt('');

      // Option 2: Redirect to new campaign's editor page
      navigate(`/campaign/${createdCampaign.id}`);

    } catch (err) {
      console.error('Failed to create campaign:', err);
      setCreateError('Failed to create campaign. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  if (isLoading) {
    return <p>Loading campaigns...</p>;
  }

  if (error) {
    return <p className="error-message">{error}</p>;
  }

import CampaignCard from '../components/CampaignCard'; // Import the CampaignCard component

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

  // Fetch campaigns on mount
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

  // Handle new campaign creation
  const handleCreateCampaign = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newCampaignTitle.trim() || !newCampaignPrompt.trim()) {
      setCreateError('Both title and initial prompt are required.');
      return;
    }

    try {
      setIsCreating(true);
      setCreateError(null);
      const newCampaignData: campaignService.CampaignCreatePayload = {
        title: newCampaignTitle,
        initial_user_prompt: newCampaignPrompt,
      };
      const createdCampaign = await campaignService.createCampaign(newCampaignData);
      
      navigate(`/campaign/${createdCampaign.id}`);

    } catch (err) {
      console.error('Failed to create campaign:', err);
      setCreateError('Failed to create campaign. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  if (isLoading) {
    return <p>Loading campaigns...</p>;
  }

  if (error) {
    return <p className="error-message">{error}</p>;
  }

  return (
    <div className="dashboard-page">
      <section className="create-campaign-section">
        <h2>Create New Campaign</h2>
        <form onSubmit={handleCreateCampaign} className="create-campaign-form">
          <div className="form-group">
            <label htmlFor="newCampaignTitle">Title:</label>
            <input
              type="text"
              id="newCampaignTitle"
              value={newCampaignTitle}
              onChange={(e) => setNewCampaignTitle(e.target.value)}
              required
              placeholder="Campaign Title"
            />
          </div>
          <div className="form-group">
            <label htmlFor="newCampaignPrompt">Initial Prompt:</label>
            <textarea
              id="newCampaignPrompt"
              value={newCampaignPrompt}
              onChange={(e) => setNewCampaignPrompt(e.target.value)}
              rows={3}
              required
              placeholder="Describe the core idea of your campaign..."
            />
          </div>
          {createError && <p className="error-message create-error">{createError}</p>}
          <button type="submit" disabled={isCreating} className="create-button">
            {isCreating ? 'Creating...' : 'Create Campaign & Start Editing'}
          </button>
        </form>
      </section>

      <section className="campaign-list-section">
        <h1>Your Campaigns</h1>
        {campaigns.length === 0 ? (
          <p>No campaigns yet. Create one above!</p>
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
