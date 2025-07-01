import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PydanticCharacter } from '../types/characterTypes';
import './CharacterCard.css'; // We'll create this CSS file next

interface CharacterCardProps {
  character: PydanticCharacter;
  campaignId: number | string; // Needed for navigation
  onDelete: (characterId: number, characterName: string) => void; // Callback for delete action
}

const CharacterCard: React.FC<CharacterCardProps> = ({ character, campaignId, onDelete }) => {
  const navigate = useNavigate();

  const handleEdit = () => {
    navigate(`/campaign/${campaignId}/character/${character.id}`);
  };

  const handleDeleteClick = (event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent card click navigation when clicking delete
    onDelete(character.id, character.name);
  };

  const defaultIcon = '/logo_placeholder.svg'; // Path to a default placeholder image

  return (
    <div className="character-card" onClick={handleEdit} title={`View or Edit ${character.name}`}>
      <div className="character-card-icon-container">
        <img
          src={character.icon_url || defaultIcon}
          alt={`${character.name} icon`}
          className="character-card-icon"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.onerror = null; // Prevent infinite loop if defaultIcon also fails
            target.src = defaultIcon;
          }}
        />
      </div>
      <div className="character-card-info">
        <h3 className="character-card-name">{character.name}</h3>
      </div>
      <div className="character-card-actions">
        <button
          onClick={handleEdit}
          className="character-card-button edit"
          title={`Edit ${character.name}`}
        >
          Edit
        </button>
        <button
          onClick={handleDeleteClick}
          className="character-card-button delete"
          title={`Delete ${character.name}`}
        >
          Delete
        </button>
      </div>
    </div>
  );
};

export default CharacterCard;
