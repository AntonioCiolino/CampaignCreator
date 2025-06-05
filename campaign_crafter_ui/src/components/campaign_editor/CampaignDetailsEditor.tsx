import React from 'react';
import { TextField, Button, Grid, Typography, Card, CardContent, Box } from '@mui/material';

interface CampaignDetailsEditorProps {
  editableTitle: string;
  setEditableTitle: (title: string) => void;
  initialPrompt: string;
  setInitialPrompt: (prompt: string) => void;
  campaignBadgeImage: string;
  setCampaignBadgeImage: (image: string) => void;
  handleSaveCampaignDetails: () => void;
  // TODO: Add other necessary props here
}

const CampaignDetailsEditor: React.FC<CampaignDetailsEditorProps> = ({
  editableTitle,
  setEditableTitle,
  initialPrompt,
  setInitialPrompt,
  campaignBadgeImage,
  setCampaignBadgeImage,
  handleSaveCampaignDetails,
}) => {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Campaign Details
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              label="Campaign Title"
              value={editableTitle}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setEditableTitle(e.target.value)}
              fullWidth
              variant="outlined"
              sx={{ mb: 2 }}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="Initial Prompt"
              value={initialPrompt}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setInitialPrompt(e.target.value)}
              fullWidth
              multiline
              rows={4}
              variant="outlined"
              sx={{ mb: 2 }}
            />
          </Grid>
          <Grid item xs={12}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSaveCampaignDetails}
            >
              Save Details
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default CampaignDetailsEditor;
