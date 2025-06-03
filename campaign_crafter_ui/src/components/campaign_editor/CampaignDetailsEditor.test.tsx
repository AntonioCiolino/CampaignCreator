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
  });

  const mockSetEditableTitle = jest.fn();
  const mockSetInitialPrompt = jest.fn();
  const mockSetCampaignBadgeImage = jest.fn();
  const mockHandleSaveCampaignDetails = jest.fn();

  const defaultProps = {
    editableTitle: 'Test Title',
    setEditableTitle: mockSetEditableTitle,
    initialPrompt: 'Test Prompt',
    setInitialPrompt: mockSetInitialPrompt,
    campaignBadgeImage: '',
    setCampaignBadgeImage: mockSetCampaignBadgeImage,
    handleSaveCampaignDetails: mockHandleSaveCampaignDetails,
  };

  test('renders correctly with basic props', () => {
    render(<CampaignDetailsEditor {...defaultProps} />);

    expect(screen.getByLabelText(/Campaign Title/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Title')).toBeInTheDocument();

    expect(screen.getByLabelText(/Initial Prompt/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Prompt')).toBeInTheDocument();

    expect(screen.getByLabelText(/Campaign Badge Image URL/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Save Details/i })).toBeInTheDocument();
  });

  test('renders badge preview when campaignBadgeImage is provided', () => {
    render(<CampaignDetailsEditor {...defaultProps} campaignBadgeImage="http://example.com/badge.png" />);
    const image = screen.getByAltText('Campaign Badge Preview');
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

  test('calls setCampaignBadgeImage on badge image URL change', () => {
    render(<CampaignDetailsEditor {...defaultProps} />);
    const badgeInput = screen.getByLabelText(/Campaign Badge Image URL/i);
    fireEvent.change(badgeInput, { target: { value: 'http://newbadge.com/img.jpg' } });
    expect(mockSetCampaignBadgeImage).toHaveBeenCalledWith('http://newbadge.com/img.jpg');
  });

  test('calls handleSaveCampaignDetails on save button click', () => {
    render(<CampaignDetailsEditor {...defaultProps} />);
    const saveButton = screen.getByRole('button', { name: /Save Details/i });
    fireEvent.click(saveButton);
    expect(mockHandleSaveCampaignDetails).toHaveBeenCalledTimes(1);
  });
});
