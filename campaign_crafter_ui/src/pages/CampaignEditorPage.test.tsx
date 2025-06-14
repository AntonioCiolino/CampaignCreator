import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import CampaignEditorPage from './CampaignEditorPage';
import * as campaignService from '../services/campaignService';
import * as llmService from '../services/llmService'; // For getAvailableLLMs
// Import LLMModel type for explicit typing of mockLLMs if desired, though not strictly necessary for mocks
// import { LLMModel } from '../services/llmService';

import * as imageService from '../services/imageService'; // For MoodBoardPanel image uploads

// Mock services
jest.mock('../services/campaignService');
jest.mock('../services/llmService');
jest.mock('../services/imageService'); // Mock imageService

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
const mockGenerateCampaignTOC = campaignService.generateCampaignTOC as jest.Mock; // Added for TOC tests
const mockGetAvailableLLMs = llmService.getAvailableLLMs as jest.Mock;
const mockUploadMoodboardImageApi = imageService.uploadMoodboardImageApi as jest.Mock;
// The global mock for ImageGenerationModal handles simulation of image generation directly.
// So, no need to mock a specific image generation function from imageService here for that modal.

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
  mood_board_image_urls: [], // Add for mood board tests
};

const mockCampaignForMoodboard = {
  id: 'moodboard-campaign-1',
  title: 'Moodboard Test Campaign',
  initial_user_prompt: 'Prompt for moodboard campaign',
  concept: 'Concept for moodboard campaign.',
  display_toc: [],
  homebrewery_export: null,
  badge_image_url: null,
  owner_id: 1,
  sections: [],
  mood_board_image_urls: ['http://example.com/initial_mood_image.jpg'],
  selected_llm_id: 'openai/gpt-3.5-turbo', // Ensure an LLM is selected for generation options
};

