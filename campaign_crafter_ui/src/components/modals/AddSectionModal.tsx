import React, { useState, useEffect } from 'react';
import { Modal, Box, Typography, TextField, Button, Paper } from '@mui/material';

interface AddSectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddSection: (title?: string, prompt?: string) => void;
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

  // Reset fields when modal opens or selectedLLMId changes (if needed)
  useEffect(() => {
    if (isOpen) {
      setTitle('');
      setPrompt('');
    }
  }, [isOpen]);

  const handleTitleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTitle(event.target.value);
  };

  const handlePromptChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPrompt(event.target.value);
  };

  const handleAdd = () => {
    onAddSection(title, prompt);
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
        />
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={handleCancel} sx={{ mr: 1 }}>
            Cancel
          </Button>
          <Button onClick={handleAdd} variant="contained" disabled={!selectedLLMId && (!title && !prompt)}>
            Add Section
          </Button>
        </Box>
        {!selectedLLMId && (!title && !prompt) && (
          <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
            A Large Language Model must be selected to automatically generate content, or a title/prompt must be provided.
          </Typography>
        )}
      </Box>
    </Modal>
  );
};

export default AddSectionModal;
