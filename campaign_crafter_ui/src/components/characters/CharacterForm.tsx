import React, { useState, useEffect } from 'react';
import { Character, CharacterStats, CharacterCreate, CharacterUpdate } from '../../types/characterTypes'; // Assuming path

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

    useEffect(() => {
        if (initialData) {
            setName(initialData.name || '');
            setDescription(initialData.description || '');
            setAppearanceDescription(initialData.appearance_description || '');
            setImageUrls((initialData.image_urls || []).join(', '));
            setVideoClipUrls((initialData.video_clip_urls || []).join(', '));
            setNotesForLlm(initialData.notes_for_llm || '');

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
        };

        // If it's an update, ensure we only send fields that are meant to be updated.
        // The CharacterUpdate type already makes fields optional.
        // If initialData exists, it's an update. Otherwise, it's a create.
        // For create, all fields are fine. For update, only changed fields should ideally be sent
        // but the current CharacterUpdate Pydantic model takes care of this with exclude_unset=True on backend.
        // So, we can send the full payload.

        await onSubmit(dataPayload);
    };

    return (
        <form onSubmit={handleSubmit}>
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

            <div className="mb-3">
                <label htmlFor="char-description" className="form-label">Description</label>
                <textarea
                    className="form-control"
                    id="char-description"
                    rows={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                ></textarea>
            </div>

            <div className="mb-3">
                <label htmlFor="char-appearance" className="form-label">Appearance Description</label>
                <textarea
                    className="form-control"
                    id="char-appearance"
                    rows={3}
                    value={appearanceDescription}
                    onChange={(e) => setAppearanceDescription(e.target.value)}
                ></textarea>
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

            <h5 className="mt-4">Stats</h5>
            <div className="row">
                <div className="col-md-4 mb-3">
                    <label htmlFor="char-strength" className="form-label">Strength</label>
                    <input type="number" className="form-control" id="char-strength" value={strength} onChange={(e) => setStrength(e.target.value)} />
                </div>
                <div className="col-md-4 mb-3">
                    <label htmlFor="char-dexterity" className="form-label">Dexterity</label>
                    <input type="number" className="form-control" id="char-dexterity" value={dexterity} onChange={(e) => setDexterity(e.target.value)} />
                </div>
                <div className="col-md-4 mb-3">
                    <label htmlFor="char-constitution" className="form-label">Constitution</label>
                    <input type="number" className="form-control" id="char-constitution" value={constitution} onChange={(e) => setConstitution(e.target.value)} />
                </div>
                <div className="col-md-4 mb-3">
                    <label htmlFor="char-intelligence" className="form-label">Intelligence</label>
                    <input type="number" className="form-control" id="char-intelligence" value={intelligence} onChange={(e) => setIntelligence(e.target.value)} />
                </div>
                <div className="col-md-4 mb-3">
                    <label htmlFor="char-wisdom" className="form-label">Wisdom</label>
                    <input type="number" className="form-control" id="char-wisdom" value={wisdom} onChange={(e) => setWisdom(e.target.value)} />
                </div>
                <div className="col-md-4 mb-3">
                    <label htmlFor="char-charisma" className="form-label">Charisma</label>
                    <input type="number" className="form-control" id="char-charisma" value={charisma} onChange={(e) => setCharisma(e.target.value)} />
                </div>
            </div>

            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Submitting...' : submitButtonText}
            </button>
        </form>
    );
};

export default CharacterForm;
