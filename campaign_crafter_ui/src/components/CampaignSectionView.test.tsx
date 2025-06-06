import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CampaignSectionView from './CampaignSectionView';
import { generateTextLLM } from '../services/llmService'; // Corrected path
import { CampaignSection } from '../services/campaignService'; // Added for defaultProps

// Mock ../services/llmService
jest.mock('../services/llmService', () => ({
  ...jest.requireActual('../services/llmService'), // Preserve other exports
  generateTextLLM: jest.fn(),
}));

// Mock react-quill
// Variable to hold the last instance for tests to access
let lastMockedQuillInstance: any;

jest.mock('react-quill', () => {
  const ActualQuill = jest.requireActual('react-quill');
  const ReactInternal = jest.requireActual('react');

  const mockImplementation = (props: any) => {
    const [value, setValue] = ReactInternal.useState(props.value);
    ReactInternal.useEffect(() => {
      setValue(props.value);
    }, [props.value]);

    const instance = {
      getSelection: jest.fn(() => null),
      getText: jest.fn((index?: number, length?: number) => {
        const currentVal = props.value; // Use prop value for getText to reflect parent state
        if (index !== undefined && length !== undefined) {
          return currentVal.substring(index, index + length);
        }
        return currentVal;
      }),
      deleteText: jest.fn((index: number, length: number) => {
        const currentVal = props.value;
        const newValue = currentVal.substring(0, index) + currentVal.substring(index + length);
        // setValue(newValue); // Internal state for textarea if used
        props.onChange(newValue); // This is key for CampaignSectionView's state
      }),
      insertText: jest.fn((index: number, text: string) => {
        const currentVal = props.value;
        const newValue = currentVal.substring(0, index) + text + currentVal.substring(index);
        // setValue(newValue); // Internal state for textarea if used
        props.onChange(newValue); // This is key for CampaignSectionView's state
      }),
      getLength: jest.fn(() => props.value.length), // Use prop value for length
      root: { innerHTML: props.value }, // Use prop value
      setSelection: jest.fn(),
      on: jest.fn(),
      off: jest.fn(),
      enable: jest.fn(),
      disable: jest.fn(),
      focus: jest.fn(),
      blur: jest.fn(),
      getEditor: jest.fn(() => instance)
    };

    lastMockedQuillInstance = instance; // Store the instance

    if (props.ref) {
      if (typeof props.ref === 'function') {
        props.ref({ getEditor: () => instance });
      } else {
        props.ref.current = { getEditor: () => instance };
      }
    }

    ReactInternal.useEffect(() => {
        if (props.ref) {
            if (typeof props.ref === 'function') {
                props.ref({ getEditor: () => instance });
            } else {
                 props.ref.current = { getEditor: () => instance };
            }
        }
    }, [props.ref, instance]);

    return (
      <div data-testid="mock-quill-editor">
        <textarea
          value={props.value} // Controlled by parent's editedContent
          onChange={(e) => {
            // setValue(e.target.value); // No internal state needed for value, parent controls it
            props.onChange(e.target.value);
          }}
          data-testid="quill-textarea"
        />
      </div>
    );
  };

  const mock = jest.fn().mockImplementation(mockImplementation);

  // Static method to get the last instance
  (mock as any).getMostRecentQuillInstance = () => lastMockedQuillInstance;

  return {
    ...ActualQuill,
    __esModule: true,
    default: mock, // Use the jest.fn() mock directly
  };
});

// Import ReactQuill after the mock setup to get the mocked version
import ReactQuill from 'react-quill';

const mockedGenerateTextLLM = generateTextLLM as jest.MockedFunction<typeof generateTextLLM>;
// Helper to get the mocked Quill instance
const getMockedQuillInstance = () => (ReactQuill as any).getMostRecentQuillInstance();

const defaultProps: React.ComponentProps<typeof CampaignSectionView> = {
  section: { id: 1, title: 'Test Section', content: 'Initial content', order: 0, campaign_id: 1, type: 'text' }, // Added type
  onSave: jest.fn().mockResolvedValue(undefined),
  isSaving: false,
  saveError: null,
  onDelete: jest.fn(),
  forceCollapse: false,
};

