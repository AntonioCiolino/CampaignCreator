import React, { useState, useEffect } from 'react';
import {
  Modal,
  Box,
  Typography,
  TextField,
  Button as MuiButton, // Alias to avoid conflict with our common Button
  List,
  ListItem,
  ListItemText,
  Paper,
} from '@mui/material';
import { Feature } from '../../types/featureTypes';
import { Character as FrontendCharacter } from '../types/characterTypes'; // Corrected path

interface SnippetContextModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (collectedContext: Record<string, any>) => void;
  feature: Feature | null;
  campaignCharacters: FrontendCharacter[];
  selectedText: string;
}

const style = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 600,
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
  maxHeight: '90vh',
  overflowY: 'auto',
};

const SnippetContextModal: React.FC<SnippetContextModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  feature,
  campaignCharacters,
  selectedText,
}) => {
  const [formData, setFormData] = useState<Record<string, any>>({});

  useEffect(() => {
    // Initialize formData when feature changes or modal opens
    if (feature && isOpen) {
      const initialFormData: Record<string, any> = {};
      feature.required_context?.forEach(key => {
        if (key !== 'selected_text' && key !== 'campaign_characters') {
          initialFormData[key] = ''; // Initialize other context fields as empty
        }
      });
      setFormData(initialFormData);
    }
  }, [feature, isOpen]);

  if (!feature) {
    return null; // Don't render if no feature is provided
  }

  const handleInputChange = (key: string, value: string) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = () => {
    const fullContext: Record<string, any> = { ...formData };
    if (feature.required_context?.includes('campaign_characters')) {
      fullContext['campaign_characters'] = campaignCharacters.map(char => char.name).join(', ');
      if (!fullContext['campaign_characters']) { // Handle case of no characters
        fullContext['campaign_characters'] = "No specific campaign characters provided.";
      }
    }
    onSubmit(fullContext);
    onClose(); // Close modal after submit
  };

  const otherContextKeys = feature.required_context?.filter(
    key => key !== 'selected_text' && key !== 'campaign_characters'
  ) || [];

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      aria-labelledby="snippet-context-modal-title"
      aria-describedby="snippet-context-modal-description"
    >
      <Box sx={style}>
        <Typography id="snippet-context-modal-title" variant="h6" component="h2">
          Context for "{feature.name}"
        </Typography>

        <Paper variant="outlined" sx={{ p: 2, mt: 2, mb: 2, maxHeight: 150, overflowY: 'auto' }}>
          <Typography variant="subtitle2" gutterBottom>
            Selected Text (for reference):
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
            {selectedText}
          </Typography>
        </Paper>

        {feature.required_context?.includes('campaign_characters') && (
          <Box mt={2} mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Campaign Characters to be considered:
            </Typography>
            {campaignCharacters.length > 0 ? (
              <List dense disablePadding>
                {campaignCharacters.map(char => (
                  <ListItem key={char.id} disableGutters sx={{pl: 1}}>
                    <ListItemText primary={char.name} />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No characters currently linked to this campaign will be specifically listed in the prompt.
              </Typography>
            )}
          </Box>
        )}

        {otherContextKeys.map(key => (
          <TextField
            key={key}
            fullWidth
            label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} // Format key for display
            value={formData[key] || ''}
            onChange={(e) => handleInputChange(key, e.target.value)}
            margin="normal"
            variant="outlined"
          />
        ))}

        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <MuiButton onClick={onClose} sx={{ mr: 1 }}>
            Cancel
          </MuiButton>
          <MuiButton onClick={handleSubmit} variant="contained">
            Generate
          </MuiButton>
        </Box>
      </Box>
    </Modal>
  );
};

export default SnippetContextModal;
