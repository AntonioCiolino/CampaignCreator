import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as characterService from '../services/characterService';
import { PydanticCharacter } from '../types/characterTypes';
import CharacterCard from '../components/CharacterCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Button from '../components/common/Button'; // Assuming a common Button component exists
import './CharacterListPage.css'; // We'll create this CSS file next

const CharacterListPage: React.FC = () => {
  const { campaignId } = useParams<{ campaignId: string }>();
  const navigate = useNavigate();
  const [characters, setCharacters] = useState<PydanticCharacter[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCharacters = useCallback(async () => {
    if (!campaignId) {
      setError("Campaign ID is missing.");
      setIsLoading(false);
      return;
    }
    try {
      setIsLoading(true);
      setError(null);
      const fetchedCharacters = await characterService.getCharactersByCampaign(campaignId);
      setCharacters(fetchedCharacters);
    } catch (err) {
      console.error("Failed to fetch characters:", err);
      setError("Failed to load characters. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  }, [campaignId]);

  useEffect(() => {
    fetchCharacters();
  }, [fetchCharacters]);

  const handleCreateCharacter = () => {
    if (campaignId) {
      navigate(`/campaign/${campaignId}/character/new`);
    }
  };

  const handleDeleteCharacter = async (characterId: number, characterName: string) => {
    if (!window.confirm(`Are you sure you want to delete the character "${characterName}"? This action cannot be undone.`)) {
      return;
    }
    try {
      setIsLoading(true); // Optional: show loading state during delete
      await characterService.deleteCharacter(characterId);
      // Refresh the list after deletion
      setCharacters(prevCharacters => prevCharacters.filter(char => char.id !== characterId));
      // Optionally show a success message
    } catch (err) {
      console.error(`Failed to delete character ${characterId}:`, err);
      setError(`Failed to delete character "${characterName}". Please try again.`);
      // Optionally clear error after some time
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <p className="error-message page-error">{error}</p>;
  }

  return (
    <div className="character-list-page">
      <header className="character-list-header">
        <h1>Characters</h1>
        <Button
          onClick={handleCreateCharacter}
          variant="primary"
          className="add-character-button"
          tooltip="Create a new character for this campaign"
        >
          Add New Character
        </Button>
      </header>

      {characters.length === 0 ? (
        <div className="no-characters-message">
          <p>No characters found for this campaign yet.</p>
          <p>Click "Add New Character" to get started!</p>
        </div>
      ) : (
        <div className="character-grid">
          {characters.map(character => (
            <CharacterCard
              key={character.id}
              character={character}
              campaignId={campaignId!} // campaignId is checked in fetchCharacters
              onDelete={handleDeleteCharacter}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default CharacterListPage;