describe('CampaignSectionView', () => {
  let mockQuillEditorInstance: any;

  beforeEach(() => {
    mockedGenerateTextLLM.mockClear();
    // Clear all method mocks on the quill instance before each test
    // This is important because the instance is reused across renders in tests if not careful
    // However, with getMostRecentQuillInstance, we get the one tied to the LATEST render.
    // If getMostRecentQuillInstance() itself is called, ensure its methods are clean.
    const currentInstance = getMockedQuillInstance();
    if (currentInstance) {
        Object.values(currentInstance).forEach(mockFn => {
            if (typeof mockFn === 'function' && 'mockClear' in mockFn) {
                (mockFn as jest.Mock).mockClear();
            }
        });
        // Specifically reset common ones to default behaviors for safety between tests
        currentInstance.getSelection.mockReturnValue(null);
        currentInstance.getText.mockImplementation((index?: number, length?: number) => {
            // This needs to access the component's actual 'editedContent' state via props
            // The mock setup for ReactQuill.default should handle this by reading props.value
            return defaultProps.section.content; // Fallback, ideally read from props
        });
    }
  });

  const renderAndEdit = (props = defaultProps) => {
    render(<CampaignSectionView {...props} />);
    const editButton = screen.getByRole('button', { name: /Edit Section Content/i });
    fireEvent.click(editButton);
    // Assign the latest mock instance after rendering and entering edit mode
    mockQuillEditorInstance = getMockedQuillInstance();
    // Ensure instance methods are callable, if instance exists
    if (mockQuillEditorInstance) {
        mockQuillEditorInstance.getText = mockQuillEditorInstance.getText || jest.fn();
        mockQuillEditorInstance.getSelection = mockQuillEditorInstance.getSelection || jest.fn();
        mockQuillEditorInstance.deleteText = mockQuillEditorInstance.deleteText || jest.fn();
        mockQuillEditorInstance.insertText = mockQuillEditorInstance.insertText || jest.fn();
        mockQuillEditorInstance.getLength = mockQuillEditorInstance.getLength || jest.fn(() => defaultProps.section.content.length);
    }
  };

  test('should display "Generate Content" button in edit mode and hide it otherwise', async () => {
    render(<CampaignSectionView {...defaultProps} />);

    // Initially, "Generate Content" button should not be visible
    expect(screen.queryByRole('button', { name: /Generate Content/i })).not.toBeInTheDocument();

    // Click the "Edit Section Content" button
    const editButton = screen.getByRole('button', { name: /Edit Section Content/i });
    fireEvent.click(editButton);

    // Wait for the editor to appear (and thus the "Generate Content" button)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Generate Content/i })).toBeVisible();
    });

    // Click "Cancel"
    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /Generate Content/i })).not.toBeInTheDocument();
    });
  });

  test('should disable "Generate Content" button and show "Generating..." text during content generation', async () => {
    renderAndEdit();

    mockedGenerateTextLLM.mockReturnValue(new Promise(() => {})); // Promise that never resolves

    const generateButton = screen.getByRole('button', { name: /Generate Content/i });
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(generateButton).toBeDisabled();
      expect(generateButton).toHaveTextContent('Generating...');
    });

    // Check other buttons are also disabled
    expect(screen.getByRole('button', { name: /Save Content/i})).toBeDisabled();
    expect(screen.getByRole('button', { name: /Generate Image/i})).toBeDisabled();
    expect(screen.getByRole('button', { name: /Cancel/i})).toBeDisabled();
  });

  test('should disable "Generate Content" button if isSaving is true', () => {
    renderAndEdit({ ...defaultProps, isSaving: true });

    const generateButton = screen.getByRole('button', { name: /Generate Content/i });
    expect(generateButton).toBeDisabled();
  });

  describe('API Calls and Context', () => {
    test('should call generateTextLLM with selected text as context and replace selection', async () => {
      renderAndEdit();

      const selectedText = "content";
      const selectionRange = { index: 8, length: selectedText.length }; // "Initial content"

      // Ensure mockQuillEditorInstance is available
      expect(mockQuillEditorInstance).toBeDefined();
      mockQuillEditorInstance.getSelection.mockReturnValue(selectionRange);
      // getText for selection is handled by the mock's direct props.value access now
      // mockQuillEditorInstance.getText.mockImplementation((index, length) => {
      //   if (index === selectionRange.index && length === selectionRange.length) {
      //     return selectedText;
      //   }
      //   return defaultProps.section.content; // fallback for other calls
      // });


      const generatedText = "Generated based on selection.";
      mockedGenerateTextLLM.mockResolvedValueOnce({ generated_text: generatedText, model_used: 'test-model' });

      const generateButton = screen.getByRole('button', { name: /Generate Content/i });
      fireEvent.click(generateButton);

      await waitFor(() => {
        expect(mockedGenerateTextLLM).toHaveBeenCalledWith(expect.objectContaining({
          prompt: expect.stringContaining(`Context: ${selectedText}`)
        }));
      });

      expect(mockQuillEditorInstance.deleteText).toHaveBeenCalledWith(selectionRange.index, selectionRange.length, 'user');
      expect(mockQuillEditorInstance.insertText).toHaveBeenCalledWith(selectionRange.index, generatedText, 'user');
      // Check that setEditedContent was called via onChange in the mock
      // This is implicitly tested by verifying deleteText/insertText which call props.onChange
    });

    test('should call generateTextLLM with full editor content if no text is selected and append', async () => {
      renderAndEdit({ ...defaultProps, section: { ...defaultProps.section, content: "Full text."}});

      expect(mockQuillEditorInstance).toBeDefined();
      mockQuillEditorInstance.getSelection.mockReturnValue(null); // No selection
      // getText for full content is handled by the mock's direct props.value access now
      // mockQuillEditorInstance.getText.mockReturnValue("Full text.");
      mockQuillEditorInstance.getLength.mockReturnValue("Full text.".length + 1); // Quill adds a newline

      const generatedText = "Generated based on full content.";
      mockedGenerateTextLLM.mockResolvedValueOnce({ generated_text: generatedText, model_used: 'test-model' });

      const generateButton = screen.getByRole('button', { name: /Generate Content/i });
      fireEvent.click(generateButton);

      await waitFor(() => {
        expect(mockedGenerateTextLLM).toHaveBeenCalledWith(expect.objectContaining({
          prompt: expect.stringContaining("Context: Full text.")
        }));
      });

      // Append means insert at end (Quill length - 1 because of the trailing newline)
      const expectedInsertPosition = "Full text.".length; // Length of "Full text."
      expect(mockQuillEditorInstance.insertText).toHaveBeenCalledWith(expectedInsertPosition, "\n" + generatedText, 'user');
    });
  });

  test('should display error message if generateTextLLM fails', async () => {
    renderAndEdit();

    mockedGenerateTextLLM.mockRejectedValueOnce(new Error('API Error'));

    const generateButton = screen.getByRole('button', { name: /Generate Content/i });
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to generate content. An error occurred./i)).toBeInTheDocument();
    });
  });

});
