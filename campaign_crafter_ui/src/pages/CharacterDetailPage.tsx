import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import * as characterService from '../services/characterService';
import * as campaignService from '../services/campaignService';
import { Character, CharacterStats } from '../types/characterTypes';
import { Campaign } from '../types/campaignTypes';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ImagePreviewModal from '../components/modals/ImagePreviewModal'; // Import ImagePreviewModal
import AlertMessage from '../components/common/AlertMessage'; // For potential error/success messages
import ConfirmationModal from '../components/modals/ConfirmationModal'; // For delete confirmation
import './CharacterDetailPage.css'; // Import the CSS file

const DEFAULT_PLACEHOLDER_IMAGE = '/logo_placeholder.svg'; // Define a default placeholder

const CharacterDetailPage: React.FC = () => {
    const { characterId } = useParams<{ characterId: string }>();
    const navigate = useNavigate();

    const [character, setCharacter] = useState<Character | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);


    // Campaign association state
    const [userCampaigns, setUserCampaigns] = useState<Campaign[]>([]);
    const [selectedCampaignToLink, setSelectedCampaignToLink] = useState<string>('');
    const [linkError, setLinkError] = useState<string | null>(null);
    const [isLinking, setIsLinking] = useState<boolean>(false);
    const [associatedCampaigns, setAssociatedCampaigns] = useState<Campaign[]>([]);

    // LLM Interaction state
    const [llmUserPrompt, setLlmUserPrompt] = useState<string>('');
    const [llmResponse, setLlmResponse] = useState<string | null>(null);
    const [isGeneratingResponse, setIsGeneratingResponse] = useState<boolean>(false);
    const [llmError, setLlmError] = useState<string | null>(null);

    // Image Generation State
    const [isGeneratingImage, setIsGeneratingImage] = useState<boolean>(false);
    const [imageGenError, setImageGenError] = useState<string | null>(null);

    // Image Preview Modal State
    const [showImagePreviewModal, setShowImagePreviewModal] = useState<boolean>(false);
    const [selectedImageUrl, setSelectedImageUrl] = useState<string | null>(null);

    // Delete Confirmation Modal State
    const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
    const [isDeleting, setIsDeleting] = useState<boolean>(false);


    const fetchCharacterAndCampaignData = useCallback(async () => {
        if (!characterId) {
            setError("No character ID provided.");
            setLoading(false);
            return;
        }
        setLoading(true);
        setError(null);
        setSuccessMessage(null);
        try {
            const id = parseInt(characterId, 10);
            if (isNaN(id)) {
                setError("Invalid character ID.");
                setLoading(false);
                return;
            }

            const [fetchedCharacter, campaigns, linkedCampaigns] = await Promise.all([
                characterService.getCharacterById(id),
                campaignService.getAllCampaigns(),
                characterService.getCharacterCampaigns(id)
            ]);

            setCharacter(fetchedCharacter);
            setUserCampaigns(campaigns);
            setAssociatedCampaigns(linkedCampaigns);

        } catch (err: any) {
            console.error("Failed to fetch character page data:", err);
            const errMsg = err.response?.data?.detail || 'Failed to load character details or campaigns.';
            if (err.response && err.response.status === 404) {
                setError('Character not found.');
            } else if (err.response && err.response.status === 403) {
                setError('You are not authorized to view this character or related campaigns.');
            } else {
                setError(errMsg);
            }
            setCharacter(null);
            setUserCampaigns([]);
            setAssociatedCampaigns([]);
        } finally {
            setLoading(false);
        }
    }, [characterId]);

    useEffect(() => {
        fetchCharacterAndCampaignData();
    }, [fetchCharacterAndCampaignData]);


    const handleLinkCampaign = async () => {
        if (!character || !selectedCampaignToLink) {
            setLinkError("Please select a campaign to link.");
            return;
        }
        setIsLinking(true);
        setLinkError(null);
        setSuccessMessage(null);
        try {
            const campaignIdToLink = parseInt(selectedCampaignToLink, 10);
            await characterService.linkCharacterToCampaign(character.id, campaignIdToLink);
            setSuccessMessage(`${character.name} successfully linked to campaign.`);
            setSelectedCampaignToLink('');
            const updatedLinkedCampaigns = await characterService.getCharacterCampaigns(character.id);
            setAssociatedCampaigns(updatedLinkedCampaigns);
        } catch (err: any) {
            console.error("Failed to link character to campaign:", err);
            setLinkError(err.response?.data?.detail || "Failed to link campaign.");
        } finally {
            setIsLinking(false);
        }
    };

    const handleUnlinkCampaign = async (campaignIdToUnlink: number, campaignTitle: string) => {
        if (!character) return;
        if (window.confirm(`Are you sure you want to unlink ${character.name} from campaign "${campaignTitle}"?`)) {
            setIsLinking(true);
            setLinkError(null);
            setSuccessMessage(null);
            try {
                await characterService.unlinkCharacterFromCampaign(character.id, campaignIdToUnlink);
                setSuccessMessage(`${character.name} successfully unlinked from campaign "${campaignTitle}".`);
                setAssociatedCampaigns(prev => prev.filter(c => c.id !== campaignIdToUnlink));
            } catch (err: any) {
                console.error("Failed to unlink character from campaign:", err);
                setLinkError(err.response?.data?.detail || "Failed to unlink campaign.");
            } finally {
                setIsLinking(false);
            }
        }
    };

    const openDeleteModal = () => {
        setShowDeleteModal(true);
        setError(null);
        setSuccessMessage(null);
    };

    const closeDeleteModal = () => {
        setShowDeleteModal(false);
    };

    const handleDeleteCharacter = async () => {
        if (!character) return;

        setIsDeleting(true);
        setError(null);
        try {
            await characterService.deleteCharacter(character.id);
            // alert('Character deleted successfully.'); // Using AlertMessage now
            navigate('/characters', { state: { successMessage: `Character "${character.name}" deleted successfully.` } });
        } catch (err: any) {
            console.error("Failed to delete character:", err);
            setError(err.response?.data?.detail || 'Failed to delete character. Please try again.');
            setIsDeleting(false); // Only set isDeleting to false on error, on success we navigate
            closeDeleteModal(); // Close modal on error
        }
    };


    const renderStats = (stats: CharacterStats | null | undefined) => {
        if (!stats) return <p className="text-muted">No stats available.</p>;

        const statItems = [
            { label: "STR", value: stats.strength },
            { label: "DEX", value: stats.dexterity },
            { label: "CON", value: stats.constitution },
            { label: "INT", value: stats.intelligence },
            { label: "WIS", value: stats.wisdom },
            { label: "CHA", value: stats.charisma },
        ];

        return (
            <div className="character-stats-grid">
                {statItems.map(stat => (
                    <div key={stat.label} className="stat-item">
                        <span className="stat-label">{stat.label}</span>
                        <span className="stat-value">{stat.value ?? '10'}</span>
                    </div>
                ))}
            </div>
        );
    };

    const handleGenerateNewImage = async () => {
        if (!character) {
            setImageGenError("Character data not available to generate image.");
            return;
        }
        setIsGeneratingImage(true);
        setImageGenError(null);
        setSuccessMessage(null);
        try {
            const updatedCharacter = await characterService.generateCharacterImage(character.id, {});
            setCharacter(updatedCharacter);
            setSuccessMessage("New image generated successfully!");
        } catch (err: any) {
            console.error("Failed to generate character image:", err);
            setImageGenError(err.response?.data?.detail || "Failed to generate image for character.");
        } finally {
            setIsGeneratingImage(false);
        }
    };

    const handleGenerateCharacterResponse = async () => {
        if (!character || !llmUserPrompt.trim()) {
            setLlmError("Please enter a prompt for the character.");
            return;
        }
        setIsGeneratingResponse(true);
        setLlmError(null);
        setLlmResponse(null);
        try {
            const response = await characterService.generateCharacterResponse(character.id, { prompt: llmUserPrompt });
            setLlmResponse(response.text);
        } catch (err: any) {
            console.error("Failed to generate character response:", err);
            setLlmError(err.response?.data?.detail || "Failed to get response from character.");
        } finally {
            setIsGeneratingResponse(false);
        }
    };

    const handleImageClick = (imageUrl: string) => {
        setSelectedImageUrl(imageUrl);
        setShowImagePreviewModal(true);
    };

    const closeImagePreviewModal = () => {
        setShowImagePreviewModal(false);
        setSelectedImageUrl(null);
    };


    if (loading && !character) {
        return (
            <div className="container mt-3 d-flex justify-content-center align-items-center" style={{ minHeight: '80vh' }}>
                <LoadingSpinner />
            </div>
        );
    }

    if (error && !character) { // If character fetch failed entirely
        return (
            <div className="container mt-3">
                <AlertMessage type="error" message={error} />
                <Link to="/characters" className="btn btn-secondary mt-3">
                    Back to Character List
                </Link>
            </div>
        );
    }

    if (!character) {
        return (
            <div className="container mt-3">
                <AlertMessage type="info" message="Character data is not available or could not be loaded." />
                <Link to="/characters" className="btn btn-secondary mt-3">
                    Back to Character List
                </Link>
            </div>
        );
    }

    // Filter out campaigns that are already associated for the link dropdown
    const availableCampaignsToLink = userCampaigns.filter(
        camp => !associatedCampaigns.some(ac => ac.id === camp.id)
    );

    return (
        <div className="container mt-4 character-detail-page">
            <div className="page-header mb-4">
                <h1>{character.name}</h1>
                <div className="header-actions">
                    <Link to={`/characters/${character.id}/edit`} className="btn btn-outline-primary me-2">
                        Edit Character
                    </Link>
                    <button onClick={openDeleteModal} className="btn btn-outline-danger">
                        Delete Character
                    </button>
                </div>
            </div>

            {error && <AlertMessage type="error" message={error} onClose={() => setError(null)} />}
            {successMessage && <AlertMessage type="success" message={successMessage} onClose={() => setSuccessMessage(null)} />}

            {/* Main Content Grid */}
            <div className="character-content-grid">
                {/* Left Column: Core Details */}
                <div className="character-main-column">
                    {character.description && (
                        <div className="card data-card mb-3">
                            <div className="card-header">Description</div>
                            <div className="card-body">
                                <p className="card-text pre-wrap">{character.description}</p>
                            </div>
                        </div>
                    )}

                    {character.appearance_description && (
                        <div className="card data-card mb-3">
                            <div className="card-header">Appearance</div>
                            <div className="card-body">
                                <p className="card-text pre-wrap">{character.appearance_description}</p>
                            </div>
                        </div>
                    )}

                    {character.notes_for_llm && (
                        <div className="card data-card mb-3">
                            <div className="card-header">Notes for LLM</div>
                            <div className="card-body">
                                <p className="card-text pre-wrap">{character.notes_for_llm}</p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Column: Stats, Images, etc. */}
                <div className="character-sidebar-column">
                    <div className="card data-card mb-3">
                        <div className="card-header">Stats</div>
                        <div className="card-body">
                            {renderStats(character.stats)}
                        </div>
                    </div>

                    <div className="card data-card mb-3">
                        <div className="card-header d-flex justify-content-between align-items-center">
                            Images
                            <button
                                className="btn btn-sm btn-success"
                                onClick={handleGenerateNewImage}
                                disabled={isGeneratingImage}
                            >
                                {isGeneratingImage ? <><LoadingSpinner size="sm" /> Generating...</> : 'Generate New'}
                            </button>
                        </div>
                        <div className="card-body">
                            {imageGenError && <AlertMessage type="error" message={imageGenError} onClose={() => setImageGenError(null)} />}
                            <div className="character-image-gallery">
                                {character.image_urls && character.image_urls.length > 0 ? (
                                    character.image_urls.map((url, index) => (
                                        <div key={index} className="character-image-thumbnail-wrapper" onClick={() => handleImageClick(url)}>
                                            <img
                                                src={url}
                                                alt={`${character.name} ${index + 1}`}
                                                className="character-image-thumbnail"
                                                onError={(e) => {
                                                    const target = e.target as HTMLImageElement;
                                                    if (target.src !== DEFAULT_PLACEHOLDER_IMAGE) {
                                                        target.src = DEFAULT_PLACEHOLDER_IMAGE;
                                                        target.alt = "Placeholder image";
                                                    }
                                                }}
                                            />
                                        </div>
                                    ))
                                ) : (
                                    !isGeneratingImage && <p className="text-muted small">No images provided. Try generating one!</p>
                                )}
                                {isGeneratingImage && (!character.image_urls || character.image_urls.length === 0) &&
                                    <div className="text-center w-100"><LoadingSpinner /> <p className="text-muted small mt-1">Generating first image...</p></div>
                                }
                            </div>
                        </div>
                    </div>
                </div>
            </div>


            {character.video_clip_urls && character.video_clip_urls.length > 0 && (
                 <div className="card data-card mb-3">
                    <div className="card-header">Video Clips</div>
                    <div className="card-body">
                        <ul className="list-unstyled">
                        {character.video_clip_urls.map((url, index) => (
                            <li key={index}><a href={url} target="_blank" rel="noopener noreferrer">{url}</a></li>
                        ))}
                        </ul>
                    </div>
                </div>
            )}


            {/* LLM Interaction Section - Full Width Below Grid */}
            <div className="card data-card mb-3">
                <div className="card-header">Interact with {character.name} (AI)</div>
                <div className="card-body">
                    <div className="mb-3">
                        <label htmlFor="llmUserPrompt" className="form-label">Your message to {character.name}:</label>
                        <textarea
                            id="llmUserPrompt"
                            className="form-control"
                            rows={3}
                            value={llmUserPrompt}
                            onChange={(e) => setLlmUserPrompt(e.target.value)}
                            placeholder={`e.g., "What are your thoughts on the encroaching shadow in the North?"`}
                            disabled={isGeneratingResponse}
                        />
                    </div>
                    <button
                        className="btn btn-info"
                        onClick={handleGenerateCharacterResponse}
                        disabled={isGeneratingResponse || !llmUserPrompt.trim()}
                    >
                        {isGeneratingResponse ? <><LoadingSpinner size="sm" /> Getting Response...</> : `Ask ${character.name}`}
                    </button>
                    {llmError && <AlertMessage type="error" message={llmError} onClose={() => setLlmError(null)} customClasses="mt-3" />}
                    {llmResponse && (
                        <div className="mt-3 p-3 border rounded bg-light llm-response-area">
                            <strong>{character.name} responds:</strong>
                            <p className="pre-wrap">{llmResponse}</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Campaign Association Management - Full Width */}
            <div className="card data-card mb-3">
                <div className="card-header">Campaign Associations</div>
                <div className="card-body">
                    {linkError && <AlertMessage type="error" message={linkError} onClose={() => setLinkError(null)} />}
                    <h5>Currently In Campaigns:</h5>
                    {associatedCampaigns.length > 0 ? (
                        <ul className="list-group list-group-flush mb-3">
                            {associatedCampaigns.map(camp => (
                                <li key={camp.id} className="list-group-item d-flex justify-content-between align-items-center">
                                    <Link to={`/campaign/${camp.id}`}>{camp.title}</Link>
                                    <button
                                        className="btn btn-sm btn-outline-warning"
                                        onClick={() => handleUnlinkCampaign(camp.id, camp.title)}
                                        disabled={isLinking}
                                    >
                                        {isLinking ? <LoadingSpinner size="sm" /> : 'Unlink'}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-muted">Not currently associated with any campaigns.</p>
                    )}
                    <hr />
                    <h5>Link to a Campaign:</h5>
                    {userCampaigns.length > 0 && availableCampaignsToLink.length > 0 ? (
                        <div className="input-group">
                            <select
                                className="form-select"
                                value={selectedCampaignToLink}
                                onChange={(e) => setSelectedCampaignToLink(e.target.value)}
                                disabled={isLinking}
                            >
                                <option value="">Select a campaign...</option>
                                {availableCampaignsToLink.map(camp => (
                                    <option key={camp.id} value={camp.id}>{camp.title}</option>
                                ))}
                            </select>
                            <button
                                className="btn btn-outline-success"
                                type="button"
                                onClick={handleLinkCampaign}
                                disabled={!selectedCampaignToLink || isLinking}
                            >
                                {isLinking ? <><LoadingSpinner size="sm" /> Linking...</> : 'Link to Campaign'}
                            </button>
                        </div>
                    ) : (
                         userCampaigns.length > 0 && availableCampaignsToLink.length === 0 ?
                         <p className="text-muted">This character is already linked to all your available campaigns.</p> :
                         <p className="text-muted">You don't have any campaigns to link this character to, or no unlinked campaigns available.</p>
                    )}
                </div>
            </div>

            <div className="mt-4 mb-3 text-center">
                <Link to="/characters" className="btn btn-secondary">
                    Back to Character List
                </Link>
            </div>

            {selectedImageUrl && (
                <ImagePreviewModal
                    isOpen={showImagePreviewModal}
                    onClose={closeImagePreviewModal}
                    imageUrl={selectedImageUrl}
                    imageAlt={`${character.name} - Preview`}
                />
            )}

            {character && (
                <ConfirmationModal
                    isOpen={showDeleteModal}
                    title="Confirm Deletion"
                    message={`Are you sure you want to delete the character "${character.name}"? This action cannot be undone.`}
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

export default CharacterDetailPage;
