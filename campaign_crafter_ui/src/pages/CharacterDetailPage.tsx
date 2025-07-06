import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import * as characterService from '../services/characterService';
// Corrected import: CharacterImageGenerationRequest and CharacterUpdate from characterTypes
import { Character, CharacterStats, CharacterImageGenerationRequest, CharacterUpdate } from '../types/characterTypes';
import * as campaignService from '../services/campaignService';
import { Campaign } from '../types/campaignTypes';
import { ChatMessage as CharacterChatMessage } from '../components/characters/CharacterChatPanel'; // Import ChatMessage type
import LoadingSpinner from '../components/common/LoadingSpinner';
import ImagePreviewModal from '../components/modals/ImagePreviewModal';
import AlertMessage from '../components/common/AlertMessage';
import ConfirmationModal from '../components/modals/ConfirmationModal';
import CharacterImagePromptModal, { CharacterImageGenSettings } from '../components/modals/CharacterImagePromptModal';
import CharacterChatPanel from '../components/characters/CharacterChatPanel';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  rectSortingStrategy, // Or verticalListSortingStrategy if preferred for single column
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import './CharacterDetailPage.css';

const DEFAULT_PLACEHOLDER_IMAGE = '/logo_placeholder.svg';

// New Sortable Item Component for Character Images
interface SortableCharacterImageProps {
  id: string; // Using image URL as ID
  url: string;
  characterName: string;
  index: number;
  onImageClick: (url: string) => void;
}

