import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import * as characterService from '../services/characterService';
import { Character } from '../types/characterTypes'; // Assuming this path is correct
// It's good practice to have a specific CSS file for larger components or pages
// import './CharacterListPage.css';

const CharacterListPage: React.FC = () => {
    const [characters, setCharacters] = useState<Character[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

import LoadingSpinner from '../components/common/LoadingSpinner'; // Import LoadingSpinner

const CharacterListPage: React.FC = () => {
    const [characters, setCharacters] = useState<Character[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchCharacters = async () => {
            // setLoading(true); // Already true by default
            try {
                const userCharacters = await characterService.getUserCharacters();
                setCharacters(userCharacters);
                setError(null);
            } catch (err) {
                console.error("Failed to fetch characters:", err);
                setError('Failed to load characters. Please try again later.');
            } finally {
                setLoading(false);
            }
        };

        fetchCharacters();
    }, []);

    if (loading) {
        // return <div className="container mt-3"><p>Loading characters...</p></div>;
        return <div className="container mt-3 d-flex justify-content-center"><LoadingSpinner /></div>;
    }

    if (error) {
        return <div className="container mt-3"><p className="text-danger">{error}</p></div>;
    }

    return (
        <div className="container mt-3 character-list-page">
            <div className="d-flex justify-content-between align-items-center mb-3">
                <h1>Your Characters</h1>
                <Link to="/characters/new" className="btn btn-primary">
                    Create New Character
                </Link>
            </div>

            {characters.length === 0 ? (
                <p>You haven't created any characters yet. Get started by creating one!</p>
            ) : (
                <div className="list-group">
                    {characters.map((character) => (
                        <Link
                            key={character.id}
                            to={`/characters/${character.id}`} // Route to be defined later
                            className="list-group-item list-group-item-action"
                        >
                            <h5 className="mb-1">{character.name}</h5>
                            {character.description && (
                                <p className="mb-1 text-muted">
                                    {character.description.length > 100
                                        ? `${character.description.substring(0, 100)}...`
                                        : character.description}
                                </p>
                            )}
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
};

export default CharacterListPage;
