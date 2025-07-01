import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Character,
    CharacterStats,
    CharacterCreate,
    CharacterUpdate,
    CharacterAspectGenerationRequestPayload
} from '../../types/characterTypes';
import * as characterService from '../../services/characterService'; // Import character service
import './CharacterForm.css';
// import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'; // Example icon
import LoadingSpinner from '../common/LoadingSpinner'; // For inline loading

interface CharacterFormProps {
    initialData?: Character | null; // For editing
    onSubmit: (data: CharacterCreate | CharacterUpdate) => Promise<void>;
    isSubmitting: boolean;
    submitButtonText?: string;
    error?: string | null;
}

const CharacterForm: React.FC<CharacterFormProps> = ({
    initialData,
    onSubmit,
    isSubmitting,
    submitButtonText = 'Submit',
    error: formError,
}) => {
    const navigate = useNavigate(); // Initialize useNavigate

    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [appearanceDescription, setAppearanceDescription] = useState('');
    const [imageUrls, setImageUrls] = useState(''); // Comma-separated string
    const [videoClipUrls, setVideoClipUrls] = useState(''); // Comma-separated string
    const [notesForLlm, setNotesForLlm] = useState('');

    // Stats
    const [strength, setStrength] = useState<string>('10');
    const [dexterity, setDexterity] = useState<string>('10');
    const [constitution, setConstitution] = useState<string>('10');
    const [intelligence, setIntelligence] = useState<string>('10');
    const [wisdom, setWisdom] = useState<string>('10');
    const [charisma, setCharisma] = useState<string>('10');

    // State for LLM generation
    const [isGeneratingDescription, setIsGeneratingDescription] = useState(false);
    const [descriptionGenError, setDescriptionGenError] = useState<string | null>(null);
    const [isGeneratingAppearance, setIsGeneratingAppearance] = useState(false);
    const [appearanceGenError, setAppearanceGenError] = useState<string | null>(null);

    // New state for export format preference
    const [exportFormatPreference, setExportFormatPreference] = useState<string>('complex');


    useEffect(() => {
        if (initialData) {
            setName(initialData.name || '');
            setDescription(initialData.description || '');
            setAppearanceDescription(initialData.appearance_description || '');
            setImageUrls((initialData.image_urls || []).join(', '));
            setVideoClipUrls((initialData.video_clip_urls || []).join(', '));
            setNotesForLlm(initialData.notes_for_llm || '');
            setExportFormatPreference(initialData.export_format_preference || 'complex'); // Set from initialData

            if (initialData.stats) {
                setStrength(initialData.stats.strength?.toString() || '10');
                setDexterity(initialData.stats.dexterity?.toString() || '10');
                setConstitution(initialData.stats.constitution?.toString() || '10');
                setIntelligence(initialData.stats.intelligence?.toString() || '10');
                setWisdom(initialData.stats.wisdom?.toString() || '10');
                setCharisma(initialData.stats.charisma?.toString() || '10');
            }
        }
    }, [initialData]);

    const parseStringToIntOrUndefined = (val: string): number | undefined => {
        const num = parseInt(val, 10);
        return isNaN(num) ? undefined : num;
    };

    const splitUrls = (urlsString: string): string[] | undefined => {
        if (!urlsString.trim()) return undefined; // Return undefined for empty or whitespace-only strings
        return urlsString.split(',').map(url => url.trim()).filter(url => url.length > 0);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const characterStats: CharacterStats = {
            strength: parseStringToIntOrUndefined(strength),
            dexterity: parseStringToIntOrUndefined(dexterity),
            constitution: parseStringToIntOrUndefined(constitution),
            intelligence: parseStringToIntOrUndefined(intelligence),
            wisdom: parseStringToIntOrUndefined(wisdom),
            charisma: parseStringToIntOrUndefined(charisma),
        };

        const processedImageUrls = splitUrls(imageUrls);
        const processedVideoClipUrls = splitUrls(videoClipUrls);

        const dataPayload: CharacterCreate | CharacterUpdate = {
            name,
            description: description || null,
            appearance_description: appearanceDescription || null,
            image_urls: processedImageUrls,
            video_clip_urls: processedVideoClipUrls,
            notes_for_llm: notesForLlm || null,
            stats: characterStats,
            export_format_preference: exportFormatPreference, // Add to payload
        };

        // If it's an update, ensure we only send fields that are meant to be updated.
        // The CharacterUpdate type already makes fields optional.
        // If initialData exists, it's an update. Otherwise, it's a create.
        // For create, all fields are fine. For update, only changed fields should ideally be sent
        // but the current CharacterUpdate Pydantic model takes care of this with exclude_unset=True on backend.
        // So, we can send the full payload.

        await onSubmit(dataPayload);
    };

    const handleGenerateAspect = async (
        aspect: "description" | "appearance_description" | "backstory_snippet"
    ) => {
        let setIsGenerating: React.Dispatch<React.SetStateAction<boolean>>;
        let setErrorState: React.Dispatch<React.SetStateAction<string | null>>;
        let setFieldState: React.Dispatch<React.SetStateAction<string>>;
        let existingContext: Partial<CharacterAspectGenerationRequestPayload> = { character_name: name || undefined };

        if (aspect === "description") {
            setIsGenerating = setIsGeneratingDescription;
            setErrorState = setDescriptionGenError;
            setFieldState = setDescription;
            existingContext.existing_appearance_description = appearanceDescription || undefined;
        } else if (aspect === "appearance_description") {
            setIsGenerating = setIsGeneratingAppearance;
            setErrorState = setAppearanceGenError;
            setFieldState = setAppearanceDescription;
            existingContext.existing_description = description || undefined;
        } else {
            console.error("Unsupported aspect for generation:", aspect);
            return; // Or handle other aspects if added later
        }

        setIsGenerating(true);
        setErrorState(null);

        try {
            const payload: CharacterAspectGenerationRequestPayload = {
                ...existingContext,
                aspect_to_generate: aspect,
                // model_id_with_prefix: "anthropic/claude-3-haiku-20240307" // Example, make this selectable or from settings
            };
            const response = await characterService.generateCharacterAspect(payload);
            setFieldState(response.generated_text);
        } catch (err: any) {
            console.error(`Failed to generate ${aspect}:`, err);
            setErrorState(err.response?.data?.detail || err.message || `An error occurred while generating ${aspect}.`);
        } finally {
            setIsGenerating(false);
        }
    };


    return (
        <form onSubmit={handleSubmit} className="character-form-container">
            {formError && <div className="alert alert-danger">{formError}</div>}

            <div className="mb-3">
                <label htmlFor="char-name" className="form-label">Name*</label>
                <input
                    type="text"
                    className="form-control"
                    id="char-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                />
            </div>

            {/* Stats Section Wrapper - MOVED HERE */}
            <div className="stats-section mb-3"> {/* Added mb-3 for spacing after stats section */}
                <h5>Stats</h5>
                <div className="stats-input-row-layout"> {/* New class for flex layout */}
                    <div className="stat-input-item mb-3"> {/* Removed col-md-4, added mb-3 for consistency if items wrap */}
                        <label htmlFor="char-strength" className="form-label">STR</label>
                        <input type="number" className="form-control" id="char-strength" value={strength} onChange={(e) => setStrength(e.target.value)} />
                    </div>
                    <div className="stat-input-item mb-3">
                        <label htmlFor="char-dexterity" className="form-label">DEX</label>
                        <input type="number" className="form-control" id="char-dexterity" value={dexterity} onChange={(e) => setDexterity(e.target.value)} />
                    </div>
                    <div className="stat-input-item mb-3">
                        <label htmlFor="char-constitution" className="form-label">CON</label>
                        <input type="number" className="form-control" id="char-constitution" value={constitution} onChange={(e) => setConstitution(e.target.value)} />
                    </div>
                    <div className="stat-input-item mb-3">
                        <label htmlFor="char-intelligence" className="form-label">INT</label>
                        <input type="number" className="form-control" id="char-intelligence" value={intelligence} onChange={(e) => setIntelligence(e.target.value)} />
                    </div>
                    <div className="stat-input-item mb-3">
                        <label htmlFor="char-wisdom" className="form-label">WIS</label>
                        <input type="number" className="form-control" id="char-wisdom" value={wisdom} onChange={(e) => setWisdom(e.target.value)} />
                    </div>
                    <div className="stat-input-item mb-3">
                        <label htmlFor="char-charisma" className="form-label">CHA</label>
                        <input type="number" className="form-control" id="char-charisma" value={charisma} onChange={(e) => setCharisma(e.target.value)} />
                    </div>
                </div>
            </div>

            <div className="mb-3">
                <div className="form-label-group">
                    <label htmlFor="char-description" className="form-label">Description</label>
                    <button
                        type="button"
                        className="btn btn-outline-primary btn-sm generate-ai-button"
                        onClick={() => handleGenerateAspect("description")}
                        disabled={isGeneratingDescription || isSubmitting}
                        title="Generate Description with AI"
                    >
                        {isGeneratingDescription ? <LoadingSpinner /> : '✨ Gen AI'}
                    </button>
                </div>
                <textarea
                    className="form-control"
                    id="char-description"
                    rows={5} // Increased rows for better editing space
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                ></textarea>
                {descriptionGenError && <small className="text-danger d-block mt-1">{descriptionGenError}</small>}
            </div>

            <div className="mb-3">
                <div className="form-label-group">
                    <label htmlFor="char-appearance" className="form-label">Appearance Description</label>
                    <button
                        type="button"
                        className="btn btn-outline-primary btn-sm generate-ai-button"
                        onClick={() => handleGenerateAspect("appearance_description")}
                        disabled={isGeneratingAppearance || isSubmitting}
                        title="Generate Appearance Description with AI"
                    >
                        {isGeneratingAppearance ? <LoadingSpinner /> : '✨ Gen AI'}
                    </button>
                </div>
                <textarea
                    className="form-control"
                    id="char-appearance"
                    rows={5} // Increased rows
                    value={appearanceDescription}
                    onChange={(e) => setAppearanceDescription(e.target.value)}
                ></textarea>
                {appearanceGenError && <small className="text-danger d-block mt-1">{appearanceGenError}</small>}
            </div>

            <div className="mb-3">
                <label htmlFor="char-image-urls" className="form-label">Image URLs (comma-separated)</label>
                <input
                    type="text"
                    className="form-control"
                    id="char-image-urls"
                    value={imageUrls}
                    onChange={(e) => setImageUrls(e.target.value)}
                    placeholder="e.g., http://example.com/img1.png, http://example.com/img2.jpg"
                />
            </div>

            <div className="mb-3">
                <label htmlFor="char-video-urls" className="form-label">Video Clip URLs (comma-separated)</label>
                <input
                    type="text"
                    className="form-control"
                    id="char-video-urls"
                    value={videoClipUrls}
                    onChange={(e) => setVideoClipUrls(e.target.value)}
                />
            </div>

            <div className="mb-3">
                <label htmlFor="char-llm-notes" className="form-label">Notes for LLM</label>
                <textarea
                    className="form-control"
                    id="char-llm-notes"
                    rows={2}
                    value={notesForLlm}
                    onChange={(e) => setNotesForLlm(e.target.value)}
                ></textarea>
            </div>

            <div className="mb-3">
                <label htmlFor="char-export-format" className="form-label">Export Format Preference</label>
                <select
                    className="form-select"
                    id="char-export-format"
                    value={exportFormatPreference}
                    onChange={(e) => setExportFormatPreference(e.target.value)}
                >
                    <option value="complex">Complex Stat Block (Elara Style)</option>
                    <option value="simple">Simple Stat Block (Harlan Style)</option>
                </select>
                <small className="form-text text-muted">
                    Determines how this character appears in Homebrewery exports.
                </small>
            </div>

            {/* Submit Button Area */}
            <div className="form-submit-area">
                <button
                    type="button"
                    className="btn btn-secondary me-2" // Added me-2 for margin
                    onClick={() => {
                        if (initialData && initialData.id) {
                            navigate(`/characters/${initialData.id}`); // Go to detail page if editing
                        } else {
                            navigate('/characters'); // Go to list page if creating
                        }
                    }}
                    disabled={isSubmitting} // Disable cancel if main action is submitting
                >
                    Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                    {isSubmitting ? 'Submitting...' : submitButtonText}
                </button>
            </div>
        </form>
    );
};

export default CharacterForm;
