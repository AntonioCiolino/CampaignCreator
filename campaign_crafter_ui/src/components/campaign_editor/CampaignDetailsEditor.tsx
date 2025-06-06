import React, { useState } from 'react'; // Import useState
import { TextField, Grid, Typography, Card, CardContent, Box, IconButton } from '@mui/material'; // Added IconButton
import Button from '../common/Button'; // Import common Button
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined'; // Import icon
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'; // Import ExpandMoreIcon
import ChevronRightIcon from '@mui/icons-material/ChevronRight'; // Import ChevronRightIcon
import VisibilityIcon from '@mui/icons-material/Visibility'; // Import VisibilityIcon
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'; // Import VisibilityOffIcon
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate'; // Import AddPhotoAlternateIcon
import EditIcon from '@mui/icons-material/Edit'; // Import EditIcon
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'; // Import DeleteOutlineIcon

interface CampaignDetailsEditorProps {
  editableTitle: string;
  setEditableTitle: (title: string) => void;
  initialPrompt: string;
  setInitialPrompt: (prompt: string) => void;
  campaignBadgeImage: string;
  setCampaignBadgeImage: (image: string) => void;
  handleSaveCampaignDetails: () => void;
  onSuggestTitles: () => void; // New prop
  isGeneratingTitles: boolean; // New prop
  titlesError: string | null; // New prop
  selectedLLMId: string; // New prop
  originalTitle: string; // New prop
  originalInitialPrompt: string; // New prop
  originalBadgeImageUrl?: string; // New prop
  onOpenBadgeImageModal: () => void; // New prop
  onEditBadgeImageUrl: () => void; // New prop
  onRemoveBadgeImage: () => void; // New prop
  badgeUpdateLoading: boolean; // New prop
  badgeUpdateError: string | null; // New prop
}

