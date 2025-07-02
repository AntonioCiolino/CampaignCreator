import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import * as campaignService from '../services/campaignService';
// import useScrollIndicators from '../hooks/useScrollIndicators'; // Removed
import * as characterService from '../services/characterService';
import CampaignCard from '../components/CampaignCard';
import CharacterCard from '../components/characters/CharacterCard';
import Button from '../components/common/Button';
// Input and Checkbox are now part of the modal
import './DashboardPage.css';
import { Campaign } from '../types/campaignTypes'; // CampaignCreatePayload is now in modal
import { Character } from '../types/characterTypes';
import LoadingSpinner from '../components/common/LoadingSpinner';
import CreateCampaignModal from '../components/modals/CreateCampaignModal'; // Import the modal

const DashboardPage: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [isLoadingCampaigns, setIsLoadingCampaigns] = useState<boolean>(true);
  const [isLoadingCharacters, setIsLoadingCharacters] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false); // State for modal

  const navigate = useNavigate();

  // Refs for scrollable sections - still useful if direct manipulation is ever needed, but not for indicators now
  const campaignsScrollRef = useRef<HTMLDivElement>(null);
  const charactersScrollRef = useRef<HTMLDivElement>(null);

  // Get scroll indicator states - REMOVED
  // const campaignScrollIndicators = useScrollIndicators(campaignsScrollRef);
  // const characterScrollIndicators = useScrollIndicators(charactersScrollRef);

  // Function to fetch all data
  const fetchAllData = async () => {
    setIsLoadingCampaigns(true);
    setIsLoadingCharacters(true);
    setError(null);
    let campaignError = null;
    let characterError = null;

    try {
      const fetchedCampaigns = await campaignService.getAllCampaigns();
      setCampaigns(fetchedCampaigns);
    } catch (err) {
      console.error('Failed to fetch campaigns:', err);
      campaignError = 'Failed to load campaigns.';
    } finally {
      setIsLoadingCampaigns(false);
    }

    try {
      const fetchedCharacters = await characterService.getUserCharacters();
      setCharacters(fetchedCharacters);
    } catch (err) {
      console.error('Failed to fetch characters:', err);
      characterError = 'Failed to load characters.';
    } finally {
      setIsLoadingCharacters(false);
    }

    if (campaignError && characterError) {
      setError(`${campaignError} ${characterError}`);
    } else {
      setError(campaignError || characterError);
    }
  };


  useEffect(() => {
    fetchAllData();
  }, []);

  // Handler for when a new campaign is created via the modal
  const handleCampaignCreated = (createdCampaign: Campaign) => {
    // Option 1: Navigate to the new campaign
    navigate(`/campaign/${createdCampaign.id}`);
    // Option 2: Or, refresh the campaigns list on the dashboard (and characters if relevant)
    // fetchAllData(); // This would re-fetch everything
    // Or, more optimistically:
    // setCampaigns(prev => [createdCampaign, ...prev]);
    // For simplicity, navigation is often preferred after creation.
  };

  // Dummy delete handler for CharacterCard
  const handleDeleteCharacter = (characterId: number, characterName: string) => {
    console.log(`Attempting to delete character: ${characterName} (ID: ${characterId}) - Not implemented on Dashboard`);
    setCharacters(prev => prev.filter(char => char.id !== characterId));
    // alert(`Character "${characterName}" would be deleted (front-end only demo).`);
    // TODO: Show a toast/notification instead of alert
  };


  if (error && !isLoadingCampaigns && !isLoadingCharacters && campaigns.length === 0 && characters.length === 0) {
    return <div className="container"><p className="error-message" style={{ textAlign: 'center' }}>{error}</p></div>;
  }

  return (
    <div className="dashboard-page container">
      <section className="dashboard-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h1 className="dashboard-section-title" style={{marginBottom: 0}}>Your Campaigns</h1>
          <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
            + New Campaign
          </Button>
        </div>
        {isLoadingCampaigns ? (
          <LoadingSpinner />
        ) : error && campaigns.length === 0 ? (
          <p className="error-message">Could not load campaigns.</p>
        ) : campaigns.length === 0 ? (
          <p>No campaigns yet. Click "+ New Campaign" to get started!</p>
        ) : (
          <div
            ref={campaignsScrollRef}
            className="horizontal-scroll-section" // Removed conditional classes for indicators
          >
            {campaigns.map((campaign) => (
              <div key={campaign.id} className="scroll-item-wrapper">
                <CampaignCard campaign={campaign} />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* <hr className="section-divider" />  Removed as per feedback */}

      <section className="dashboard-section">
         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h1 className="dashboard-section-title" style={{marginBottom: 0}}>Your Characters</h1>
            <Button variant="primary" onClick={() => navigate('/characters/new')}>
              + New Character
            </Button>
        </div>
        {isLoadingCharacters ? (
          <LoadingSpinner />
        ) : error && characters.length === 0 ? (
           <p className="error-message">Could not load characters.</p>
        ): characters.length === 0 ? (
          <p>No characters yet. <a href="/characters/new">Create a character!</a></p>
        ) : (
          <div
            ref={charactersScrollRef}
            className="horizontal-scroll-section" // Removed conditional classes for indicators
          >
            {characters.map((character) => (
              <div key={character.id} className="scroll-item-wrapper">
                <CharacterCard character={character} onDelete={handleDeleteCharacter} showActions={false} />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* The old create-campaign-section is now replaced by the modal button and the modal itself */}

      <CreateCampaignModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCampaignCreated={handleCampaignCreated}
      />
    </div>
  );
};

export default DashboardPage;
