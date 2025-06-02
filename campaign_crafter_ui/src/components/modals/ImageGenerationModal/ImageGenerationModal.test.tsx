import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ImageGenerationModal from './ImageGenerationModal';
import apiClient from '../../../services/api apiClient'; // Path to your apiClient

// Helper function (copy from component or import if exported)
const sanitizeFilename = (text: string, maxLength = 50): string => {
  if (!text) return "generated_image";
  const sanitized = text
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .slice(0, 5)
    .join('_')
    .replace(/[^\w.-]/g, '')
    .substring(0, maxLength);
  return sanitized || "generated_image";
};

// Mock apiClient
jest.mock('../../../services/apiClient');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

// Mock navigator.clipboard
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: jest.fn().mockResolvedValue(undefined),
  },
  writable: true,
});

describe('ImageGenerationModal', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    // Clear mocks before each test
    mockOnClose.mockClear();
    mockedApiClient.post.mockClear();
    (navigator.clipboard.writeText as jest.Mock).mockClear();

    // Clear spies
    jest.restoreAllMocks();
  });

  test('renders correctly when open', () => {
    render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Generate Image')).toBeInTheDocument(); // Modal title
    expect(screen.getByLabelText('Prompt:')).toBeInTheDocument();
    expect(screen.getByLabelText('Model:')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Generate' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Copy URL' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Download' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument();
  });

  test('initial state is correct', () => {
    render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByLabelText('Prompt:')).toHaveValue('');
    expect(screen.getByLabelText('Model:')).toHaveValue('dall-e');
    expect(screen.getByRole('button', { name: 'Generate' })).toBeDisabled(); // Disabled because prompt is empty
    expect(screen.getByRole('button', { name: 'Copy URL' })).toBeDisabled(); // Disabled because no image URL
    expect(screen.getByRole('button', { name: 'Download' })).toBeDisabled(); // Disabled because no image URL
    expect(screen.getByText('Image will appear here')).toBeInTheDocument();
  });

  test('enables Generate button when prompt is entered', () => {
    render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
    fireEvent.change(screen.getByLabelText('Prompt:'), { target: { value: 'A test prompt' } });
    expect(screen.getByRole('button', { name: 'Generate' })).toBeEnabled();
  });

  test('shows error if Generate is clicked with empty prompt', () => {
    render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
    // Ensure prompt is empty or only whitespace
    fireEvent.change(screen.getByLabelText('Prompt:'), { target: { value: '   ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }));
    expect(screen.getByText('Prompt cannot be empty.')).toBeInTheDocument();
    expect(mockedApiClient.post).not.toHaveBeenCalled();
  });

  test('calls API on Generate click and displays image on success', async () => {
    const testPrompt = 'A test prompt';
    const mockApiResponse = {
      data: {
        image_url: 'http://example.com/generated_image.png',
        prompt_used: testPrompt,
        model_used: 'dall-e',
        size_used: '1024x1024',
      },
    };
    mockedApiClient.post.mockResolvedValue(mockApiResponse);

    render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);

    fireEvent.change(screen.getByLabelText('Prompt:'), { target: { value: testPrompt } });
    fireEvent.change(screen.getByLabelText('Model:'), { target: { value: 'dall-e' } });
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

    expect(screen.getByText('Generating image...')).toBeInTheDocument();
    expect(mockedApiClient.post).toHaveBeenCalledWith('/api/v1/images/generate', { // Corrected path
      prompt: testPrompt,
      model: 'dall-e',
    });

    await waitFor(() => {
      expect(screen.getByRole('img', { name: 'Generated' })).toHaveAttribute('src', mockApiResponse.data.image_url);
    });
    expect(screen.getByRole('button', { name: 'Copy URL' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Download' })).toBeEnabled();
    // Check that the URL string itself is NOT directly displayed
    expect(screen.queryByText(mockApiResponse.data.image_url)).not.toBeInTheDocument();
  });

  test('displays error message on API failure', async () => {
    const errorMessage = 'Network error: Could not connect to the server.';
    mockedApiClient.post.mockRejectedValue({ message: 'Network Error', request: {} }); // Simulate network error

    render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
    fireEvent.change(screen.getByLabelText('Prompt:'), { target: { value: 'A test prompt' } });
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

    expect(screen.getByText('Generating image...')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Copy URL' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Download' })).toBeDisabled();
  });

  test('displays API error detail from response', async () => {
    const errorDetail = "Invalid prompt content policy violation";
    mockedApiClient.post.mockRejectedValue({
      response: { data: { detail: errorDetail } }
    });

    render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
    fireEvent.change(screen.getByLabelText('Prompt:'), { target: { value: 'A problematic prompt' } });
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

    await waitFor(() => {
      expect(screen.getByText(`API Error: ${errorDetail}`)).toBeInTheDocument();
    });
  });

  describe('Copy URL button functionality', () => {
    test('is enabled and copies HTTP URL', async () => {
      const httpImageUrl = 'http://example.com/image.png';
      mockedApiClient.post.mockResolvedValue({ data: { image_url: httpImageUrl } });
      render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
      fireEvent.change(screen.getByLabelText('Prompt:'), { target: { value: 'http url test' } });
      fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

      await waitFor(() => expect(screen.getByRole('img')).toBeInTheDocument());

      const copyButton = screen.getByRole('button', { name: 'Copy URL' });
      expect(copyButton).toBeEnabled();
      fireEvent.click(copyButton);
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(httpImageUrl);
    });

    test('is disabled for Data URL', async () => {
      const dataImageUrl = 'data:image/webp;base64,dGVzdA==';
      mockedApiClient.post.mockResolvedValue({ data: { image_url: dataImageUrl } });
      render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
      fireEvent.change(screen.getByLabelText('Prompt:'), { target: { value: 'data url test' } });
      fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

      await waitFor(() => expect(screen.getByRole('img')).toBeInTheDocument());

      const copyButton = screen.getByRole('button', { name: 'Copy URL' });
      expect(copyButton).toBeDisabled();
    });
  });

  test('closes modal when Close button is clicked', () => {
    render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  test('resets state on open', () => {
    const { rerender } = render(<ImageGenerationModal isOpen={false} onClose={mockOnClose} />);
    // Simulate it being opened, then having state changed, then closed, then reopened
    rerender(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
    fireEvent.change(screen.getByLabelText('Prompt:'), { target: { value: 'Initial prompt' } });
    // Simulate generation
    mockedApiClient.post.mockResolvedValue({ data: { image_url: 'http://example.com/img1.png' }});
    fireEvent.click(screen.getByRole('button', {name: "Generate"}));

    // Wait for first generation to "complete" to set state like generatedImageUrl
    return waitFor(() => {
        expect(screen.getByRole('img')).toBeInTheDocument();
      }).then(() => {
        rerender(<ImageGenerationModal isOpen={false} onClose={mockOnClose} />); // Close it
        rerender(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />); // Reopen

        expect(screen.getByLabelText('Prompt:')).toHaveValue('');
        expect(screen.getByLabelText('Model:')).toHaveValue('dall-e');
        expect(screen.queryByRole('img')).not.toBeInTheDocument();
        expect(screen.getByText('Image will appear here')).toBeInTheDocument();
        expect(screen.queryByText('API Error:')).not.toBeInTheDocument(); // Error should be cleared
      });
  });

  describe('Download button functionality', () => {
    const testPrompt = "A beautiful landscape painting";
    const sanitizedTestPrompt = sanitizeFilename(testPrompt); // "a_beautiful_landscape_painting"

    const setupGeneratedImageWithPrompt = async (imageUrl: string) => {
      mockedApiClient.post.mockResolvedValue({
        data: { image_url: imageUrl, prompt_used: testPrompt, model_used: 'dall-e', size_used: '512x512' }
      });
      render(<ImageGenerationModal isOpen={true} onClose={mockOnClose} />);
      // Simulate user typing the prompt
      fireEvent.change(screen.getByLabelText('Prompt:'), { target: { value: testPrompt } });
      fireEvent.click(screen.getByRole('button', { name: 'Generate' }));
      await waitFor(() => expect(screen.getByRole('img', { name: 'Generated' })).toBeInTheDocument());
    };

    test('downloads an HTTP URL image with sanitized filename', async () => {
      const httpImageUrl = 'http://example.com/some/path/image.jpeg?query=param';
      await setupGeneratedImageWithPrompt(httpImageUrl);

      const createElementSpy = jest.spyOn(document, 'createElement');
      const anchorClickSpy = jest.fn();

      createElementSpy.mockImplementation(() => ({
        href: '',
        download: '',
        style: { display: '' },
        click: anchorClickSpy,
        remove: jest.fn(),
      } as any));

      const appendChildSpy = jest.spyOn(document.body, 'appendChild').mockImplementation(() => ({} as Node));
      const removeChildSpy = jest.spyOn(document.body, 'removeChild').mockImplementation(() => ({} as Node));

      fireEvent.click(screen.getByRole('button', { name: 'Download' }));

      expect(createElementSpy).toHaveBeenCalledWith('a');
      const mockedAnchor = createElementSpy.mock.results[0].value;
      expect(mockedAnchor.href).toBe(httpImageUrl);
      expect(mockedAnchor.download).toBe(`${sanitizedTestPrompt}.jpeg`); // Sanitized name + original extension
      expect(anchorClickSpy).toHaveBeenCalledTimes(1);

      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });

    test('downloads a Data URL image (webp) with sanitized filename', async () => {
      const base64Content = 'dGVzdGluZ1dlYnA='; // "testingWebp"
      const dataImageUrl = `data:image/webp;base64,${base64Content}`;
      await setupGeneratedImageWithPrompt(dataImageUrl);

      const mockBlob = new Blob([Buffer.from(base64Content, 'base64')], { type: 'image/webp' });
      const mockObjectUrl = 'blob:http://localhost/mock-object-url';

      const fetchSpy = jest.spyOn(window, 'fetch').mockResolvedValue(new Response(mockBlob));
      const createObjectURLSpy = jest.spyOn(window.URL, 'createObjectURL').mockReturnValue(mockObjectUrl);
      const revokeObjectURLSpy = jest.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});

      const createElementSpy = jest.spyOn(document, 'createElement');
      const anchorClickSpy = jest.fn();
      createElementSpy.mockImplementation(() => ({
        href: '',
        download: '',
        style: { display: '' },
        click: anchorClickSpy,
        remove: jest.fn(),
      } as any));
      const appendChildSpy = jest.spyOn(document.body, 'appendChild').mockImplementation(() => ({} as Node));
      const removeChildSpy = jest.spyOn(document.body, 'removeChild').mockImplementation(() => ({} as Node));

      fireEvent.click(screen.getByRole('button', { name: 'Download' }));

      await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith(dataImageUrl));
      await waitFor(() => expect(createObjectURLSpy).toHaveBeenCalledWith(expect.any(Blob)));

      const mockedAnchor = createElementSpy.mock.results[0].value;
      expect(mockedAnchor.href).toBe(mockObjectUrl);
      expect(mockedAnchor.download).toBe(`${sanitizedTestPrompt}.webp`); // Sanitized name + extension from blob type
      expect(anchorClickSpy).toHaveBeenCalledTimes(1);
      expect(revokeObjectURLSpy).toHaveBeenCalledWith(mockObjectUrl);

      fetchSpy.mockRestore();
      createObjectURLSpy.mockRestore();
      revokeObjectURLSpy.mockRestore();
      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });

    test('handles error when creating blob from data URL during download', async () => {
      const dataImageUrl = `data:image/png;base64,problematic`;
      await setupGeneratedImageWithPrompt(dataImageUrl); // Prompt is set here

      const fetchSpy = jest.spyOn(window, 'fetch').mockResolvedValue({
        blob: () => Promise.reject(new Error('Blob creation failed')),
      } as any);
      const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});

      fireEvent.click(screen.getByRole('button', { name: 'Download' }));

      await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith(dataImageUrl));
      await waitFor(() => expect(alertSpy).toHaveBeenCalledWith('Failed to prepare image for download.'));

      fetchSpy.mockRestore();
      alertSpy.mockRestore();
    });
  });
});
