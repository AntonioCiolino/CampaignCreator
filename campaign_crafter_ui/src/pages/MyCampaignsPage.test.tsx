import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import MyCampaignsPage from './MyCampaignsPage';
import * as campaignService from '../services/campaignService';
import { Campaign } from '../types/campaignTypes';

// Mock the entire campaignService
jest.mock('../services/campaignService');

const mockCampaignsData: Campaign[] = [
  {
    id: 1,
    title: 'Campaign Alpha',
    initial_user_prompt: 'Alpha prompt',
    concept: 'Alpha concept',
    display_toc: [{ title: 'Chapter 1', type: 'chapter' }],
    homebrewery_toc: null,
    badge_image_url: null,
    selected_llm_id: 'openai/gpt-3.5-turbo',
    temperature: 0.7,
    owner_id: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    sections: [],
    mood_board_image_urls: [],
    theme_primary_color: null,
    theme_secondary_color: null,
    theme_background_color: null,
    theme_text_color: null,
    theme_font_family: null,
    theme_background_image_url: null,
    theme_background_image_opacity: null,
    homebrewery_export: null,
    thematic_image_url: null,
    thematic_image_prompt: null,

  },
  {
    id: 2,
    title: 'Campaign Beta',
    initial_user_prompt: 'Beta prompt',
    concept: 'Beta concept',
    display_toc: [{ title: 'Intro', type: 'introduction' }],
    homebrewery_toc: null,
    badge_image_url: null,
    selected_llm_id: 'openai/gpt-4',
    temperature: 0.5,
    owner_id: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    sections: [],
    mood_board_image_urls: [],
    theme_primary_color: null,
    theme_secondary_color: null,
    theme_background_color: null,
    theme_text_color: null,
    theme_font_family: null,
    theme_background_image_url: null,
    theme_background_image_opacity: null,
    homebrewery_export: null,
    thematic_image_url: null,
    thematic_image_prompt: null,
  },
];

// Mock useNavigate
const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockedNavigate,
}));


describe('MyCampaignsPage', () => {
  beforeEach(() => {
    // Reset mocks before each test
    (campaignService.getAllCampaigns as jest.Mock).mockResolvedValue([...mockCampaignsData]);
    (campaignService.deleteCampaign as jest.Mock).mockResolvedValue(undefined);
    // Mock other services if MyCampaignsPage uses them during these flows
    mockedNavigate.mockClear(); // Clear navigate mock calls
  });

  test('displays campaigns and initiates deletion process successfully', async () => {
    render(
      <MemoryRouter>
        <MyCampaignsPage />
      </MemoryRouter>
    );

    // Verify campaign cards are displayed
    expect(await screen.findByText('Campaign Alpha')).toBeInTheDocument();
    expect(screen.getByText('Campaign Beta')).toBeInTheDocument();

    // Simulate a click on the "Delete" button of the first campaign card
    // Buttons are inside CampaignCard, ensure they are uniquely identifiable or use querySelector logic if needed
    const deleteButtons = screen.getAllByRole('button', { name: /Delete campaign/i });
    expect(deleteButtons.length).toBeGreaterThan(0);

    await act(async () => {
        fireEvent.click(deleteButtons[0]); // Click delete for "Campaign Alpha"
    });


    // Verify that the ConfirmationModal appears
    expect(await screen.findByText('Confirm Deletion')).toBeInTheDocument();
    expect(screen.getByText(/Are you sure you want to delete the campaign "Campaign Alpha"\?/i)).toBeInTheDocument();

    // Simulate a click on the "Confirm" button in the modal
    const confirmDeleteButton = screen.getByRole('button', { name: 'Delete' });

    await act(async () => {
        fireEvent.click(confirmDeleteButton);
    });

    // Assert that campaignService.deleteCampaign was called
    expect(campaignService.deleteCampaign).toHaveBeenCalledWith(mockCampaignsData[0].id);
    expect(campaignService.deleteCampaign).toHaveBeenCalledTimes(1);

    // Assert that getAllCampaigns was called again (to refresh the list)
    // This depends on the implementation choice in handleDeleteCampaign
    // If filtering locally, this might not be called again immediately, or at all.
    // Current implementation in previous step uses fetchCampaigns() which calls getAllCampaigns()
    await waitFor(() => {
      expect(campaignService.getAllCampaigns).toHaveBeenCalledTimes(2); // Initial load + after delete
    });

    // Optional: Verify modal is closed
    expect(screen.queryByText('Confirm Deletion')).not.toBeInTheDocument();
  });

  test('handles error during campaign deletion', async () => {
    // Mock deleteCampaign to reject
    const errorMessage = 'Network Error: Failed to delete campaign';
    (campaignService.deleteCampaign as jest.Mock).mockRejectedValueOnce({
        response: { data: { detail: errorMessage } }
    });

    render(
      <MemoryRouter>
        <MyCampaignsPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('Campaign Alpha')).toBeInTheDocument();
    const deleteButtons = screen.getAllByRole('button', { name: /Delete campaign/i });

    await act(async () => {
        fireEvent.click(deleteButtons[0]);
    });

    expect(await screen.findByText('Confirm Deletion')).toBeInTheDocument();
    const confirmDeleteButton = screen.getByRole('button', { name: 'Delete' });

    await act(async () => {
        fireEvent.click(confirmDeleteButton);
    });


    expect(campaignService.deleteCampaign).toHaveBeenCalledWith(mockCampaignsData[0].id);

    // Verify that an error message is displayed on the page
    expect(await screen.findByText(errorMessage)).toBeInTheDocument();

    // Verify the modal is closed
    expect(screen.queryByText('Confirm Deletion')).not.toBeInTheDocument();
  });

  test('cancels deletion from confirmation modal', async () => {
    render(
      <MemoryRouter>
        <MyCampaignsPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('Campaign Alpha')).toBeInTheDocument();
    const deleteButtons = screen.getAllByRole('button', { name: /Delete campaign/i });

    await act(async () => {
        fireEvent.click(deleteButtons[0]);
    });

    expect(await screen.findByText('Confirm Deletion')).toBeInTheDocument();

    // Simulate a click on the "Cancel" button in the modal
    const cancelButton = screen.getByRole('button', { name: 'Cancel' });
    await act(async () => {
        fireEvent.click(cancelButton);
    });


    // Assert that campaignService.deleteCampaign was *not* called
    expect(campaignService.deleteCampaign).not.toHaveBeenCalled();

    // Verify the modal is closed
    expect(screen.queryByText('Confirm Deletion')).not.toBeInTheDocument();
  });
});
