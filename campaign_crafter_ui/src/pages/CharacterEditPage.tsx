import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import CharacterForm from '../components/characters/CharacterForm'; // Adjust path as needed
import * as characterService from '../services/characterService';
import { Character, CharacterUpdate } from '../types/characterTypes';
import LoadingSpinner from '../components/common/LoadingSpinner'; // Import LoadingSpinner

const CharacterEditPage: React.FC = () => {
    const { characterId } = useParams<{ characterId: string }>();
    const navigate = useNavigate();

    const [initialData, setInitialData] = useState<Character | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [formError, setFormError] = useState<string | null>(null);


    useEffect(() => {
        if (characterId) {
            const id = parseInt(characterId, 10);
            if (isNaN(id)) {
                setError("Invalid character ID.");
                setLoading(false);
                return;
            }
            characterService.getCharacterById(id)
                .then(data => {
                    setInitialData(data);
                    setError(null);
                })
                .catch(err => {
                    console.error("Failed to fetch character for editing:", err);
                    if (err.response && err.response.status === 404) {
                        setError('Character not found.');
                    } else if (err.response && err.response.status === 403) {
                        setError('You are not authorized to edit this character.');
                    } else {
                        setError('Failed to load character data. Please try again.');
                    }
                })
                .finally(() => setLoading(false));
        } else {
            setError("No character ID provided for editing.");
            setLoading(false);
        }
    }, [characterId]);

    const handleSubmit = async (data: CharacterUpdate) => {
        if (!characterId) return;

        setIsSubmitting(true);
        setFormError(null);
        try {
            const id = parseInt(characterId, 10);
            await characterService.updateCharacter(id, data);
            alert('Character updated successfully!');
            navigate(`/characters/${id}`); // Navigate to the character's detail page
        } catch (err: any) {
            console.error('Failed to update character:', err);
            const errorMsg = err.response?.data?.detail || 'An unknown error occurred while updating. Please try again.';
            setFormError(errorMsg);
            setIsSubmitting(false);
        }
         // No need to setIsSubmitting(false) on success because we navigate away
    };

    if (loading) {
        // return <div className="container mt-3"><p>Loading character data for editing...</p></div>;
        return <div className="container mt-3 d-flex justify-content-center"><LoadingSpinner /></div>;
    }

    if (error) {
        return <div className="container mt-3"><p className="text-danger">{error}</p></div>;
    }

    if (!initialData) {
        return <div className="container mt-3"><p>Could not load character data for editing.</p></div>;
    }

    return (
        <div className="container mt-3">
            <h1>Edit Character: {initialData.name}</h1>
            <CharacterForm
                initialData={initialData}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                submitButtonText="Save Changes"
                error={formError}
            />
        </div>
    );
};

export default CharacterEditPage;
