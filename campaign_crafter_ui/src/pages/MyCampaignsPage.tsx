// campaign_crafter_ui/src/pages/MyCampaignsPage.tsx
import React, { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import * as campaignService from '../services/campaignService';
import { Campaign } from '../types/campaignTypes';
import CampaignCard from '../components/CampaignCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import AlertMessage from '../components/common/AlertMessage';
import Button from '../components/common/Button';
import CreateCampaignModal from '../components/modals/CreateCampaignModal'; // For creating new campaign
import ConfirmationModal from '../components/modals/ConfirmationModal'; // If delete functionality is added
import './MyCampaignsPage.css'; // Create this CSS file

const MyCampaignsPage: React.FC = () => {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    // const [successMessage, setSuccessMessage] = useState<string | null>(null); // If delete/update messages are needed

    const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
    const navigate = useNavigate();

    // State for delete confirmation modal (if implementing delete)
    const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
    const [campaignToDelete, setCampaignToDelete] = useState<{ id: number; title: string } | null>(null);
    const [isDeleting, setIsDeleting] = useState<boolean>(false); // Keep this for later

    const fetchCampaigns = useCallback(async () => {
        setLoading(true);
        try {
            const userCampaigns = await campaignService.getAllCampaigns();
            setCampaigns(userCampaigns);
            setError(null);
        } catch (err: any) {
            console.error("Failed to fetch campaigns:", err);
            setError(err.response?.data?.detail || 'Failed to load campaigns. Please try again later.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchCampaigns();
    }, [fetchCampaigns]);

    const handleCampaignCreated = (createdCampaign: Campaign) => {
        navigate(`/campaign/${createdCampaign.id}`);
        // Or fetchCampaigns(); to refresh the list
    };

    // Delete functionality (optional, can be added later)

    const openDeleteModal = (campaignId: number, campaignTitle: string) => {
        setCampaignToDelete({ id: campaignId, title: campaignTitle });
        setShowDeleteModal(true);
        // setSuccessMessage(null); // Uncomment if success messages are used
        setError(null); // Clear previous errors
    };

    const closeDeleteModal = () => {
        setShowDeleteModal(false);
        setCampaignToDelete(null);
    };

    const handleDeleteCampaign = async () => {
        if (!campaignToDelete) return;

        setIsDeleting(true);
        setError(null); // Clear previous errors
        // setSuccessMessage(null); // Clear previous success messages if you use them

        try {
            await campaignService.deleteCampaign(campaignToDelete.id);
            // setSuccessMessage(`Campaign "${campaignToDelete.title}" deleted successfully.`); // Optional success message
            // Option 1: Refetch campaigns list
            fetchCampaigns();
            // Option 2: Filter out the deleted campaign from local state (faster UI update)
            // setCampaigns(prevCampaigns => prevCampaigns.filter(c => c.id !== campaignToDelete.id));
        } catch (err: any) {
            console.error("Failed to delete campaign:", err);
            setError(err.response?.data?.detail || `Failed to delete campaign "${campaignToDelete.title}". Please try again.`);
        } finally {
            setIsDeleting(false);
            closeDeleteModal(); // Close modal regardless of success or failure
        }
    };


    if (loading && campaigns.length === 0) {
        return (
            <div className="container mt-3 d-flex justify-content-center align-items-center" style={{ minHeight: '80vh' }}>
                <LoadingSpinner />
            </div>
        );
    }

    return (
        <div className="container mt-3 my-campaigns-page">
            <div className="page-header mb-4">
                <h1>My Campaigns</h1>
                <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
                    + Create New Campaign
                </Button>
            </div>

            {error && <AlertMessage type="error" message={error} onClose={() => setError(null)} />}
            {/* {successMessage && <AlertMessage type="success" message={successMessage} onClose={() => setSuccessMessage(null)} />} */}

            {loading && campaigns.length > 0 && (
                <div className="text-center my-3">
                    <LoadingSpinner />
                </div>
            )}

            {!loading && campaigns.length === 0 && !error && (
                <div className="text-center card p-4">
                    <h4>No Campaigns Yet!</h4>
                    <p>You haven't created any campaigns. Click the button above to get started!</p>
                </div>
            )}

            {campaigns.length > 0 && (
                <div className="campaign-grid"> {/* Similar to character-grid or a new style */}
                    {campaigns.map((campaign) => (
                        <CampaignCard
                            key={campaign.id}
                            campaign={campaign}
                            // Add onDelete prop to CampaignCard if delete functionality is desired directly on card
                            onDelete={openDeleteModal}
                        />
                    ))}
                </div>
            )}

            {campaignToDelete && (
                <ConfirmationModal
                    isOpen={showDeleteModal}
                    title="Confirm Deletion"
                    message={`Are you sure you want to delete the campaign "${campaignToDelete.title}"? This action cannot be undone.`}
                    onConfirm={handleDeleteCampaign}
                    onCancel={closeDeleteModal}
                    confirmButtonText="Delete"
                    cancelButtonText="Cancel"
                    isConfirming={isDeleting}
                    confirmButtonVariant="danger"
                />
            )}

            <CreateCampaignModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onCampaignCreated={handleCampaignCreated}
            />
        </div>
    );
};

export default MyCampaignsPage;
