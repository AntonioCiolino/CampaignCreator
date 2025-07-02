import React from 'react';
import { Link } from 'react-router-dom';
import { Character } from '../../types/characterTypes';
import Card from '../common/Card'; // Import the generic Card component
import './CharacterCard.css';

const DEFAULT_THUMBNAIL = '/logo_placeholder.svg';

interface CharacterCardProps {
    character: Character;
    onDelete: (characterId: number, characterName: string) => void;
}

const CharacterCard: React.FC<CharacterCardProps> = ({ character, onDelete }) => {
    const thumbnailUrl = character.image_urls && character.image_urls.length > 0
        ? character.image_urls[0]
        : DEFAULT_THUMBNAIL;

    const handleDeleteClick = (event: React.MouseEvent) => {
        event.preventDefault();
        event.stopPropagation();
        onDelete(character.id, character.name);
    };

    const cardActions = (
        <div className="character-card-actions">
            <Link
                to={`/characters/${character.id}/edit`}
                className="btn btn-sm btn-outline-primary me-2"
                onClick={(e) => e.stopPropagation()}
            >
                Edit
            </Link>
            <button
                onClick={handleDeleteClick}
                className="btn btn-sm btn-outline-danger"
            >
                Delete
            </button>
        </div>
    );

    return (
        <Card
            href={`/characters/${character.id}`}
            interactive
            className="character-card" // Keep for specific styling overrides or additions
            footerContent={cardActions}
        >
            <div className="character-card-link-content"> {/* New wrapper for content that was inside the old Link */}
                <div className="character-card-thumbnail-wrapper">
                    <img
                        src={thumbnailUrl}
                        alt={`${character.name} thumbnail`}
                        className="character-card-thumbnail"
                        onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            if (target.src !== DEFAULT_THUMBNAIL) {
                                target.src = DEFAULT_THUMBNAIL;
                                target.alt = "Placeholder image";
                            }
                        }}
                    />
                </div>
                <div className="character-card-info">
                    <h5 className="character-card-name">{character.name}</h5>
                    {/* Optional: Add a snippet of description or other info here */}
                    {/* <p className="character-card-description">{character.description?.substring(0, 50) || 'No description'}...</p> */}
                </div>
            </div>
        </Card>
    );
};

export default CharacterCard;