const CampaignDetailsEditor: React.FC<CampaignDetailsEditorProps> = ({
  editableTitle,
  setEditableTitle,
  initialPrompt,
  setInitialPrompt,
  campaignBadgeImage,
  setCampaignBadgeImage,
  handleSaveCampaignDetails,
  onSuggestTitles, // New prop
  isGeneratingTitles, // New prop
  titlesError, // New prop
  selectedLLMId, // New prop
  originalTitle, // New prop
  originalInitialPrompt, // New prop
  // originalBadgeImageUrl, // New prop - currently unused for hasUnsavedChanges
  onOpenBadgeImageModal, // New prop
  onEditBadgeImageUrl, // New prop
  onRemoveBadgeImage, // New prop
  badgeUpdateLoading, // New prop
  badgeUpdateError, // New prop
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false); // Add state for collapse
  const [isInitialPromptVisible, setIsInitialPromptVisible] = useState(false); // State for prompt visibility
  const [isBadgeActionsVisible, setIsBadgeActionsVisible] = useState(false); // State for badge actions visibility

  const hasUnsavedChanges = editableTitle !== originalTitle || initialPrompt !== originalInitialPrompt;
  // Note: campaignBadgeImage changes are not currently part of hasUnsavedChanges logic for the main save button.

  return (
    <Card sx={{ mb: 3 }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          p: 2,
          borderBottom: !isCollapsed ? '1px solid rgba(0, 0, 0, 0.12)' : 'none',
        }}
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <Typography variant="h6">Campaign Details</Typography>
        {isCollapsed ? <ChevronRightIcon /> : <ExpandMoreIcon />}
      </Box>
      {!isCollapsed && (
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                label="Campaign Title"
              value={editableTitle}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setEditableTitle(e.target.value)}
              fullWidth
              variant="outlined"
              sx={{ mb: 1 }} // Adjusted margin for the button
            />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
              <Button
                onClick={onSuggestTitles}
                disabled={isGeneratingTitles || !selectedLLMId}
                className="action-button"
                icon={<LightbulbOutlinedIcon />}
                tooltip="Suggest alternative titles for your campaign based on the concept"
              >
                {isGeneratingTitles ? 'Generating...' : 'Suggest Titles'}
              </Button>
            </Box>
            {titlesError && <Typography color="error" sx={{ mt: 1 }}>{titlesError}</Typography>}
          </Grid>
          <Grid item xs={12} sx={{ mb: 2 }}> {/* Added sx mb here to manage spacing */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="subtitle1">Initial Prompt</Typography>
              <IconButton onClick={() => setIsInitialPromptVisible(!isInitialPromptVisible)} size="small" aria-label={isInitialPromptVisible ? "Hide initial prompt" : "Show initial prompt"}>
                {isInitialPromptVisible ? <VisibilityOffIcon /> : <VisibilityIcon />}
              </IconButton>
            </Box>
            {isInitialPromptVisible && (
              <TextField
                // label="Initial Prompt Text" // Label removed as Typography is used above
                value={initialPrompt}
                onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setInitialPrompt(e.target.value)}
                fullWidth
                multiline
                rows={4}
                variant="outlined"
                placeholder="Enter the initial prompt for the campaign..."
              />
            )}
          </Grid>
          {/* Campaign Badge Section */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="subtitle1">Campaign Badge</Typography>
              <IconButton
                onClick={() => setIsBadgeActionsVisible(!isBadgeActionsVisible)}
                size="small"
                aria-label={isBadgeActionsVisible ? "Hide badge actions" : "Show badge actions"}
              >
                {isBadgeActionsVisible ? <VisibilityOffIcon /> : <VisibilityIcon />}
              </IconButton>
            </Box>
            {isBadgeActionsVisible && (
              <Box className="campaign-badge-area-internal" sx={{ mt: 1 }}>
                {campaignBadgeImage && (
                  <Box sx={{ mt: 1, mb: 1, textAlign: 'center' }}>
                    <Typography variant="caption" display="block" gutterBottom>
                      Current Badge:
                    </Typography>
                    <img
                      src={campaignBadgeImage}
                      alt="Campaign Badge"
                      style={{ maxWidth: '100px', maxHeight: '100px', border: '1px solid #ccc' }}
                    />
                  </Box>
                )}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: campaignBadgeImage ? 1 : 0 }}> {/* Adjusted layout for buttons */}
                  <Button
                    onClick={onOpenBadgeImageModal}
                    disabled={badgeUpdateLoading}
                    className="action-button" // Ensure this class is styled appropriately or use MUI Button props for full styling
                    icon={<AddPhotoAlternateIcon />}
                    tooltip="Generate a new badge image for your campaign"
                  >
                    {badgeUpdateLoading ? "Processing..." : "Generate New Badge"}
                  </Button>
                  <Button
                    onClick={onEditBadgeImageUrl}
                    disabled={badgeUpdateLoading}
                    className="action-button secondary-action-button" // Ensure this class is styled appropriately
                    icon={<EditIcon />}
                    tooltip="Manually set or change the URL for the campaign badge"
                  >
                    {badgeUpdateLoading ? "Processing..." : "Edit Badge URL"}
                  </Button>
                  {campaignBadgeImage && (
                    <Button
                      onClick={onRemoveBadgeImage}
                      disabled={badgeUpdateLoading || !campaignBadgeImage}
                      className="action-button remove-button" // Ensure this class is styled appropriately
                      icon={<DeleteOutlineIcon />}
                      tooltip="Remove the current campaign badge image"
                    >
                      {badgeUpdateLoading ? "Removing..." : "Remove Badge"}
                    </Button>
                  )}
                </Box>
                {badgeUpdateError && <Typography color="error" sx={{ mt: 1 }}>{badgeUpdateError}</Typography>}
              </Box>
            )}
          </Grid>
          <Grid item xs={12}>
            {/* The Save Details button was here, assuming it might be part of a larger form structure or moved elsewhere based on overall UI design.
                If it's meant to be part of this component, it should be retained.
                For this specific task, we are only focusing on the title suggestion button.
                The original instructions didn't specify removing or moving the "Save Details" button,
                so I am keeping it as it was.
            */}
            <Button
              variant="primary" // Changed from "contained"
              onClick={handleSaveCampaignDetails}
              disabled={!hasUnsavedChanges} // Disable button if no unsaved changes
              // sx prop might not be supported by common/Button, remove if it causes issues
              // For now, assuming sx is fine or will be ignored if not supported by common/Button
              // color="primary" is removed as it's usually part of MUI Button, not a common custom prop combined with variant="primary"
              sx={{ mt: 2 }} // Added margin top for spacing from the prompt field
            >
              Save Details
            </Button>
          </Grid>
        </Grid>
      </CardContent>
      )}
    </Card>
  );
};

export default CampaignDetailsEditor;
