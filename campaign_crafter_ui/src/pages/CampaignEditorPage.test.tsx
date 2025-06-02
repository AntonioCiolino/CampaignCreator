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

const mockGetCampaignById = campaignService.getCampaignById as jest.Mock;
const mockGetCampaignSections = campaignService.getCampaignSections as jest.Mock;
const mockUpdateCampaign = campaignService.updateCampaign as jest.Mock;
const mockGetAvailableLLMs = llmService.getAvailableLLMs as jest.Mock;

// Mock window.prompt and window.confirm
const mockPrompt = jest.fn();
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
    mockPrompt.mockReset();
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
    
    expect(screen.getByRole('button', { name: 'Change Badge' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove Badge' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove Badge' })).toBeEnabled();
  });

  test('displays placeholder and correct buttons when badge_image_url does not exist', async () => {
    mockGetCampaignById.mockResolvedValue(mockCampaignWithoutBadge);
    
    renderPage(mockCampaignWithoutBadge.id);

    await waitFor(() => expect(screen.getByText('Campaign Badge')).toBeInTheDocument());

    expect(screen.getByText('No badge image set.')).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: /badge/i })).not.toBeInTheDocument();
    
    expect(screen.getByRole('button', { name: 'Set Badge' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Remove Badge' })).not.toBeInTheDocument();
  });

  test('Set Badge button updates badge_image_url via prompt', async () => {
    mockGetCampaignById.mockResolvedValue(mockCampaignWithoutBadge);
    const newImageUrl = 'http://example.com/newbadge.png';
    mockPrompt.mockReturnValue(newImageUrl); // User enters this URL in prompt
    mockUpdateCampaign.mockResolvedValue({ ...mockCampaignWithoutBadge, badge_image_url: newImageUrl });

    renderPage(mockCampaignWithoutBadge.id);
    await waitFor(() => expect(screen.getByText('Campaign Badge')).toBeInTheDocument());

    const setBadgeButton = screen.getByRole('button', { name: 'Set Badge' });
    fireEvent.click(setBadgeButton);

    expect(mockPrompt).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(mockUpdateCampaign).toHaveBeenCalledWith(
      mockCampaignWithoutBadge.id,
      { badge_image_url: newImageUrl }
    ));
    
    // Check if UI updates (image appears, buttons change)
    await waitFor(() => {
      const badgeImage = screen.getByRole('img', { name: /badge/i });
      expect(badgeImage).toHaveAttribute('src', newImageUrl);
      expect(screen.getByRole('button', { name: 'Change Badge' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Remove Badge' })).toBeInTheDocument();
    });
  });

  test('Change Badge button updates badge_image_url via prompt', async () => {
    mockGetCampaignById.mockResolvedValue(mockCampaignWithBadge);
    const changedImageUrl = 'http://example.com/changedbadge.png';
    mockPrompt.mockReturnValue(changedImageUrl);
    mockUpdateCampaign.mockResolvedValue({ ...mockCampaignWithBadge, badge_image_url: changedImageUrl });

    renderPage(mockCampaignWithBadge.id);
    await waitFor(() => expect(screen.getByText('Campaign Badge')).toBeInTheDocument());

    const changeBadgeButton = screen.getByRole('button', { name: 'Change Badge' });
    fireEvent.click(changeBadgeButton);

    expect(mockPrompt).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(mockUpdateCampaign).toHaveBeenCalledWith(
      mockCampaignWithBadge.id,
      { badge_image_url: changedImageUrl }
    ));

    await waitFor(() => {
      const badgeImage = screen.getByRole('img', { name: /badge/i });
      expect(badgeImage).toHaveAttribute('src', changedImageUrl);
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

});
