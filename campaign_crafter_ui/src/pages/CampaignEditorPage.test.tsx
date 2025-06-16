import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useParams } from 'react-router-dom';
import CampaignEditorPage from './CampaignEditorPage';
import * as campaignService from '../services/campaignService';
import * as llmService from '../services/llmService';
import { Campaign, CampaignSection, TOCEntry } from '../services/campaignService';
import { LLMModel } from '../services/llmService';

// Mock external services and hooks
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: jest.fn(),
}));

jest.mock('../services/campaignService');
jest.mock('../services/llmService');

// Mock ReactMarkdown
jest.mock('react-markdown', () => (props: { children: React.ReactNode }) => <div data-testid="react-markdown">{props.children}</div>);

// Mock common components that might be complex or irrelevant to these specific tests
jest.mock('../components/common/LoadingSpinner', () => () => <div data-testid="loading-spinner">Loading...</div>);
jest.mock('../components/modals/LLMSelectionDialog', () => () => null);
jest.mock('../components/modals/ImageGenerationModal/ImageGenerationModal', () => () => null);
jest.mock('../components/modals/SuggestedTitlesModal', () => () => null);
jest.mock('../components/common/MoodBoardPanel', () => () => null);
jest.mock('../components/campaign_editor/CampaignDetailsEditor', () => () => <div data-testid="campaign-details-editor">Details Editor</div>);
jest.mock('../components/campaign_editor/CampaignLLMSettings', () => () => <div data-testid="llm-settings">LLM Settings</div>);
jest.mock('../components/campaign_editor/CampaignSectionEditor', () => () => <div data-testid="section-editor">Section Editor</div>);
jest.mock('../components/campaign_editor/TOCEditor', () => () => <div data-testid="toc-editor">TOC Editor</div>);
jest.mock('../components/campaign_editor/CampaignThemeEditor', () => () => <div data-testid="theme-editor">Theme Editor</div>);


const mockUseParams = useParams as jest.Mock;
const mockGetCampaignById = campaignService.getCampaignById as jest.Mock;
const mockGetCampaignSections = campaignService.getCampaignSections as jest.Mock;
const mockUpdateCampaign = campaignService.updateCampaign as jest.Mock;
const mockGetAvailableLLMs = llmService.getAvailableLLMs as jest.Mock;

const mockCampaignId = 'test-campaign-123';

const mockLLMs: LLMModel[] = [
  { id: 'llm1', name: 'LLM One', capabilities: ['chat'] },
  { id: 'llm2', name: 'LLM Two', capabilities: ['chat'] },
];

const initialCampaignConcept = 'This is the initial campaign concept.';
const mockCampaign: Campaign = {
  id: mockCampaignId,
  title: 'Test Campaign Title',
  concept: initialCampaignConcept,
  initial_user_prompt: 'Initial prompt',
  current_status: 'draft',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  user_id: 'user1',
  selected_llm_id: 'llm1',
  temperature: 0.7,
  display_toc: [],
  sections_order: [],
  thematic_image_url: null,
  thematic_image_prompt: null,
  badge_image_url: null,
  mood_board_image_urls: [],
  theme_primary_color: null,
  theme_secondary_color: null,
  theme_background_color: null,
  theme_text_color: null,
  theme_font_family: null,
  theme_background_image_url: null,
  theme_background_image_opacity: null,
  homebrewery_toc: null,
  is_public: false,
  view_count: 0,
  like_count: 0,
};

const mockSections: CampaignSection[] = [];

// Helper to get the specific "Edit" button for the concept
const getConceptEditButton = () => {
    // The button has "Edit" text and a tooltip "Edit Campaign Concept"
    // It's also identifiable by being within the 'page-level-concept' section
    const allEditButtons = screen.getAllByRole('button', { name: /Edit/i });
    // Find the button that is within the campaign concept section
    return allEditButtons.find(btn => btn.closest('.page-level-concept') && btn.textContent === "Edit");
};


