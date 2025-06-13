import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AddMoodBoardImageModal, { AddMoodBoardImageModalProps } from './AddMoodBoardImageModal';

// Mock the child Modal component to simplify testing and focus on AddMoodBoardImageModal logic
jest.mock('../common/Modal', () => ({
  __esModule: true,
  default: ({ isOpen, onClose, title, children, size }: any) => {
    if (!isOpen) return null;
    return (
      <div data-testid="mock-modal" aria-label={title}>
        <button data-testid="mock-modal-close-button" onClick={onClose}>Close Mock Modal</button>
        <h1>{title}</h1>
        <div>{children}</div>
      </div>
    );
  },
}));

// Mock the image service for the upload flow to prevent actual API calls
jest.mock('../../services/imageService', () => ({
  uploadMoodboardImageApi: jest.fn(),
}));
import { uploadMoodboardImageApi } from '../../services/imageService';


describe('AddMoodBoardImageModal', () => {
  const mockOnClose = jest.fn();
  const mockOnAddUrl = jest.fn();
  const mockOnInitiateGenerateImage = jest.fn();
  const mockCampaignId = 'test-campaign-123';

  const defaultProps: AddMoodBoardImageModalProps = {
    isOpen: true,
    onClose: mockOnClose,
    onAddUrl: mockOnAddUrl,
    onInitiateGenerateImage: mockOnInitiateGenerateImage,
    campaignId: mockCampaignId,
    title: 'Add Image to Mood Board',
  };

  beforeEach(() => {
    // Clear mocks before each test
    mockOnClose.mockClear();
    mockOnAddUrl.mockClear();
    mockOnInitiateGenerateImage.mockClear();
    (uploadMoodboardImageApi as jest.Mock).mockClear();
  });

  const renderComponent = (props: Partial<AddMoodBoardImageModalProps> = {}) => {
    return render(<AddMoodBoardImageModal {...defaultProps} {...props} />);
  };

  test('renders initial choice view correctly', () => {
    renderComponent();
    expect(screen.getByText(defaultProps.title!)).toBeInTheDocument();
    expect(screen.getByText('Upload Image from Computer')).toBeInTheDocument();
    expect(screen.getByText('Generate New Image')).toBeInTheDocument();
    expect(screen.getByText('Add Image by URL')).toBeInTheDocument();
  });

  describe('"Add Image by URL" flow', () => {
    test('switches to URL input view, adds URL, and calls onClose', async () => {
      renderComponent();
      await userEvent.click(screen.getByText('Add Image by URL'));

      expect(screen.getByLabelText('Image URL')).toBeInTheDocument();
      expect(screen.getByText('Add URL')).toBeInTheDocument();
      expect(screen.getByText('Back')).toBeInTheDocument();

      const urlInput = screen.getByLabelText('Image URL');
      const testUrl = 'http://example.com/image.png';
      await userEvent.type(urlInput, testUrl);
      await userEvent.click(screen.getByText('Add URL'));

      expect(mockOnAddUrl).toHaveBeenCalledWith(testUrl);
      // The component calls onClose internally after successful add
      // For this mock setup, onClose is called by the component itself.
      // If it were the base Modal's close button, we'd click that.
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    test('validates URL and shows error for invalid URL', async () => {
      renderComponent();
      await userEvent.click(screen.getByText('Add Image by URL'));
      const urlInput = screen.getByLabelText('Image URL');
      await userEvent.type(urlInput, 'invalid-url');
      await userEvent.click(screen.getByText('Add URL'));

      expect(screen.getByText('Please enter a valid URL.')).toBeInTheDocument();
      expect(mockOnAddUrl).not.toHaveBeenCalled();
      expect(mockOnClose).not.toHaveBeenCalled();
    });

    test('navigates back to choice view from URL input view', async () => {
      renderComponent();
      await userEvent.click(screen.getByText('Add Image by URL'));
      expect(screen.getByLabelText('Image URL')).toBeInTheDocument(); // Ensure we are in pasteUrl view

      await userEvent.click(screen.getByText('Back'));
      expect(screen.getByText('Upload Image from Computer')).toBeInTheDocument(); // Back to choice view
    });
  });

  describe('"Upload Image from Computer" flow', () => {
    test('switches to upload view, enables button on file select, calls service and onClose', async () => {
      // Mock the upload service to resolve successfully
      (uploadMoodboardImageApi as jest.Mock).mockResolvedValue({ imageUrl: 'http://newly.uploaded/image.png', campaign: {} });

      renderComponent();
      await userEvent.click(screen.getByText('Upload Image from Computer'));

      const fileInput = screen.getByRole('button', {name: /upload image from computer/i}).parentElement?.querySelector('input[type="file"]');
      expect(fileInput).toBeInTheDocument(); // More robust way to find the input if no label
      if (!fileInput) throw new Error("File input not found");

      const uploadButton = screen.getByRole('button', { name: 'Upload' });
      expect(uploadButton).toBeDisabled();
      expect(screen.getByText('Back')).toBeInTheDocument();

      const testFile = new File(['hello'], 'hello.png', { type: 'image/png' });
      await userEvent.upload(fileInput, testFile);

      expect(screen.getByText(`Selected: ${testFile.name}`)).toBeInTheDocument();
      expect(uploadButton).not.toBeDisabled();

      await userEvent.click(uploadButton);

      expect(uploadMoodboardImageApi).toHaveBeenCalledWith(mockCampaignId, testFile);
      expect(mockOnAddUrl).toHaveBeenCalledWith('http://newly.uploaded/image.png');
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    test('shows error message if upload fails', async () => {
      const errorMessage = "Network Error";
      (uploadMoodboardImageApi as jest.Mock).mockRejectedValue(new Error(errorMessage));

      renderComponent();
      await userEvent.click(screen.getByText('Upload Image from Computer'));

      const fileInput = screen.getByRole('button', {name: /upload image from computer/i}).parentElement?.querySelector('input[type="file"]');
      if (!fileInput) throw new Error("File input not found");

      const testFile = new File(['hello'], 'hello.png', { type: 'image/png' });
      await userEvent.upload(fileInput, testFile);

      const uploadButton = screen.getByRole('button', { name: 'Upload' });
      await userEvent.click(uploadButton);

      expect(uploadMoodboardImageApi).toHaveBeenCalledWith(mockCampaignId, testFile);
      expect(await screen.findByText(errorMessage)).toBeInTheDocument(); // Error message is displayed
      expect(mockOnAddUrl).not.toHaveBeenCalled();
      expect(mockOnClose).not.toHaveBeenCalled(); // Modal should remain open to show error
    });

    test('navigates back to choice view from upload view', async () => {
      renderComponent();
      await userEvent.click(screen.getByText('Upload Image from Computer'));
      const fileInput = screen.getByRole('button', {name: /upload image from computer/i}).parentElement?.querySelector('input[type="file"]');
      expect(fileInput).toBeInTheDocument(); // In upload view

      await userEvent.click(screen.getByText('Back'));
      expect(screen.getByText('Add Image by URL')).toBeInTheDocument(); // Back to choice view
    });
  });

  describe('"Generate New Image" flow', () => {
    test('calls onInitiateGenerateImage and onClose', async () => {
      renderComponent();
      await userEvent.click(screen.getByText('Generate New Image'));

      expect(mockOnInitiateGenerateImage).toHaveBeenCalledTimes(1);
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  test('closing the modal resets the view to choice', async () => {
    const { rerender } = renderComponent();

    // Navigate to a different view
    await userEvent.click(screen.getByText('Add Image by URL'));
    expect(screen.getByLabelText('Image URL')).toBeInTheDocument();

    // Simulate closing the modal by calling onClose (as if from the base Modal)
    // In our mock, this is done by clicking the "Close Mock Modal" button
    await userEvent.click(screen.getByTestId('mock-modal-close-button'));
    expect(mockOnClose).toHaveBeenCalledTimes(1); // The modal's internal onClose is called

    // Re-open the modal
    rerender(<AddMoodBoardImageModal {...defaultProps} isOpen={true} />);

    // Should be back to choice view
    expect(screen.getByText('Upload Image from Computer')).toBeInTheDocument();
    expect(screen.getByText('Generate New Image')).toBeInTheDocument();
    expect(screen.getByText('Add Image by URL')).toBeInTheDocument();
    expect(screen.queryByLabelText('Image URL')).not.toBeInTheDocument(); // URL input should not be visible
  });
});
