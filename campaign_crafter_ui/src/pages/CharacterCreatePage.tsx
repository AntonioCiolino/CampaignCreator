import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CharacterForm from '../components/characters/CharacterForm'; // Adjust path as needed
import * as characterService from '../services/characterService';
import { CharacterCreate, CharacterUpdate } from '../types/characterTypes'; // Added CharacterUpdate to import

const CharacterCreatePage: React.FC = () => {
    const navigate = useNavigate();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (data: CharacterCreate | CharacterUpdate) => { // Type already correct from previous attempt
        setIsSubmitting(true);
        setError(null);
        try {
            // When creating, the 'data' object will conform to CharacterCreate
            // because 'name' is required by the form.
            const newCharacter = await characterService.createCharacter(data as CharacterCreate);
            alert('Character created successfully!'); // Or use a more sophisticated notification system
            navigate(`/characters/${newCharacter.id}`); // Navigate to the new character's detail page
        } catch (err: any) {
            console.error('Failed to create character:', err);
            const errorMsg = err.response?.data?.detail || 'An unknown error occurred. Please try again.';
            setError(errorMsg);
            setIsSubmitting(false);
        }
        // No need to setIsSubmitting(false) on success because we navigate away
    };

    return (
        <div className="container mt-3">
            <h1>Create New Character</h1>
            <CharacterForm
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                submitButtonText="Create Character"
                error={error}
            />
        </div>
    );
};

export default CharacterCreatePage;
