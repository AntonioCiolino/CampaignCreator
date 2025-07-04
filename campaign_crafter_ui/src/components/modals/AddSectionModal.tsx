import React, { useState, useEffect } from 'react';
import { Modal, Box, Typography, TextField, Button, Paper, FormControlLabel, Checkbox } from '@mui/material';

interface AddSectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddSection: (data: { title?: string; prompt?: string; bypassLLM?: boolean }) => void;
  selectedLLMId: string | null;
}

const style = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 400,
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
};

const AddSectionModal: React.FC<AddSectionModalProps> = ({ isOpen, onClose, onAddSection, selectedLLMId }) => {
  const [title, setTitle] = useState<string>('');
  const [prompt, setPrompt] = useState<string>('');
  const [bypassLLM, setBypassLLM] = useState<boolean>(false);

  // Reset fields when modal opens or selectedLLMId changes (if needed)
  useEffect(() => {
    if (isOpen) {
      setTitle('');
      setPrompt('');
      setBypassLLM(false);
    }
  }, [isOpen]);

  const handleTitleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTitle(event.target.value);
  };

  const handlePromptChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPrompt(event.target.value);
  };

  const handleAdd = () => {
    onAddSection({ title, prompt, bypassLLM });
    onClose(); // Close modal after adding
  };

  const handleCancel = () => {
    onClose();
  };

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      aria-labelledby="add-section-modal-title"
      aria-describedby="add-section-modal-description"
    >
      <Box sx={style} component={Paper}>
        <Typography id="add-section-modal-title" variant="h6" component="h2">
          Add New Section
        </Typography>
        <TextField
          margin="normal"
          fullWidth
          label="Section Title (Optional)"
          value={title}
          onChange={handleTitleChange}
          variant="outlined"
        />
        <TextField
          margin="normal"
          fullWidth
          label="Section Prompt (Optional)"
          value={prompt}
          onChange={handlePromptChange}
          multiline
          rows={4}
          variant="outlined"
          disabled={bypassLLM} // Disable if bypassing LLM
        />
        <FormControlLabel
          control={<Checkbox checked={bypassLLM} onChange={(e) => setBypassLLM(e.target.checked)} />}
          label="Create blank section (skip AI content generation)"
          sx={{ mt: 1, mb: 1 }}
        />
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={handleCancel} sx={{ mr: 1 }}>
            Cancel
          </Button>
          <Button
            onClick={handleAdd}
            variant="contained"
            // Logic for disabled:
            // If bypassing LLM, only title is relevant (though optional).
            // If not bypassing LLM, then either selectedLLMId must be present OR (title or prompt must be present).
            // Simplified: disable if not bypassing LLM AND no LLM is selected AND both title/prompt are empty.
            disabled={!bypassLLM && !selectedLLMId && !title.trim() && !prompt.trim()}
          >
            Add Section
          </Button>
        </Box>
        {!bypassLLM && !selectedLLMId && !title.trim() && !prompt.trim() && (
          <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
            To generate AI content, select an LLM (in Campaign Settings) or provide a Title/Prompt. Otherwise, check "Create blank section".
          </Typography>
        )}
      </Box>
    </Modal>
  );
};

export default AddSectionModal;
