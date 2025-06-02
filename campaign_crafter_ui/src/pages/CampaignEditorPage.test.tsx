import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import CampaignEditorPage from './CampaignEditorPage';
import * as campaignService from '../services/campaignService';
import * as llmService from '../services/llmService'; // For getAvailableLLMs

// Mock services
jest.mock('../services/campaignService');
jest.mock('../services/llmService');

// Mock ImageGenerationModal
jest.mock('../components/modals/ImageGenerationModal/ImageGenerationModal', () => ({
  __esModule: true,
  default: jest.fn(({ isOpen, onClose, onImageSuccessfullyGenerated }) => {
    if (!isOpen) return null;
    return (
      <div data-testid="mock-image-gen-modal">
        Mock Image Generation Modal
        <button onClick={() => onImageSuccessfullyGenerated?.('http://example.com/mock-generated-badge.png')}>
          Simulate Generate Badge
        </button>
        <button onClick={onClose}>Close Mock Modal</button>
      </div>
    );
  }),
}));

const mockGetCampaignById = campaignService.getCampaignById as jest.Mock;
const mockGetCampaignSections = campaignService.getCampaignSections as jest.Mock;
const mockUpdateCampaign = campaignService.updateCampaign as jest.Mock;
const mockGetAvailableLLMs = llmService.getAvailableLLMs as jest.Mock;

// Mock window.prompt and window.confirm
const mockPrompt = jest.fn(); // Re-adding for 'Edit URL'
const mockConfirm = jest.fn();
global.prompt = mockPrompt;
global.confirm = mockConfirm;

const mockCampaignWithBadge = {
  id: '1',
  title: 'Test Campaign with Badge',
  initial_user_prompt: 'Initial prompt for badge test',
  concept: 'A cool concept.',
  toc: '1. Chapter 1',
  homebrewery_export: null,
  badge_image_url: 'http://example.com/badge.png',
  owner_id: 1,
  sections: [],
};

const mockCampaignWithoutBadge = {
  id: '2',
  title: 'Test Campaign No Badge',
  initial_user_prompt: 'Initial prompt for no badge test',
  concept: 'Another concept.',
  toc: '1. Intro',
  homebrewery_export: null,
  badge_image_url: null,
  owner_id: 1,
  sections: [],
};

const mockLLMs = [
  { id: 'openai/gpt-3.5-turbo', name: 'GPT-3.5 Turbo', capabilities: ['chat'] },
  { id: 'openai/gpt-4', name: 'GPT-4', capabilities: ['chat'] },
];

const mockSections: campaignService.CampaignSection[] = [
  { id: 1, campaign_id: 1, title: 'Section 1', content: 'Content 1', order: 0 },
];


const renderPage = (campaignId: string) => {
  return render(
    <MemoryRouter initialEntries={[`/campaign/${campaignId}`]}>
      <Routes>
        <Route path="/campaign/:campaignId" element={<CampaignEditorPage />} />
      </Routes>
    </MemoryRouter>
  );
};

