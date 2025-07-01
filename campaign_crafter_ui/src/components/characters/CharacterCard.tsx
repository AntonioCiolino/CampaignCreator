import React from 'react';
import { Link } from 'react-router-dom';
import { Character } from '../../types/characterTypes';
import './CharacterCard.css'; // Styles for this component

// Placeholder image URL - replace with a proper one or logic to generate/fetch
const DEFAULT_THUMBNAIL = '/logo_placeholder.svg'; // Or any other placeholder image path

interface CharacterCardProps {
    character: Character;
    onDelete: (characterId: number, characterName: string) => void; // Function to call when delete is clicked
}

const CharacterCard: React.FC<CharacterCardProps> = ({ character, onDelete }) => {
    const thumbnailUrl = character.image_urls && character.image_urls.length > 0
        ? character.image_urls[0] // Use the first image as thumbnail
        : DEFAULT_THUMBNAIL;

    const handleDeleteClick = (event: React.MouseEvent) => {
        event.preventDefault(); // Prevent navigation when clicking delete button
        event.stopPropagation(); // Stop event from bubbling up to the Link
        onDelete(character.id, character.name);
    };

    return (
        <div className="character-card">
            <Link to={`/characters/${character.id}`} className="character-card-link">
                <div className="character-card-thumbnail-wrapper">
                    <img
                        src={thumbnailUrl}
                        alt={`${character.name} thumbnail`}
                        className="character-card-thumbnail"
                        onError={(e) => {
                            // Fallback if the primary image fails to load
                            const target = e.target as HTMLImageElement;
                            if (target.src !== DEFAULT_THUMBNAIL) { // Prevent infinite loop if placeholder also fails
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
            </Link>
            <div className="character-card-actions">
                <Link
                    to={`/characters/${character.id}/edit`}
                    className="btn btn-sm btn-outline-primary me-2"
                    onClick={(e) => e.stopPropagation()} // Prevent Link's navigation if card is also a link
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
        </div>
    );
};

export default CharacterCard;