describe('CampaignEditorPage - Campaign Concept Editing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseParams.mockReturnValue({ campaignId: mockCampaignId });
    mockGetCampaignById.mockResolvedValue({...mockCampaign, concept: initialCampaignConcept}); // Ensure fresh concept
    mockGetCampaignSections.mockResolvedValue(mockSections);
    mockGetAvailableLLMs.mockResolvedValue(mockLLMs);
    
    // Default mock for updateCampaign
    mockUpdateCampaign.mockImplementation(async (id, payload) => {
      const currentCampaign = await mockGetCampaignById(id); // Get current state
      return { ...currentCampaign, ...payload };
    });
  });

  const renderPage = async () => {
    render(<CampaignEditorPage />);
    await waitFor(() => expect(mockGetCampaignById).toHaveBeenCalledWith(mockCampaignId));
    await waitFor(() => expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument(), { timeout: 2000 });
  };

  test('editor is hidden by default and concept is displayed', async () => {
    await renderPage();
    expect(screen.getByTestId('react-markdown')).toHaveTextContent(initialCampaignConcept);
    expect(screen.queryByLabelText(/Campaign Concept/i, { selector: 'textarea' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Save Concept/i })).not.toBeInTheDocument();
    // Check for specific cancel button if possible, or any cancel button for now
    const cancelButtons = screen.queryAllByRole('button', { name: /Cancel/i });
    const conceptCancelButton = cancelButtons.find(btn => btn.closest('.edit-concept-section'));
    expect(conceptCancelButton).not.toBeInTheDocument();
  });

  test('Edit Concept button is visible when a concept exists', async () => {
    await renderPage();
    const editButton = getConceptEditButton();
    expect(editButton).toBeInTheDocument();
  });

  test('clicking Edit Concept button shows the editor and initializes concept', async () => {
    await renderPage();
    const editButton = getConceptEditButton();
    expect(editButton).toBeInTheDocument();
    fireEvent.click(editButton!);

    await waitFor(() => {
      expect(screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' })).toBeInTheDocument();
    });
    const textField = screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' });
    expect(textField).toHaveValue(initialCampaignConcept);
    expect(screen.getByRole('button', { name: /Save Concept/i })).toBeInTheDocument();
    
    const cancelButtons = screen.getAllByRole('button', { name: /Cancel/i });
    const conceptCancelButton = cancelButtons.find(btn => btn.closest('.edit-concept-section'));
    expect(conceptCancelButton).toBeInTheDocument();
  });

  test('editing concept updates TextField value', async () => {
    await renderPage();
    const editButton = getConceptEditButton();
    fireEvent.click(editButton!);

    await waitFor(() => {
      expect(screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' })).toBeInTheDocument();
    });
    const textField = screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' });
    const newConceptText = 'This is an updated campaign concept.';
    fireEvent.change(textField, { target: { value: newConceptText } });
    expect(textField).toHaveValue(newConceptText);
  });

  test('saving new concept calls updateCampaign, updates UI, shows success, and hides editor', async () => {
    await renderPage();
    const editButton = getConceptEditButton();
    fireEvent.click(editButton!);
    
    await waitFor(() => {
      expect(screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' })).toBeInTheDocument();
    });

    const textField = screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' });
    const updatedConcept = 'Successfully updated concept.';
    fireEvent.change(textField, { target: { value: updatedConcept } });

    mockUpdateCampaign.mockResolvedValueOnce({ ...mockCampaign, concept: updatedConcept });

    const saveButton = screen.getByRole('button', { name: /Save Concept/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateCampaign).toHaveBeenCalledWith(mockCampaignId, { concept: updatedConcept });
    });

    expect(await screen.findByText(/Campaign concept updated successfully!/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByLabelText(/Campaign Concept/i, { selector: 'textarea' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Save Concept/i })).not.toBeInTheDocument();
    });

    expect(screen.getByTestId('react-markdown')).toHaveTextContent(updatedConcept);
  });

  test('saving concept failure shows error message and keeps editor visible', async () => {
    await renderPage();
    const editButton = getConceptEditButton();
    fireEvent.click(editButton!);

    await waitFor(() => {
        expect(screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' })).toBeInTheDocument();
    });
    const textField = screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' });
    const conceptWithError = 'Concept causing error.';
    fireEvent.change(textField, { target: { value: conceptWithError } });

    mockUpdateCampaign.mockRejectedValueOnce(new Error('Failed to save'));

    const saveButton = screen.getByRole('button', { name: /Save Concept/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateCampaign).toHaveBeenCalledWith(mockCampaignId, { concept: conceptWithError });
    });

    expect(await screen.findByText(/Failed to save concept. Please try again./i)).toBeInTheDocument();

    expect(screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Save Concept/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' })).toHaveValue(conceptWithError);
  });

  test('canceling edit hides editor and does not call updateCampaign', async () => {
    await renderPage();
    const editButton = getConceptEditButton();
    fireEvent.click(editButton!);

    await waitFor(() => {
        expect(screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' })).toBeInTheDocument();
    });
    const textField = screen.getByLabelText(/Campaign Concept/i, { selector: 'textarea' });
    const tempConcept = 'Temporary concept change.';
    fireEvent.change(textField, { target: { value: tempConcept } });

    const conceptCancelButton = screen.getAllByRole('button', { name: /Cancel/i }).find(btn => btn.closest('.edit-concept-section'));
    expect(conceptCancelButton).toBeInTheDocument();
    if (conceptCancelButton) fireEvent.click(conceptCancelButton);


    await waitFor(() => {
      expect(screen.queryByLabelText(/Campaign Concept/i, { selector: 'textarea' })).not.toBeInTheDocument();
    });

    expect(mockUpdateCampaign).not.toHaveBeenCalled();
    expect(screen.getByTestId('react-markdown')).toHaveTextContent(initialCampaignConcept);
  });

  test('does not show Edit Concept button if campaign concept is empty or null', async () => {
    // Override mock for this specific test
    mockGetCampaignById.mockResolvedValueOnce({ ...mockCampaign, concept: null });
    await renderPage(); // Render with the campaign having null concept

    // The "Campaign Concept" h2 itself should be visible
    expect(screen.getByRole('heading', { name: /Campaign Concept/i, level: 2})).toBeInTheDocument();

    // The specific "Edit" button for concept should not be present
    const editButton = getConceptEditButton(); // This helper looks for the button within the concept section
    expect(editButton).not.toBeInTheDocument();

    // Also, the ReactMarkdown display for the concept should not render the initialCampaignConcept
    expect(screen.queryByTestId('react-markdown')).not.toHaveTextContent(initialCampaignConcept);
  });

});