describe('CampaignEditorPage - Badge Image Functionality', () => {
  beforeEach(() => {
    mockGetCampaignById.mockReset();
    mockGetCampaignSections.mockReset();
    mockUpdateCampaign.mockReset();
    mockGetAvailableLLMs.mockReset();
    mockPrompt.mockReset(); // Re-added
    mockConfirm.mockReset();

    // Default mocks for services called on page load
    mockGetAvailableLLMs.mockResolvedValue(mockLLMs);
    mockGetCampaignSections.mockResolvedValue(mockSections); // Provide a default to avoid issues
  });

  test('displays badge image and correct buttons when badge_image_url exists', async () => {
    mockGetCampaignById.mockResolvedValue(mockCampaignWithBadge);
    
    renderPage(mockCampaignWithBadge.id);

    // Wait for loading to complete and campaign data to be processed
    await waitFor(() => expect(screen.getByText('Campaign Badge')).toBeInTheDocument());
    
    const badgeImage = screen.getByRole('img', { name: /badge/i });
    expect(badgeImage).toBeInTheDocument();
    expect(badgeImage).toHaveAttribute('src', mockCampaignWithBadge.badge_image_url);

    const parentLink = badgeImage.closest('a');
    expect(parentLink).toHaveAttribute('href', mockCampaignWithBadge.badge_image_url);
    expect(parentLink).toHaveAttribute('target', '_blank');
    
    expect(screen.getByRole('button', { name: 'Generate Badge' })).toBeInTheDocument(); // Text changed
    expect(screen.getByRole('button', { name: 'Edit URL' })).toBeInTheDocument(); // New button
    expect(screen.getByRole('button', { name: 'Remove Badge' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove Badge' })).toBeEnabled();
  });

  test('displays placeholder and correct buttons when badge_image_url does not exist', async () => {
    mockGetCampaignById.mockResolvedValue(mockCampaignWithoutBadge);
    
    renderPage(mockCampaignWithoutBadge.id);

    await waitFor(() => expect(screen.getByText('Campaign Badge')).toBeInTheDocument());

    expect(screen.getByText('No badge image set.')).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: /badge/i })).not.toBeInTheDocument();
    
    expect(screen.getByRole('button', { name: 'Generate Badge' })).toBeInTheDocument(); // Text changed
    expect(screen.getByRole('button', { name: 'Edit URL' })).toBeInTheDocument(); // New button
    expect(screen.queryByRole('button', { name: 'Remove Badge' })).not.toBeInTheDocument();
  });

  test('Generate Badge button (previously Set Badge) opens modal and updates badge_image_url on generation', async () => {
    mockGetCampaignById.mockResolvedValue(mockCampaignWithoutBadge);
    const newImageUrlFromModal = 'http://example.com/mock-generated-badge.png';
    mockUpdateCampaign.mockResolvedValue({ 
      ...mockCampaignWithoutBadge, 
      badge_image_url: newImageUrlFromModal 
    });
  
    renderPage(mockCampaignWithoutBadge.id);
  
    const generateBadgeButton = await screen.findByRole('button', { name: 'Generate Badge' });
    expect(screen.queryByTestId('mock-image-gen-modal')).not.toBeInTheDocument();
  
    fireEvent.click(generateBadgeButton);
  
    const mockModal = await screen.findByTestId('mock-image-gen-modal');
    expect(mockModal).toBeInTheDocument();
  
    const simulateGenerationButtonInModal = screen.getByRole('button', { name: 'Simulate Generate Badge' });
    fireEvent.click(simulateGenerationButtonInModal);
  
    await waitFor(() => expect(mockUpdateCampaign).toHaveBeenCalledWith(
      mockCampaignWithoutBadge.id,
      { badge_image_url: newImageUrlFromModal }
    ));
    
    await waitFor(() => expect(screen.queryByTestId('mock-image-gen-modal')).not.toBeInTheDocument());
  
    await waitFor(() => {
      const badgeImage = screen.getByRole('img', { name: /badge/i });
      expect(badgeImage).toHaveAttribute('src', newImageUrlFromModal);
      expect(screen.getByRole('button', { name: 'Generate Badge' })).toBeInTheDocument(); // Text should remain "Generate Badge"
    });
  });

  // This test is for the "Generate Badge" button when a badge already exists.
  // It effectively replaces the old "Change Badge" test's primary function of opening the modal.
  test('Generate Badge button (when badge exists) opens modal and updates badge_image_url on generation', async () => {
    mockGetCampaignById.mockResolvedValue(mockCampaignWithBadge);
    const newImageUrlFromModal = 'http://example.com/new-mock-badge.png';
    mockUpdateCampaign.mockResolvedValue({ 
      ...mockCampaignWithBadge, 
      badge_image_url: newImageUrlFromModal 
    });

    renderPage(mockCampaignWithBadge.id);

    const generateBadgeButton = await screen.findByRole('button', { name: 'Generate Badge' });
    fireEvent.click(generateBadgeButton);

    const mockModal = await screen.findByTestId('mock-image-gen-modal');
    expect(mockModal).toBeInTheDocument();

    const simulateGenerationButtonInModal = screen.getByRole('button', { name: 'Simulate Generate Badge' });
    fireEvent.click(simulateGenerationButtonInModal);
    
    await waitFor(() => expect(mockUpdateCampaign).toHaveBeenCalledWith(
      mockCampaignWithBadge.id,
      { badge_image_url: newImageUrlFromModal }
    ));

    await waitFor(() => expect(screen.queryByTestId('mock-image-gen-modal')).not.toBeInTheDocument());

    await waitFor(() => {
      const badgeImage = screen.getByRole('img', { name: /badge/i });
      expect(badgeImage).toHaveAttribute('src', newImageUrlFromModal);
    });
  });

  test('Remove Badge button removes badge_image_url after confirmation', async () => {
    mockGetCampaignById.mockResolvedValue(mockCampaignWithBadge);
    mockConfirm.mockReturnValue(true); // User confirms removal
    mockUpdateCampaign.mockResolvedValue({ ...mockCampaignWithBadge, badge_image_url: null });

    renderPage(mockCampaignWithBadge.id);
    await waitFor(() => expect(screen.getByText('Campaign Badge')).toBeInTheDocument());
    
    const removeBadgeButton = screen.getByRole('button', { name: 'Remove Badge' });
    fireEvent.click(removeBadgeButton);

    expect(mockConfirm).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(mockUpdateCampaign).toHaveBeenCalledWith(
      mockCampaignWithBadge.id,
      { badge_image_url: null }
    ));

    await waitFor(() => {
      expect(screen.getByText('No badge image set.')).toBeInTheDocument();
      expect(screen.queryByRole('img', { name: /badge/i })).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Set Badge' })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Remove Badge' })).not.toBeInTheDocument();
    });
  });

   test('Remove Badge button does nothing if user cancels confirmation', async () => {
    mockGetCampaignById.mockResolvedValue(mockCampaignWithBadge);
    mockConfirm.mockReturnValue(false); // User cancels removal

    renderPage(mockCampaignWithBadge.id);
    await waitFor(() => expect(screen.getByText('Campaign Badge')).toBeInTheDocument());
    
    const removeBadgeButton = screen.getByRole('button', { name: 'Remove Badge' });
    fireEvent.click(removeBadgeButton);

    expect(mockConfirm).toHaveBeenCalledTimes(1);
    expect(mockUpdateCampaign).not.toHaveBeenCalled();
    
    // Image should still be there
    const badgeImage = screen.getByRole('img', { name: /badge/i });
    expect(badgeImage).toHaveAttribute('src', mockCampaignWithBadge.badge_image_url);
  });

  describe('Edit URL button functionality', () => {
    test('is visible and updates badge_image_url via prompt', async () => {
      mockGetCampaignById.mockResolvedValue(mockCampaignWithBadge); // Start with an existing badge
      const editedImageUrl = 'http://example.com/edited-badge.jpg';
      mockPrompt.mockReturnValue(editedImageUrl); // User enters this URL in prompt
      mockUpdateCampaign.mockResolvedValue({ ...mockCampaignWithBadge, badge_image_url: editedImageUrl });
  
      renderPage(mockCampaignWithBadge.id);
      const editUrlButton = await screen.findByRole('button', { name: 'Edit URL' });
      expect(editUrlButton).toBeInTheDocument();
  
      fireEvent.click(editUrlButton);
  
      expect(mockPrompt).toHaveBeenCalledWith(
        "Enter or edit the image URL for the campaign badge:", 
        mockCampaignWithBadge.badge_image_url // Check if current URL is default in prompt
      );
      await waitFor(() => expect(mockUpdateCampaign).toHaveBeenCalledWith(
        mockCampaignWithBadge.id,
        { badge_image_url: editedImageUrl }
      ));
      
      await waitFor(() => {
        const badgeImage = screen.getByRole('img', { name: /badge/i });
        expect(badgeImage).toHaveAttribute('src', editedImageUrl);
      });
    });

    test('Edit URL button sets URL to null if prompt returns empty string', async () => {
      mockGetCampaignById.mockResolvedValue(mockCampaignWithBadge);
      mockPrompt.mockReturnValue(""); // User clears the URL in prompt
      mockUpdateCampaign.mockResolvedValue({ ...mockCampaignWithBadge, badge_image_url: null });

      renderPage(mockCampaignWithBadge.id);
      const editUrlButton = await screen.findByRole('button', { name: 'Edit URL' });
      fireEvent.click(editUrlButton);

      expect(mockPrompt).toHaveBeenCalledTimes(1);
      await waitFor(() => expect(mockUpdateCampaign).toHaveBeenCalledWith(
        mockCampaignWithBadge.id,
        { badge_image_url: null }
      ));

      await waitFor(() => {
        expect(screen.getByText('No badge image set.')).toBeInTheDocument();
        expect(screen.queryByRole('img', { name: /badge/i })).not.toBeInTheDocument();
      });
    });

    test('Edit URL button does nothing if prompt is cancelled', async () => {
      mockGetCampaignById.mockResolvedValue(mockCampaignWithBadge);
      mockPrompt.mockReturnValue(null); // User cancels prompt

      renderPage(mockCampaignWithBadge.id);
      const editUrlButton = await screen.findByRole('button', { name: 'Edit URL' });
      fireEvent.click(editUrlButton);

      expect(mockPrompt).toHaveBeenCalledTimes(1);
      expect(mockUpdateCampaign).not.toHaveBeenCalled();
      
      // Image should still be the original one
      const badgeImage = screen.getByRole('img', { name: /badge/i });
      expect(badgeImage).toHaveAttribute('src', mockCampaignWithBadge.badge_image_url);
    });
  });
});
