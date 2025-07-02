// campaign_crafter_ui/src/components/modals/CreateCampaignModal.tsx
import React, { useState, FormEvent, useEffect } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import Input from '../common/Input';
import Checkbox from '../common/Checkbox';
import { Campaign, CampaignCreatePayload } from '../../types/campaignTypes';
import * as campaignService from '../../services/campaignService';
// Potentially add specific CSS if needed: import './CreateCampaignModal.css';

interface CreateCampaignModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCampaignCreated: (campaign: Campaign) => void;
}

const CreateCampaignModal: React.FC<CreateCampaignModalProps> = ({ isOpen, onClose, onCampaignCreated }) => {
  const [title, setTitle] = useState<string>('');
  const [initialUserPrompt, setInitialUserPrompt] = useState<string>('');
  const [skipConceptGeneration, setSkipConceptGeneration] = useState<boolean>(false);
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when modal opens or closes
  useEffect(() => {
    if (isOpen) {
      setTitle('');
      setInitialUserPrompt('');
      setSkipConceptGeneration(false);
      setError(null);
      setIsCreating(false);
    }
  }, [isOpen]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!title.trim()) {
      setError('Campaign title is required.');
      return;
    }
    setError(null);
    setIsCreating(true);

    try {
      const newCampaignData: CampaignCreatePayload = {
        title: title,
        initial_user_prompt: skipConceptGeneration ? undefined : initialUserPrompt,
        skip_concept_generation: skipConceptGeneration,
        // model_id_with_prefix_for_concept can be added here if an LLMSelector is included
      };
      const createdCampaign = await campaignService.createCampaign(newCampaignData);
      onCampaignCreated(createdCampaign); // Pass created campaign to parent
      onClose(); // Close modal on success
    } catch (err) {
      console.error('Failed to create campaign:', err);
      const errorMessage = (err instanceof Error && (err as any).response?.data?.detail)
        ? (err as any).response.data.detail
        : 'Failed to create campaign. Please try again.';
      setError(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Campaign">
      <form onSubmit={handleSubmit} className="create-campaign-form-modal">
        <Input
          id="newCampaignTitleModal"
          name="newCampaignTitleModal"
          label="Campaign Title:"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter the title for your new campaign"
          required
          disabled={isCreating}
        />
        <div className="form-group">
          <label htmlFor="newCampaignPromptModal" className="form-label">
            Initial Prompt (Optional if skipping AI concept):
          </label>
          <textarea
            id="newCampaignPromptModal"
            name="newCampaignPromptModal"
            value={initialUserPrompt}
            onChange={(e) => setInitialUserPrompt(e.target.value)}
            rows={4}
            placeholder="Describe the core idea or starting point for your campaign..."
            className="form-textarea" // Ensure this class is styled globally or locally
            disabled={skipConceptGeneration || isCreating}
          />
        </div>
        <Checkbox
          id="skipConceptGenerationModal"
          label="Skip initial AI concept generation"
          checked={skipConceptGeneration}
          onChange={(e) => setSkipConceptGeneration(e.target.checked)}
          className="skip-concept-checkbox" // Ensure this class is styled globally or locally
          disabled={isCreating}
        />
        {/*
          TODO: Add LLMSelector here if users should choose a model for initial concept generation,
          and ensure it's disabled if skipConceptGeneration is true or isCreating is true.
        */}
        {error && <p className="error-message create-error">{error}</p>}
        <div className="modal-actions" style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
          <Button type="button" variant="secondary" onClick={onClose} disabled={isCreating}>
            Cancel
          </Button>
          <Button type="submit" variant="success" disabled={isCreating} className="create-button">
            {isCreating ? 'Creating...' : 'Create Campaign'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default CreateCampaignModal;