// Explicitly type with llmService.LLMModel if you imported it, or ensure structural compatibility
const mockLLMs: llmService.LLMModel[] = [ // or just any[] if not importing type for mocks
  {
    id: 'openai/gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    capabilities: ['chat'],
    model_type: "chat",        // Added
    supports_temperature: true // Added
  },
  {
    id: 'openai/gpt-4',
    name: 'GPT-4',
    capabilities: ['chat'],
    model_type: "chat",        // Added
    supports_temperature: true // Added
  },
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
    mockGenerateCampaignTOC.mockReset(); // Reset TOC mock
    mockPrompt.mockReset();
    mockConfirm.mockReset();
    mockUploadMoodboardImageApi.mockReset();
    // No longer need to reset mockGenerateImageService as it's removed


    // Default mocks for services called on page load
    mockGetAvailableLLMs.mockResolvedValue(mockLLMs);
    mockGetCampaignSections.mockResolvedValue(mockSections);
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

describe('CampaignEditorPage - Regenerate TOC Warning', () => {
  beforeEach(() => {
    // Clear mocks before each test in this suite
    mockGetCampaignById.mockReset();
    mockGetCampaignSections.mockReset();
    mockGetAvailableLLMs.mockReset();
    mockGenerateCampaignTOC.mockReset();
    mockConfirm.mockReset();

    // Default mocks for services called on page load for this suite
    mockGetAvailableLLMs.mockResolvedValue(mockLLMs);
    mockGetCampaignSections.mockResolvedValue(mockSections); // Default sections
  });

  test('shows warning if TOC exists and regenerates if user confirms', async () => {
    const campaignWithExistingTOC = {
      ...mockCampaignWithBadge, // Use a base campaign
      id: 'toc-test-1',
      display_toc: "## Chapter 1\n- Section A\n- Section B",
      selected_llm_id: 'openai/gpt-3.5-turbo', // Ensure an LLM is selected for button to be enabled
    };
    mockGetCampaignById.mockResolvedValue(campaignWithExistingTOC);
    mockConfirm.mockReturnValue(true); // User confirms
    mockGenerateCampaignTOC.mockResolvedValue({ ...campaignWithExistingTOC, display_toc: "New TOC" });

    renderPage(campaignWithExistingTOC.id);

    // Wait for page to load and button to be available
    const regenerateButton = await screen.findByRole('button', { name: /Re-generate Table of Contents/i });
    expect(regenerateButton).toBeEnabled(); // Check if LLM is selected

    fireEvent.click(regenerateButton);

    await waitFor(() => {
      expect(mockConfirm).toHaveBeenCalledWith("A Table of Contents already exists. Are you sure you want to regenerate it? This will overwrite the current TOC.");
    });
    await waitFor(() => {
      expect(mockGenerateCampaignTOC).toHaveBeenCalledWith(campaignWithExistingTOC.id, {});
    });
    // Optionally, check for success message or updated TOC if needed
    expect(await screen.findByText(/Table of Contents generated successfully!/i)).toBeInTheDocument();
  });

  test('does not regenerate if user cancels warning', async () => {
    const campaignWithExistingTOC = {
      ...mockCampaignWithBadge,
      id: 'toc-test-2',
      display_toc: "## Chapter 1\n- Section A",
      selected_llm_id: 'openai/gpt-3.5-turbo',
    };
    mockGetCampaignById.mockResolvedValue(campaignWithExistingTOC);
    mockConfirm.mockReturnValue(false); // User cancels
    // mockGenerateCampaignTOC is not expected to be called, so no specific mock return value needed for it.

    renderPage(campaignWithExistingTOC.id);

    const regenerateButton = await screen.findByRole('button', { name: /Re-generate Table of Contents/i });
    expect(regenerateButton).toBeEnabled();
    fireEvent.click(regenerateButton);

    await waitFor(() => {
      expect(mockConfirm).toHaveBeenCalledWith("A Table of Contents already exists. Are you sure you want to regenerate it? This will overwrite the current TOC.");
    });
    expect(mockGenerateCampaignTOC).not.toHaveBeenCalled();
  });

  test('no warning if TOC does not exist and generates TOC', async () => {
    const campaignWithoutTOC = {
      ...mockCampaignWithoutBadge, // Use a base campaign
      id: 'toc-test-3',
      display_toc: null, // No TOC
      selected_llm_id: 'openai/gpt-3.5-turbo',
    };
    mockGetCampaignById.mockResolvedValue(campaignWithoutTOC);
    // window.confirm should not be called, so no need to mock its return for this path.
    mockGenerateCampaignTOC.mockResolvedValue({ ...campaignWithoutTOC, display_toc: "Generated TOC" });

    renderPage(campaignWithoutTOC.id);

    const generateButton = await screen.findByRole('button', { name: /Generate Table of Contents/i });
    expect(generateButton).toBeEnabled();
    fireEvent.click(generateButton);

    expect(mockConfirm).not.toHaveBeenCalled();
    await waitFor(() => {
      expect(mockGenerateCampaignTOC).toHaveBeenCalledWith(campaignWithoutTOC.id, {});
    });
    expect(await screen.findByText(/Table of Contents generated successfully!/i)).toBeInTheDocument();
  });

  test('no warning if TOC is an empty string and generates TOC', async () => {
    const campaignWithEmptyTOC = {
      ...mockCampaignWithoutBadge,
      id: 'toc-test-4',
      display_toc: "   ", // TOC with only whitespace
      selected_llm_id: 'openai/gpt-3.5-turbo',
    };
    mockGetCampaignById.mockResolvedValue(campaignWithEmptyTOC);
    mockGenerateCampaignTOC.mockResolvedValue({ ...campaignWithEmptyTOC, display_toc: "Generated TOC from empty" });

    renderPage(campaignWithEmptyTOC.id);

    // Button text should be "Generate..." if TOC is effectively empty
    const generateButton = await screen.findByRole('button', { name: /Generate Table of Contents/i });
    expect(generateButton).toBeEnabled();
    fireEvent.click(generateButton);

    expect(mockConfirm).not.toHaveBeenCalled();
    await waitFor(() => {
      expect(mockGenerateCampaignTOC).toHaveBeenCalledWith(campaignWithEmptyTOC.id, {});
    });
     expect(await screen.findByText(/Table of Contents generated successfully!/i)).toBeInTheDocument();
  });
});


describe('CampaignEditorPage - Mood Board Image Addition', () => {
  beforeEach(() => {
    // Reset mocks
    mockGetCampaignById.mockReset();
    mockGetCampaignSections.mockResolvedValue(mockSections); // Default sections
    mockGetAvailableLLMs.mockResolvedValue(mockLLMs); // Default LLMs
    mockUpdateCampaign.mockReset();
    mockUploadMoodboardImageApi.mockReset();
    // mockGenerateImageService was removed, so no reset needed here either.

    // Setup a consistent campaign state for mood board tests
    mockGetCampaignById.mockResolvedValue(mockCampaignForMoodboard);
    // Mock updateCampaign to echo back the mood_board_image_urls from payload
    mockUpdateCampaign.mockImplementation(async (campaignId, payload) => {
      return {
        ...mockCampaignForMoodboard,
        id: campaignId,
        mood_board_image_urls: payload.mood_board_image_urls || mockCampaignForMoodboard.mood_board_image_urls,
      };
    });
  });

  test('"Add Image by URL" flow updates mood board', async () => {
    renderPage(mockCampaignForMoodboard.id);

    await fireEvent.click(await screen.findByRole('button', { name: /Show Mood Board/i }));
    await fireEvent.click(await screen.findByRole('button', { name: /Add new image to mood board/i })); // '+' button

    // In AddMoodBoardImageModal
    await fireEvent.click(screen.getByText('Add Image by URL'));

    const urlInput = screen.getByLabelText('Image URL');
    const newUrl = 'http://example.com/new_url_via_paste.png';
    await fireEvent.change(urlInput, { target: { value: newUrl } }); // Using fireEvent.change for direct input set
    await fireEvent.click(screen.getByText('Add URL'));

    await waitFor(() => {
      expect(mockUpdateCampaign).toHaveBeenCalledWith(
        mockCampaignForMoodboard.id,
        expect.objectContaining({
          mood_board_image_urls: [...mockCampaignForMoodboard.mood_board_image_urls, newUrl],
        })
      );
    });
    // Check if the image appears in the mood board (assuming MoodBoardPanel displays img tags)
    // This requires MoodBoardPanel to re-render with updated campaign prop
    // The mockUpdateCampaign now returns the updated list, so CampaignEditorPage state should update
    expect(await screen.findByAltText(`Mood board ${mockCampaignForMoodboard.mood_board_image_urls.length + 1}`)).toHaveAttribute('src', newUrl);
  });

  test('"Upload Image" flow updates mood board', async () => {
    const uploadedImageUrl = 'http://example.com/uploaded_image.png';
    mockUploadMoodboardImageApi.mockResolvedValue({ imageUrl: uploadedImageUrl, campaign: {} });

    renderPage(mockCampaignForMoodboard.id);

    await fireEvent.click(await screen.findByRole('button', { name: /Show Mood Board/i }));
    await fireEvent.click(await screen.findByRole('button', { name: /Add new image to mood board/i }));

    // In AddMoodBoardImageModal
    await fireEvent.click(screen.getByText('Upload Image from Computer'));

    // Find file input - this might be tricky depending on how it's structured in AddMoodBoardImageModal
    // Assuming a simple input type="file" that becomes available
    const fileInput = screen.getByTestId('mock-modal').querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
    if (!fileInput) throw new Error("File input not found in mocked modal content for upload view");

    const testFile = new File(['(⌐□_□)'], 'chucknorris.png', { type: 'image/png' });
    // Simulate file selection
    await act(async () => { // act might be needed for state updates from userEvent.upload
      fireEvent.change(fileInput, { target: { files: [testFile] } });
    });

    // Wait for upload button to be enabled and click it
    const uploadButton = await screen.findByRole('button', { name: 'Upload' });
    expect(uploadButton).not.toBeDisabled();
    await fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(mockUploadMoodboardImageApi).toHaveBeenCalledWith(mockCampaignForMoodboard.id, testFile);
    });
    await waitFor(() => {
      expect(mockUpdateCampaign).toHaveBeenCalledWith(
        mockCampaignForMoodboard.id,
        expect.objectContaining({
          mood_board_image_urls: [...mockCampaignForMoodboard.mood_board_image_urls, uploadedImageUrl],
        })
      );
    });
    expect(await screen.findByAltText(`Mood board ${mockCampaignForMoodboard.mood_board_image_urls.length + 1}`)).toHaveAttribute('src', uploadedImageUrl);
  });

  test('"Generate Image" flow updates mood board', async () => {
    // The ImageGenerationModal is globally mocked. Its "Simulate Generate Badge" button
    // will call onImageSuccessfullyGenerated with 'http://example.com/mock-generated-badge.png'.
    // We'll use this URL for this test.
    const generatedImageUrl = 'http://example.com/mock-generated-badge.png'; // From the global mock

    renderPage(mockCampaignForMoodboard.id);

    await fireEvent.click(await screen.findByRole('button', { name: /Show Mood Board/i }));
    await fireEvent.click(await screen.findByRole('button', { name: /Add new image to mood board/i }));

    // In AddMoodBoardImageModal, click "Generate New Image"
    await fireEvent.click(screen.getByText('Generate New Image'));

    // This should close AddMoodBoardImageModal and open ImageGenerationModal (mocked version)
    const imageGenModal = await screen.findByTestId('mock-image-gen-modal');
    expect(imageGenModal).toBeInTheDocument();

    // Simulate generation within the mocked ImageGenerationModal
    // The mocked modal has a button "Simulate Generate Badge" which calls onImageSuccessfullyGenerated
    // In CampaignEditorPage, for the mood board instance, onImageSuccessfullyGenerated updates editableMoodBoardUrls
    await fireEvent.click(screen.getByRole('button', { name: 'Simulate Generate Badge' }));

    // The onImageSuccessfullyGenerated in CampaignEditorPage for the mood board's modal
    // directly updates `editableMoodBoardUrls`. This state change then triggers the
    // useEffect for auto-saving mood board URLs, which calls updateCampaign.
    await waitFor(() => {
      expect(mockUpdateCampaign).toHaveBeenCalledWith(
        mockCampaignForMoodboard.id,
        expect.objectContaining({
          mood_board_image_urls: [...mockCampaignForMoodboard.mood_board_image_urls, generatedImageUrl],
        })
      );
    });

    // Verify the image appears in the mood board
    expect(await screen.findByAltText(`Mood board ${mockCampaignForMoodboard.mood_board_image_urls.length + 1}`)).toHaveAttribute('src', generatedImageUrl);

    // Ensure the image generation modal is closed
    expect(screen.queryByTestId('mock-image-gen-modal')).not.toBeInTheDocument();
  });
});

[end of campaign_crafter_ui/src/pages/CampaignEditorPage.test.tsx]
