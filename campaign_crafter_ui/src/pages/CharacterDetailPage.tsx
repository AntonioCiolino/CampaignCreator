import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import * as characterService from '../services/characterService';
import * as campaignService from '../services/campaignService'; // Import campaignService
import { Character, CharacterStats } from '../types/characterTypes';
import { Campaign } from '../types/campaignTypes'; // Assuming campaignTypes.ts exists or will be created
import LoadingSpinner from '../components/common/LoadingSpinner'; // Import LoadingSpinner
// import './CharacterDetailPage.css';

const CharacterDetailPage: React.FC = () => {
    const { characterId } = useParams<{ characterId: string }>();
    const navigate = useNavigate(); // For navigation after delete

    const [character, setCharacter] = useState<Character | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [userCampaigns, setUserCampaigns] = useState<Campaign[]>([]);
    const [selectedCampaignToLink, setSelectedCampaignToLink] = useState<string>('');
    const [linkError, setLinkError] = useState<string | null>(null);
    const [isLinking, setIsLinking] = useState<boolean>(false);

    // State for currently associated campaigns - this is the tricky part
    // We don't get this from GET /characters/{id}
    // For now, this will remain unpopulated. Unlinking UI won't be fully functional.
    const [associatedCampaigns, setAssociatedCampaigns] = useState<Campaign[]>([]);


    useEffect(() => {
        const fetchPageData = async () => {
            if (characterId) {
                setLoading(true);
                try {
                    const id = parseInt(characterId, 10);
                    if (isNaN(id)) {
                        setError("Invalid character ID.");
                        setLoading(false);
                        return;
                    }
                    // Fetch character details
                    const fetchedCharacter = await characterService.getCharacterById(id);
                    setCharacter(fetchedCharacter);

                    // Fetch all user campaigns for the dropdown
                    const campaigns = await campaignService.getAllCampaigns();
                    setUserCampaigns(campaigns);

                    // TODO: Fetch campaigns character is ALREADY part of, if an endpoint exists
                    // e.g., const linkedCampaigns = await characterService.getCharacterCampaigns(id);
                    // setAssociatedCampaigns(linkedCampaigns);

                    setError(null);
                } catch (err: any) {
                    console.error("Failed to fetch character details or campaigns:", err);
                    if (err.response && err.response.status === 404) {
                        setError('Character not found.');
                    } else if (err.response && err.response.status === 403) {
                        setError('You are not authorized to view this character or related campaigns.');
                    } else {
                        setError('Failed to load character details or campaigns. Please try again later.');
                    }
                    setCharacter(null);
                    setUserCampaigns([]);
                } finally {
                    setLoading(false);
                }
            } else {
                setError("No character ID provided.");
                setLoading(false);
            }
        };
        fetchPageData();
    }, [characterId]);

    const handleLinkCampaign = async () => {
        if (!character || !selectedCampaignToLink) {
            setLinkError("Please select a campaign to link.");
            return;
        }
        setIsLinking(true);
        setLinkError(null);
        try {
            const campaignIdToLink = parseInt(selectedCampaignToLink, 10);
            await characterService.linkCharacterToCampaign(character.id, campaignIdToLink);
            alert(`${character.name} successfully linked to campaign.`);
            setSelectedCampaignToLink(''); // Reset dropdown
            // TODO: Refresh associated campaigns list here if it were displayed
            // For now, the user has to manually verify or refresh the page (or navigate to campaign)
        } catch (err: any) {
            console.error("Failed to link character to campaign:", err);
            setLinkError(err.response?.data?.detail || "Failed to link campaign.");
        } finally {
            setIsLinking(false);
        }
    };

    // Placeholder for unlinking - would need associatedCampaigns to be populated
    const handleUnlinkCampaign = async (campaignIdToUnlink: number) => {
        if (!character) return;
        if (window.confirm(`Are you sure you want to unlink ${character.name} from this campaign?`)) {
            setIsLinking(true); // Reuse isLinking for general association operations
            setLinkError(null);
            try {
                await characterService.unlinkCharacterFromCampaign(character.id, campaignIdToUnlink);
                alert(`${character.name} successfully unlinked from campaign.`);
                // TODO: Refresh associated campaigns list here
                // setAssociatedCampaigns(prev => prev.filter(c => c.id !== campaignIdToUnlink));
            } catch (err: any) {
                console.error("Failed to unlink character from campaign:", err);
                setLinkError(err.response?.data?.detail || "Failed to unlink campaign.");
            } finally {
                setIsLinking(false);
            }
        }
    };

    useEffect(() => {
        if (characterId) {
            const fetchCharacterDetails = async () => {
                try {
                    setLoading(true);
                    const id = parseInt(characterId, 10);
                    if (isNaN(id)) {
                        setError("Invalid character ID.");
                        setCharacter(null);
                        return;
                    }
                    const fetchedCharacter = await characterService.getCharacterById(id);
                    setCharacter(fetchedCharacter);
                    setError(null);
                } catch (err: any) {
                    console.error("Failed to fetch character details:", err);
                    if (err.response && err.response.status === 404) {
                        setError('Character not found.');
                    } else if (err.response && err.response.status === 403) {
                        setError('You are not authorized to view this character.');
                    } else {
                        setError('Failed to load character details. Please try again later.');
                    }
                    setCharacter(null);
                } finally {
                    setLoading(false);
                }
            };
            fetchCharacterDetails();
        } else {
            setError("No character ID provided.");
            setLoading(false);
        }
    }, [characterId]);

    const handleDelete = async () => {
        if (character && window.confirm(`Are you sure you want to delete "${character.name}"? This action cannot be undone.`)) {
            try {
                setLoading(true); // Indicate loading state during deletion
                await characterService.deleteCharacter(character.id);
                alert('Character deleted successfully.'); // Simple notification
                navigate('/characters'); // Navigate to character list
            } catch (err: any) {
                console.error("Failed to delete character:", err);
                setError(err.response?.data?.detail || 'Failed to delete character. Please try again.');
                setLoading(false); // Reset loading state on error
            }
            // No need to setLoading(false) on success as we navigate away
        }
    };

    const renderStats = (stats: CharacterStats | null | undefined) => {
        if (!stats) return <p className="card-text text-muted">No stats available.</p>;

        const statItems = [
            { label: "Strength", value: stats.strength },
            { label: "Dexterity", value: stats.dexterity },
            { label: "Constitution", value: stats.constitution },
            { label: "Intelligence", value: stats.intelligence },
            { label: "Wisdom", value: stats.wisdom },
            { label: "Charisma", value: stats.charisma },
        ];

        return (
            <div className="row">
                {statItems.map(stat => (
                    <div key={stat.label} className="col-md-4 col-6 mb-2">
                        <dt className="text-muted small text-uppercase">{stat.label}</dt>
                        <dd className="fs-5">{stat.value ?? '10'}</dd> {/* Display 10 if N/A or undefined */}
                    </div>
                ))}
            </div>
        );
    };

    if (loading) {
        // return <div className="container mt-3"><p>Loading character details...</p></div>;
        return <div className="container mt-3 d-flex justify-content-center"><LoadingSpinner /></div>;
    }

    if (error) {
        return <div className="container mt-3"><p className="text-danger">{error}</p></div>;
    }

    if (!character) {
        // This case should ideally be covered by error state if characterId was valid but fetch failed
        return <div className="container mt-3"><p>Character data is not available.</p></div>;
    }

    return (
        <div className="container mt-3 character-detail-page">
            <div className="d-flex justify-content-between align-items-center mb-3">
                <h1>{character.name}</h1>
                <div>
                    <Link to={`/characters/${character.id}/edit`} className="btn btn-outline-primary me-2">
                        Edit
                    </Link>
                    <button onClick={handleDelete} className="btn btn-outline-danger">
                        Delete
                    </button>
                </div>
            </div>

            {character.description && (
                <div className="card mb-3">
                    <div className="card-header">Description</div>
                    <div className="card-body">
                        <p className="card-text">{character.description}</p>
                    </div>
                </div>
            )}

            {character.appearance_description && (
                <div className="card mb-3">
                    <div className="card-header">Appearance</div>
                    <div className="card-body">
                        <p className="card-text">{character.appearance_description}</p>
                    </div>
                </div>
            )}

            <div className="card mb-3">
                <div className="card-header">Stats</div>
                {renderStats(character.stats)}
            </div>

            {character.image_urls && character.image_urls.length > 0 && (
                <div className="card mb-3">
                    <div className="card-header">Images</div>
                    <div className="card-body">
                        {character.image_urls.map((url, index) => (
                            <img key={index} src={url} alt={`${character.name} image ${index + 1}`} className="img-thumbnail me-2 mb-2" style={{ maxWidth: '200px', maxHeight: '200px' }} onError={(e) => (e.currentTarget.style.display = 'none')} />
                        ))}
                         {character.image_urls.length === 0 && <p>No images provided.</p>}
                    </div>
                </div>
            )}

            {character.video_clip_urls && character.video_clip_urls.length > 0 && (
                 <div className="card mb-3">
                    <div className="card-header">Video Clips</div>
                    <div className="card-body">
                        <ul className="list-unstyled">
                        {character.video_clip_urls.map((url, index) => (
                            <li key={index}><a href={url} target="_blank" rel="noopener noreferrer">{url}</a></li>
                        ))}
                        </ul>
                        {character.video_clip_urls.length === 0 && <p>No video clips provided.</p>}
                    </div>
                </div>
            )}

            {character.notes_for_llm && (
                <div className="card mb-3">
                    <div className="card-header">Notes for LLM</div>
                    <div className="card-body">
                        <p className="card-text">{character.notes_for_llm}</p>
                    </div>
                </div>
            )}

            {/* Placeholder for Campaign Association Management - to be implemented later */}
            <div className="card mb-3">
                <div className="card-header">Campaign Associations</div>
                <div className="card-body">
                    {/* Section to display ALREADY associated campaigns - NOT YET FUNCTIONAL */}
                    <h5>Currently In Campaigns:</h5>
                    {associatedCampaigns.length > 0 ? (
                        <ul className="list-group mb-3">
                            {associatedCampaigns.map(camp => (
                                <li key={camp.id} className="list-group-item d-flex justify-content-between align-items-center">
                                    <Link to={`/campaign/${camp.id}`}>{camp.title}</Link>
                                    <button
                                        className="btn btn-sm btn-outline-warning"
                                        onClick={() => handleUnlinkCampaign(camp.id)}
                                        disabled={isLinking}
                                    >
                                        Unlink
                                    </button>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-muted">Not currently part of any campaigns (that we know of on this page).</p>
                    )}
                    <hr />
                    {/* Section to link to a new campaign */}
                    <h5>Link to a Campaign:</h5>
                    {userCampaigns.length > 0 ? (
                        <div className="input-group">
                            <select
                                className="form-select"
                                value={selectedCampaignToLink}
                                onChange={(e) => setSelectedCampaignToLink(e.target.value)}
                                disabled={isLinking}
                            >
                                <option value="">Select a campaign...</option>
                                {userCampaigns.map(camp => (
                                    // Filter out campaigns the character might already be in, if associatedCampaigns was populated
                                    // For now, this shows all user campaigns.
                                    <option key={camp.id} value={camp.id}>{camp.title}</option>
                                ))}
                            </select>
                            <button
                                className="btn btn-outline-success"
                                type="button"
                                onClick={handleLinkCampaign}
                                disabled={!selectedCampaignToLink || isLinking}
                            >
                                {isLinking ? 'Linking...' : 'Link to Campaign'}
                            </button>
                        </div>
                    ) : (
                        <p className="text-muted">You don't have any campaigns to link this character to.</p>
                    )}
                    {linkError && <p className="text-danger mt-2">{linkError}</p>}
                </div>
            </div>

            <Link to="/characters" className="btn btn-secondary mt-3">
                Back to Character List
            </Link>
        </div>
    );
};

export default CharacterDetailPage;
