import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import CampaignDetailsEditor from './CampaignDetailsEditor';

describe('CampaignDetailsEditor', () => {
  // Clear all mocks before each test
  beforeEach(() => {
    mockSetEditableTitle.mockClear();
    mockSetInitialPrompt.mockClear();
    mockSetCampaignBadgeImage.mockClear();
    mockHandleSaveCampaignDetails.mockClear();
    mockOnSuggestTitles.mockClear();
    mockOnOpenBadgeImageModal.mockClear();
    mockOnEditBadgeImageUrl.mockClear();
    mockOnRemoveBadgeImage.mockClear();
    mockSetEditableMoodBoardUrls.mockClear(); // Clear new mock
  });

  const mockSetEditableTitle = jest.fn();
  const mockSetInitialPrompt = jest.fn();
  const mockSetCampaignBadgeImage = jest.fn();
  const mockHandleSaveCampaignDetails = jest.fn();
  const mockOnSuggestTitles = jest.fn();
  const mockOnOpenBadgeImageModal = jest.fn();
  const mockOnEditBadgeImageUrl = jest.fn();
  const mockOnRemoveBadgeImage = jest.fn();
  const mockSetEditableMoodBoardUrls = jest.fn(); // Define new mock

  const defaultProps = {
    editableTitle: 'Test Title',
    setEditableTitle: mockSetEditableTitle,
    initialPrompt: 'Test Prompt',
    setInitialPrompt: mockSetInitialPrompt,
    campaignBadgeImage: '',
    setCampaignBadgeImage: mockSetCampaignBadgeImage,
    handleSaveCampaignDetails: mockHandleSaveCampaignDetails,
    // New props
    onSuggestTitles: mockOnSuggestTitles,
    isGeneratingTitles: false,
    titlesError: null,
    selectedLLMId: 'test-llm-id',
    originalTitle: 'Test Title', // Match editableTitle to keep save button disabled initially
    originalInitialPrompt: 'Test Prompt', // Match initialPrompt to keep save button disabled
    originalBadgeImageUrl: '',
    onOpenBadgeImageModal: mockOnOpenBadgeImageModal,
    onEditBadgeImageUrl: mockOnEditBadgeImageUrl,
    onRemoveBadgeImage: mockOnRemoveBadgeImage,
    badgeUpdateLoading: false,
    badgeUpdateError: null,
    // Add new mood board props
    editableMoodBoardUrls: [],
    setEditableMoodBoardUrls: mockSetEditableMoodBoardUrls,
    originalMoodBoardUrls: [],
  };

  test('renders correctly with basic props', () => {
    render(<CampaignDetailsEditor {...defaultProps} />);

    // Check for Campaign Title
    expect(screen.getByLabelText(/Campaign Title/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Title')).toBeInTheDocument();

    // Check for Initial Prompt visibility toggle and then reveal content
    // The TextField itself is not initially visible. We check for the toggle.
    expect(screen.getByText(/Initial Prompt/i)).toBeInTheDocument(); // The Typography label
    expect(screen.getByRole('button', { name: /Show initial prompt/i })).toBeInTheDocument();
    // fireEvent.click(screen.getByRole('button', { name: /Show initial prompt/i }));
    // expect(screen.getByDisplayValue('Test Prompt')).toBeInTheDocument(); // Now it should be visible

    // Check for Campaign Badge visibility toggle
    expect(screen.getByText(/Campaign Badge/i)).toBeInTheDocument(); // The Typography label
    expect(screen.getByRole('button', { name: /Show badge actions/i })).toBeInTheDocument();

    // Check for Save button
    expect(screen.getByRole('button', { name: /Save Details/i })).toBeInTheDocument();
    // By default, originalTitle and originalInitialPrompt match editable versions, so button should be disabled
    expect(screen.getByRole('button', { name: /Save Details/i })).toBeDisabled();
  });

  test('renders badge preview when campaignBadgeImage is provided and badge section is visible', () => {
    render(<CampaignDetailsEditor {...defaultProps} campaignBadgeImage="http://example.com/badge.png" />);
    // First, make the badge section visible
    fireEvent.click(screen.getByRole('button', { name: /Show badge actions/i }));
    const image = screen.getByAltText('Campaign Badge');
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute('src', 'http://example.com/badge.png');
  });

  test('calls setEditableTitle on title change', () => {
    render(<CampaignDetailsEditor {...defaultProps} />);
    const titleInput = screen.getByLabelText(/Campaign Title/i);
    fireEvent.change(titleInput, { target: { value: 'New Title' } });
    expect(mockSetEditableTitle).toHaveBeenCalledWith('New Title');
  });

  test('calls setInitialPrompt on prompt change', () => {
    render(<CampaignDetailsEditor {...defaultProps} />);
    const promptInput = screen.getByLabelText(/Initial Prompt/i);
    fireEvent.change(promptInput, { target: { value: 'New Prompt' } });
    expect(mockSetInitialPrompt).toHaveBeenCalledWith('New Prompt');
  });

  // test('calls setCampaignBadgeImage on badge image URL change', () => {
  //   render(<CampaignDetailsEditor {...defaultProps} />);
  //   const badgeInput = screen.getByLabelText(/Campaign Badge Image URL/i);
  //   fireEvent.change(badgeInput, { target: { value: 'http://newbadge.com/img.jpg' } });
  //   expect(mockSetCampaignBadgeImage).toHaveBeenCalledWith('http://newbadge.com/img.jpg');
  // });

  test('calls handleSaveCampaignDetails on save button click when changes are made', () => {
    // To enable the save button, change a prop that affects `hasUnsavedChanges`
    const modifiedProps = { ...defaultProps, editableTitle: "New Test Title" };
    render(<CampaignDetailsEditor {...modifiedProps} />);
    const saveButton = screen.getByRole('button', { name: /Save Details/i });
    expect(saveButton).not.toBeDisabled(); // Ensure button is enabled
    fireEvent.click(saveButton);
    expect(mockHandleSaveCampaignDetails).toHaveBeenCalledTimes(1);
  });
});