const SortableCharacterImage: React.FC<SortableCharacterImageProps> = ({ id, url, characterName, index, onImageClick }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging, // Added to provide dragging style
  } = useSortable({ id });

  const itemStyle = { // Renamed from style to avoid conflict if CharacterDetailPage itself has a 'style' const
    transform: CSS.Transform.toString(transform),
    transition,
    cursor: 'grab',
    // Opacity will be handled by CSS via the 'dragging' class
  };

  return (
    <div
      ref={setNodeRef}
      style={itemStyle}
      {...attributes}
      {...listeners}
      className={`character-image-thumbnail-wrapper ${isDragging ? 'dragging' : ''}`} // Conditionally add 'dragging' class
      onClick={() => onImageClick(url)}
    >
      <img
        src={url}
        alt={`${characterName} ${index + 1}`}
        className="character-image-thumbnail" // Existing class
        onError={(e) => {
          const target = e.target as HTMLImageElement;
          if (target.src !== DEFAULT_PLACEHOLDER_IMAGE) {
            target.src = DEFAULT_PLACEHOLDER_IMAGE;
            target.alt = "Placeholder image";
          }
        }}
      />
    </div>
  );
};

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

    // New Modal State for Character Image Generation Prompt
    const [isCharImagePromptModalOpen, setIsCharImagePromptModalOpen] = useState<boolean>(false);

    // Character Chat Panel State
    const [isChatPanelOpen, setIsChatPanelOpen] = useState<boolean>(false);

    const [chatHistory, setChatHistory] = useState<Array<CharacterChatMessage>>([]);

    // State for LLM Notes visibility
    const [showLlmNotes, setShowLlmNotes] = useState<boolean>(false); // Default to collapsed

    // States for other collapsible sections
    const [showStats, setShowStats] = useState<boolean>(true); // Expanded by default
    const [showDescription, setShowDescription] = useState<boolean>(true); // Expanded by default
    const [showAppearance, setShowAppearance] = useState<boolean>(true); // Expanded by default
    const [showImages, setShowImages] = useState<boolean>(false); // Collapsed by default
    const [showVideoClips, setShowVideoClips] = useState<boolean>(false); // Collapsed by default
    const [showCampaignAssociations, setShowCampaignAssociations] = useState<boolean>(false); // Collapsed by default

    // DND Kit Sensors
    const sensors = useSensors(
        useSensor(PointerSensor, {
            // Require the mouse to move by 8 pixels before starting a drag
            // Allows click events to fire if movement is less than this.
            activationConstraint: {
                distance: 8,
            },
        }),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const handleDragEnd = async (event: DragEndEvent) => {
        const { active, over } = event;

        if (active.id !== over?.id && character && character.image_urls) {
            const oldIndex = character.image_urls.findIndex(url => url === active.id);
            const newIndex = character.image_urls.findIndex(url => url === over?.id);

            if (oldIndex === -1 || newIndex === -1) return; // Should not happen if IDs are URLs

            const newImageUrls = arrayMove(character.image_urls, oldIndex, newIndex);

            // Optimistic update
            setCharacter(prev => prev ? { ...prev, image_urls: newImageUrls } : null);

            // Persist to backend
            try {
                const payload: CharacterUpdate = { image_urls: newImageUrls };
                // Assuming character.id is available and correct
                await characterService.updateCharacter(character.id, payload);
                // Optionally show a success message or rely on optimistic update
                setSuccessMessage("Image order saved.");
                setTimeout(() => setSuccessMessage(null), 3000);
            } catch (err) {
                console.error("Failed to save image order:", err);
                setError("Failed to save new image order. Reverting.");
                // Revert optimistic update on error
                setCharacter(prev => prev ? { ...prev, image_urls: character.image_urls } : null);
                setTimeout(() => setError(null), 5000);
            }
        }
    };


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
            navigate('/characters', { state: { successMessage: `Character "${character.name}" deleted successfully.` } });
        } catch (err: any) {
            console.error("Failed to delete character:", err);
            setError(err.response?.data?.detail || 'Failed to delete character. Please try again');
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
            setImageGenError("Character data not available.");
            return;
        }
        setIsCharImagePromptModalOpen(true); // Open the new modal instead of direct generation
    };

    const handleSubmitCharacterImageGeneration = async (basePrompt: string, additionalDetails: string, settings: CharacterImageGenSettings) => {
        if (!character) {
            setImageGenError("Character data not available for image generation.");
            return;
        }
        setIsGeneratingImage(true);
        setImageGenError(null);
        setSuccessMessage(null);
        setIsCharImagePromptModalOpen(false); // Close modal on submit

        try {
            const finalAdditionalDetails = `${basePrompt} ${additionalDetails}`.trim();

            const requestPayload: CharacterImageGenerationRequest = {
                additional_prompt_details: finalAdditionalDetails, // This contains the user's full desired prompt info
                model_name: settings.model_name,
                size: settings.size,
                quality: settings.quality,
                steps: settings.steps,
                cfg_scale: settings.cfg_scale,
                gemini_model_name: settings.gemini_model_name,
            };

            const updatedCharacter = await characterService.generateCharacterImage(character.id, requestPayload);
            setCharacter(updatedCharacter); // Update character state with the new image URL
            setSuccessMessage("New image generated successfully!");

        } catch (err: any) { // Ensure this catch is correctly placed
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
        // setLlmResponse(null); // Clear previous direct response, new one will come via history

        const userMessage: CharacterChatMessage = { speaker: 'user', text: llmUserPrompt };
        // Optimistically update UI with user's message
        // Create a snapshot of history *before* this user message for the API call
        const historyForApi = [...chatHistory];
        setChatHistory(prevHistory => [...prevHistory, userMessage]);

        const currentPrompt = llmUserPrompt; // Capture before clearing
        setLlmUserPrompt(''); // Clear the input field immediately

        try {
            // Send the history *before* the current user message for context,
            // and the current user message as the new prompt.
            // The backend is expected to handle the prompt and the history separately.
            // The `historyForApi` is what the character is responding *to*, considering `currentPrompt` as the newest thing.
            // However, the backend was updated to expect chat_history to include the latest user message.
            // So, we send `chatHistory` including the just-added user message.
            const updatedHistoryForApi = [...historyForApi, userMessage];

            const response = await characterService.generateCharacterResponse(character.id, {
                prompt: currentPrompt, // Still send the current prompt explicitly
                chat_history: updatedHistoryForApi.map(msg => ({ // Ensure plain objects if service expects that
                    speaker: msg.speaker,
                    text: msg.text,
                })),
            });

            const aiMessage: CharacterChatMessage = { speaker: character.name, text: response.text };
            setChatHistory(prevHistory => [...prevHistory, aiMessage]);
            setLlmResponse(null); // Ensure any old direct llmResponse is cleared
        } catch (err: any) {
            console.error("Failed to generate character response:", err);
            setLlmError(err.response?.data?.detail || "Failed to get response from character.");
            // Optional: If user message failed to send, remove it from history
            // setChatHistory(prevHistory => prevHistory.slice(0, -1));
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
            <div className="page-header-nav mb-3">
                <Link to="/characters" className="btn btn-sm btn-outline-secondary">
                    &larr; Back to Character List
                </Link>
            </div>
            <div className="page-header mb-4">
                {/* Title now takes available space, actions are on the right */}
                <h1 className="character-title">{character.name}</h1>
                <div className="header-actions">
                    <Link to={`/characters/${character.id}/edit`} className="btn btn-outline-primary">
                        <i className="bi bi-pencil-square"></i> Edit
                    </Link>
                    <button onClick={openDeleteModal} className="btn btn-outline-danger">
                        <i className="bi bi-trash"></i> Delete
                    </button>
                    <button
                        onClick={() => setIsChatPanelOpen(prev => !prev)}
                        className="btn btn-outline-info"
                        title={isChatPanelOpen ? "Close Chat" : "Chat with Character"}
                    >
                        💬 Chat
                    </button>
                </div>
            </div>

            {error && <AlertMessage type="error" message={error} onClose={() => setError(null)} />}
            {successMessage && <AlertMessage type="success" message={successMessage} onClose={() => setSuccessMessage(null)} />}

            {/* Main Content Grid */}
            <div className="character-content-grid">
                {/* Left Column: Core Details */}
                <div className="character-main-column">
                    {/* Stats Card MOVED HERE - to be the first item in the main column */}
                    <div className="card data-card mb-3">
                        <div
                            className="card-header d-flex justify-content-between align-items-center"
                            onClick={() => setShowStats(!showStats)}
                            style={{ cursor: 'pointer' }}
                        >
                            <span>Stats</span>
                            {showStats ? <i className="bi bi-chevron-up"></i> : <i className="bi bi-chevron-down"></i>}
                        </div>
                        {showStats && (
                            <div className="card-body">
                                {renderStats(character.stats)}
                            </div>
                        )}
                    </div>

                    {/* "Notes for LLM" moved here, after Stats */}
                    {character.notes_for_llm && (
                        <div className="card data-card mb-3">
                            <div
                                className="card-header d-flex justify-content-between align-items-center"
                                onClick={() => setShowLlmNotes(!showLlmNotes)} // Make the entire header clickable
                                style={{ cursor: 'pointer' }} // Add pointer cursor to indicate clickability
                            >
                                <span>Notes for LLM</span> {/* Wrap title in span for flex control */}
                                {/* Icon indicating collapsed/expanded state */}
                                {showLlmNotes ? <i className="bi bi-chevron-up"></i> : <i className="bi bi-chevron-down"></i>}
                            </div>
                            {showLlmNotes && (
                                <div className="card-body">
                                    <p className="card-text pre-wrap">{character.notes_for_llm}</p>
                                </div>
                            )}
                            {/* The part for "{!showLlmNotes && ... (Notes are hidden)}" is completely removed */}
                        </div>
                    )}

                    {character.description && (
                        <div className="card data-card mb-3">
                            <div
                                className="card-header d-flex justify-content-between align-items-center"
                                onClick={() => setShowDescription(!showDescription)}
                                style={{ cursor: 'pointer' }}
                            >
                                <span>Description</span>
                                {showDescription ? <i className="bi bi-chevron-up"></i> : <i className="bi bi-chevron-down"></i>}
                            </div>
                            {showDescription && (
                                <div className="card-body">
                                    <p className="card-text pre-wrap">{character.description}</p>
                                </div>
                            )}
                        </div>
                    )}

                    {character.appearance_description && (
                        <div className="card data-card mb-3">
                            <div
                                className="card-header d-flex justify-content-between align-items-center"
                                onClick={() => setShowAppearance(!showAppearance)}
                                style={{ cursor: 'pointer' }}
                            >
                                <span>Appearance</span>
                                {showAppearance ? <i className="bi bi-chevron-up"></i> : <i className="bi bi-chevron-down"></i>}
                            </div>
                            {showAppearance && (
                                <div className="card-body">
                                    <p className="card-text pre-wrap">{character.appearance_description}</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Right Column: Images, etc. (Stats removed from here) */}
                <div className="character-sidebar-column">
                    <div className="card data-card mb-3">
                        <div
                            className="card-header d-flex justify-content-between align-items-center mb-3"
                            onClick={() => setShowImages(!showImages)}
                            style={{ cursor: 'pointer' }}
                        >
                            <span>Images</span>
                            <div> {/* Wrapper for button and chevron */}
                                <button
                                    className="btn btn-sm btn-success me-2"
                                    onClick={(e) => {
                                        e.stopPropagation(); // Prevent header onClick
                                        handleGenerateNewImage();
                                    }}
                                    disabled={isGeneratingImage}
                                >
                                    {isGeneratingImage ? <><LoadingSpinner /> Generating...</> : 'Generate New'}
                                </button>
                                {showImages ? <i className="bi bi-chevron-up"></i> : <i className="bi bi-chevron-down"></i>}
                            </div>
                        </div>
                        {showImages && (
                            <div className="card-body">
                                {imageGenError && <AlertMessage type="error" message={imageGenError} onClose={() => setImageGenError(null)} />}
                                <DndContext
                                sensors={sensors}
                                collisionDetection={closestCenter}
                                onDragEnd={handleDragEnd}
                            >
                                <SortableContext
                                    items={character.image_urls?.map(url => url) || []}
                                    strategy={rectSortingStrategy} // Good for grids
                                >
                                    <div className="character-image-gallery">
                                        {character.image_urls && character.image_urls.length > 0 ? (
                                            character.image_urls.map((url, index) => (
                                                <SortableCharacterImage
                                                    key={url} // Use URL as key for DND
                                                    id={url}  // Use URL as ID for DND
                                                    url={url}
                                                    characterName={character.name}
                                                    index={index}
                                                    onImageClick={handleImageClick}
                                                />
                                            ))
                                        ) : (
                                            !isGeneratingImage && <p className="text-muted small">No images provided. Try generating one!</p>
                                        )}
                                        {isGeneratingImage && (!character.image_urls || character.image_urls.length === 0) &&
                                            <div className="text-center w-100"><LoadingSpinner /> <p className="text-muted small mt-1">Generating first image...</p></div>
                                        }
                                    </div>
                                </SortableContext>
                            </DndContext>
                        </div> // Correctly closes card-body
                        )} {/* Correctly closes showImages conditional block */}
                    </div> // Correctly closes the Images card <div className="card data-card mb-3">
                </div> // Correctly closes the <div className="character-sidebar-column">
            </div> {/* ADDED: Closes character-content-grid */}


            {character.video_clip_urls && character.video_clip_urls.length > 0 && (
                <div className="card data-card mb-3">
                    <div
                        className="card-header d-flex justify-content-between align-items-center"
                        onClick={() => setShowVideoClips(!showVideoClips)}
                        style={{ cursor: 'pointer' }}
                    >
                        <span>Video Clips</span>
                        {showVideoClips ? <i className="bi bi-chevron-up"></i> : <i className="bi bi-chevron-down"></i>}
                    </div>
                    {showVideoClips && (
                        <div className="card-body">
                            <table className="table table-sm">
                                <thead>
                                <tr>
                                    <th>URL</th>
                                    <th style={{ width: '100px' }}>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {character.video_clip_urls.map((url, index) => (
                                    <tr key={index}>
                                        <td>
                                            <a href={url} target="_blank" rel="noopener noreferrer" title={url}>
                                                {url.length > 70 ? `${url.substring(0, 67)}...` : url}
                                            </a>
                                        </td>
                                        <td>
                                            <a href={url} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-outline-primary">
                                                Open
                                            </a>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div> // Closes card-body
                    )} {/* Closes showVideoClips conditional */}
                </div> // Closes the Video Clips card <div className="card data-card mb-3">
            )} {/* Closes the character.video_clip_urls conditional */}

            {/* Campaign Association Management - Full Width */}
            <div className="card data-card mb-3">
                <div
                    className="card-header d-flex justify-content-between align-items-center"
                    onClick={() => setShowCampaignAssociations(!showCampaignAssociations)}
                    style={{ cursor: 'pointer' }}
                >
                    <span>Campaign Associations</span>
                    {showCampaignAssociations ? <i className="bi bi-chevron-up"></i> : <i className="bi bi-chevron-down"></i>}
                </div>
                {showCampaignAssociations && (
                    <div className="card-body">
                        {linkError && <AlertMessage type="error" message={linkError} onClose={() => setLinkError(null)} />}
                        <h5>Currently In Campaigns:</h5>
                    {associatedCampaigns.length > 0 ? (
                        <div className="associated-campaigns-list mb-3"> {/* New wrapper class, kept mb-3 */}
                            {associatedCampaigns.map(camp => (
                                <div key={camp.id} className="associated-campaign-item">
                                    <img
                                        src={camp.badge_image_url || camp.thematic_image_url || '/logo_placeholder.svg'}
                                        alt={`Campaign: ${camp.title}`}
                                        className="associated-campaign-thumbnail"
                                        onError={(e) => {
                                            const target = e.target as HTMLImageElement;
                                            if (target.src !== '/logo_placeholder.svg') {
                                                target.src = '/logo_placeholder.svg';
                                                target.alt = "Placeholder image";
                                            }
                                        }}
                                    />
                                    <Link to={`/campaign/${camp.id}`} className="associated-campaign-name">
                                        {camp.title}
                                    </Link>
                                    <button
                                        className="btn btn-icon btn-outline-danger" // btn-sm removed
                                        onClick={() => handleUnlinkCampaign(camp.id, camp.title)}
                                        disabled={isLinking}
                                        title={`Unlink from ${camp.title}`}
                                    >
                                        {isLinking ? <LoadingSpinner /> : <i className="bi bi-x-circle"></i>}
                                    </button>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-muted">Not currently associated with any campaigns.</p>
                    )}
                    <hr />
                    <h5>Link to a Campaign:</h5>
                    {userCampaigns.length > 0 && availableCampaignsToLink.length > 0 ? (
                        <div className="link-campaign-controls"> {/* New wrapper div */}
                            <select
                                className="form-select me-2" // Add margin to separate from link
                                value={selectedCampaignToLink}
                                onChange={(e) => setSelectedCampaignToLink(e.target.value)}
                                disabled={isLinking}
                                style={{ width: 'auto', flexGrow: 1 }} // Allow select to take space
                            >
                                <option value="">Select a campaign...</option>
                                {availableCampaignsToLink.map(camp => (
                                    <option key={camp.id} value={camp.id}>{camp.title}</option>
                                ))}
                            </select>
                            <button
                                className="btn btn-link text-success p-0 align-baseline" // Use btn-link, remove padding, ensure text color, align baseline
                                type="button"
                                onClick={handleLinkCampaign}
                                disabled={!selectedCampaignToLink || isLinking}
                                title="Link selected campaign"
                            >
                                {isLinking ? (
                                    <><LoadingSpinner /> Linking...</>
                                ) : (
                                    <><i className="bi bi-plus-circle"></i> Link</> // Using a plus-circle icon
                                )}
                            </button>
                        </div>
                    ) : (
                         userCampaigns.length > 0 && availableCampaignsToLink.length === 0 ?
                         <p className="text-muted">This character is already linked to all your available campaigns.</p> :
                         <p className="text-muted">You don't have any campaigns to link this character to, or no unlinked campaigns available.</p>
                    )}
                    </div>
                )}
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

            {character && (
              <CharacterImagePromptModal
                isOpen={isCharImagePromptModalOpen}
                onClose={() => setIsCharImagePromptModalOpen(false)}
                character={character}
                onSubmit={handleSubmitCharacterImageGeneration}
                isGenerating={isGeneratingImage}
              />
            )}

            {character && (
                <CharacterChatPanel
                    characterName={character.name}
                    isOpen={isChatPanelOpen}
                    onClose={() => setIsChatPanelOpen(false)}
                    llmUserPrompt={llmUserPrompt}
                    setLlmUserPrompt={setLlmUserPrompt}
                    handleGenerateCharacterResponse={handleGenerateCharacterResponse}
                    isGeneratingResponse={isGeneratingResponse}
                    llmResponse={llmResponse} // This could be removed if panel solely relies on chatHistory
                    llmError={llmError}
                    chatHistory={chatHistory} // Pass the chat history
                />
            )}
        </div>
    );
};

export default CharacterDetailPage;
