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

// Define MockQuillInstance at the top level
interface MockQuillInstance {
  getSelection: jest.Mock<any, any>;
  getText: jest.Mock<any, any>;
  deleteText: jest.Mock<any, any>;
  insertText: jest.Mock<any, any>;
  getLength: jest.Mock<any, any>;
  root: { innerHTML: string };
  setSelection: jest.Mock<any, any>;
  on: jest.Mock<any, any>;
  off: jest.Mock<any, any>;
  enable: jest.Mock<any,any>;
  disable: jest.Mock<any,any>;
  focus: jest.Mock<any,any>;
  blur: jest.Mock<any,any>;
  getEditor: jest.Mock<any,any>;
}

// Mock react-quill
// Variable to hold the last instance for tests to access, prefixed with "mock"
let mockLastQuillInstance: MockQuillInstance | undefined;

jest.mock('react-quill', () => {
  const ActualQuill = jest.requireActual('react-quill');
  const ReactInternal = jest.requireActual('react');

  // This is the actual component React will render
  const ForwardRefQuillMock = ReactInternal.forwardRef((props: any, ref: any) => {
    // Memoize the instance to ensure stability.
    // Its methods will close over the props from when it's created/updated.
    const instance = ReactInternal.useMemo(() => {
      const inst: MockQuillInstance = {
        getSelection: jest.fn(() => null),
        getText: jest.fn((index?: number, length?: number) => {
          const currentVal = props.value;
          if (index !== undefined && length !== undefined) {
            return currentVal.substring(index, index + length);
          }
          return currentVal;
        }),
        deleteText: jest.fn((index: number, length: number) => {
          const currentVal = props.value;
          const newValue = currentVal.substring(0, index) + currentVal.substring(index + length);
          props.onChange(newValue);
        }),
        insertText: jest.fn((index: number, text: string) => {
          const currentVal = props.value;
          const newValue = currentVal.substring(0, index) + text + currentVal.substring(index);
          props.onChange(newValue);
        }),
        getLength: jest.fn(() => props.value.length),
        root: { innerHTML: props.value },
        setSelection: jest.fn(),
        on: jest.fn(),
        off: jest.fn(),
        enable: jest.fn(),
        disable: jest.fn(),
        focus: jest.fn(),
        blur: jest.fn(),
        getEditor: jest.fn(() => inst) // Important: inst refers to this memoized object, and getEditor is a jest.Mock
      };
      return inst;
    }, [props.value, props.onChange]); // Dependencies for when the instance itself should be re-memoized

    mockLastQuillInstance = instance;

    // Expose the memoized instance through the ref.
    // The dependency array [instance] ensures useImperativeHandle updates if the instance itself changes.
    ReactInternal.useImperativeHandle(ref, () => instance, [instance]);

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
  });

  // Add the static method to the ForwardRefQuillMock component itself
  (ForwardRefQuillMock as any).getMostRecentQuillInstance = () => mockLastQuillInstance;

  return {
    ...ActualQuill,
    __esModule: true,
    default: ForwardRefQuillMock, // Export the forwardRef component directly
    Quill: ActualQuill.Quill, // Preserve Quill static if needed elsewhere, though not used in current tests
  };
});

// Import ReactQuill after the mock setup to get the mocked version
import ReactQuill from 'react-quill';

const mockedGenerateTextLLM = generateTextLLM as jest.MockedFunction<typeof generateTextLLM>;
// Helper to get the mocked Quill instance
const getMockedQuillInstance = () => (ReactQuill as any).getMostRecentQuillInstance() as MockQuillInstance | undefined; // Added type cast

const defaultProps: React.ComponentProps<typeof CampaignSectionView> = {
  section: { id: 1, title: 'Test Section', content: 'Initial content', order: 0, campaign_id: 1 }, // Removed type property
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
    mockLastQuillInstance = undefined; // Explicitly reset the shared mock instance storage for each test
  });

  const renderAndEdit = (props = defaultProps) => {
    render(<CampaignSectionView {...props} />);
    const editButton = screen.getByRole('button', { name: /Edit Section Content/i });
    fireEvent.click(editButton);
    // Assign the latest mock instance after rendering and entering edit mode
    mockQuillEditorInstance = getMockedQuillInstance();
    // Ensure instance methods are callable, if instance exists
    // The instance methods are already jest.fn() from the mock definition.
    // No need to re-assign or check if they exist here.
    // mockQuillEditorInstance = getMockedQuillInstance(); // Already assigned
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
      const currentMockInstance = getMockedQuillInstance();

      const selectedText = "content";
      const selectionRange = { index: 8, length: selectedText.length }; // "Initial content"

      expect(currentMockInstance).toBeDefined();
      currentMockInstance!.getSelection.mockReturnValue(selectionRange);


      const generatedText = "Generated based on selection.";
      mockedGenerateTextLLM.mockResolvedValueOnce({ text: generatedText, model_used: 'test-model' }); // Changed generated_text to text

      const generateButton = screen.getByRole('button', { name: /Generate Content/i });
      fireEvent.click(generateButton);

      await waitFor(() => {
        expect(mockedGenerateTextLLM).toHaveBeenCalledWith(expect.objectContaining({
          prompt: expect.stringContaining(`Context: ${selectedText}`)
        }));
      });

      expect(currentMockInstance!.deleteText).toHaveBeenCalledWith(selectionRange.index, selectionRange.length, 'user');
      expect(currentMockInstance!.insertText).toHaveBeenCalledWith(selectionRange.index, generatedText, 'user');
    });

    test('should call generateTextLLM with full editor content if no text is selected and append', async () => {
      renderAndEdit({ ...defaultProps, section: { ...defaultProps.section, content: "Full text."}});
      const currentMockInstance = getMockedQuillInstance();

      expect(currentMockInstance).toBeDefined();
      currentMockInstance!.getSelection.mockReturnValue(null); // No selection
      currentMockInstance!.getLength.mockReturnValue("Full text.".length + 1); // Quill adds a newline


      const generatedText = "Generated based on full content.";
      mockedGenerateTextLLM.mockResolvedValueOnce({ text: generatedText, model_used: 'test-model' }); // Changed generated_text to text

      const generateButton = screen.getByRole('button', { name: /Generate Content/i });
      fireEvent.click(generateButton);

      await waitFor(() => {
        expect(mockedGenerateTextLLM).toHaveBeenCalledWith(expect.objectContaining({
          prompt: expect.stringContaining("Context: Full text.")
        }));
      });

      const expectedInsertPosition = "Full text.".length;
      expect(currentMockInstance!.insertText).toHaveBeenCalledWith(expectedInsertPosition, "\n" + generatedText, 'user');
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
