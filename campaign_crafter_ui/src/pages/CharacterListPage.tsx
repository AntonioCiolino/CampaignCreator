import React, { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom'; // Import useNavigate
import * as characterService from '../services/characterService';
import { Character } from '../types/characterTypes';
import Button from '../components/common/Button'; // Import Button component
import CharacterCard from '../components/characters/CharacterCard'; // Import CharacterCard
import LoadingSpinner from '../components/common/LoadingSpinner';
import ConfirmationModal from '../components/modals/ConfirmationModal'; // Assuming a generic confirmation modal exists
import AlertMessage from '../components/common/AlertMessage'; // Assuming a generic alert message component
import './CharacterListPage.css'; // Import the CSS file

const CharacterListPage: React.FC = () => {
    const [characters, setCharacters] = useState<Character[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    // State for delete confirmation modal
    const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
    const [characterToDelete, setCharacterToDelete] = useState<{ id: number; name: string } | null>(null);
    const [isDeleting, setIsDeleting] = useState<boolean>(false);
    const navigate = useNavigate(); // Initialize useNavigate

    const fetchCharacters = useCallback(async () => {
        setLoading(true);
        try {
            const userCharacters = await characterService.getUserCharacters();
            setCharacters(userCharacters);
            setError(null);
        } catch (err: any) {
            console.error("Failed to fetch characters:", err);
            setError(err.response?.data?.detail || 'Failed to load characters. Please try again later.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchCharacters();
    }, [fetchCharacters]);

    const openDeleteModal = (characterId: number, characterName: string) => {
        setCharacterToDelete({ id: characterId, name: characterName });
        setShowDeleteModal(true);
        setSuccessMessage(null); // Clear previous success messages
        setError(null); // Clear previous error messages
    };

    const closeDeleteModal = () => {
        setShowDeleteModal(false);
        setCharacterToDelete(null);
    };

    const handleDeleteCharacter = async () => {
        if (!characterToDelete) return;

        setIsDeleting(true);
        setError(null);
        setSuccessMessage(null);

        try {
            await characterService.deleteCharacter(characterToDelete.id);
            setCharacters(prevCharacters => prevCharacters.filter(char => char.id !== characterToDelete.id));
            setSuccessMessage(`Character "${characterToDelete.name}" deleted successfully.`);
        } catch (err: any) {
            console.error("Failed to delete character:", err);
            setError(err.response?.data?.detail || `Failed to delete ${characterToDelete.name}. Please try again.`);
        } finally {
            setIsDeleting(false);
            closeDeleteModal();
        }
    };

    if (loading && characters.length === 0) { // Show full page spinner only on initial load
        return (
            <div className="container mt-3 d-flex justify-content-center align-items-center" style={{ minHeight: '80vh' }}>
                <LoadingSpinner />
            </div>
        );
    }

    return (
        <div className="container mt-3 character-list-page">
            <div className="page-header mb-4">
                <h1>Your Characters</h1>
                <Button variant="primary" onClick={() => navigate('/characters/new')}>
                    + Create New Character
                </Button>
            </div>

            {error && <AlertMessage type="error" message={error} onClose={() => setError(null)} />}
            {successMessage && <AlertMessage type="success" message={successMessage} onClose={() => setSuccessMessage(null)} />}

            {loading && characters.length > 0 && (
                <div className="text-center my-3">
                    <LoadingSpinner /> {/* Smaller spinner for re-fetching or background loading */}
                </div>
            )}

            {!loading && characters.length === 0 && !error && (
                <div className="text-center card p-4">
                    <h4>No Characters Yet!</h4>
                    <p>You haven't created any characters. Click the button above to get started!</p>
                </div>
            )}

            {characters.length > 0 && (
                <div className="character-grid">
                    {characters.map((character) => (
                        <CharacterCard
                            key={character.id}
                            character={character}
                            onDelete={() => openDeleteModal(character.id, character.name)}
                        />
                    ))}
                </div>
            )}

            {characterToDelete && (
                <ConfirmationModal
                    isOpen={showDeleteModal}
                    title="Confirm Deletion"
                    message={`Are you sure you want to delete the character "${characterToDelete.name}"? This action cannot be undone.`}
                    onConfirm={handleDeleteCharacter}
                    onCancel={closeDeleteModal}
                    confirmButtonText="Delete"
                    cancelButtonText="Cancel"
                    isConfirming={isDeleting}
                    confirmButtonVariant="danger"
                />
            )}
        </div>
    );
};

export default CharacterListPage;
