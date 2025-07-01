import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CampaignSectionView from './CampaignSectionView';
import { generateTextLLM } from '../services/llmService'; // Corrected path
import { CampaignSection } from '../types/campaignTypes'; // Corrected import path

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
import * as featureService from '../services/featureService';
import { Feature } from '../types/featureTypes';

// Mock featureService
jest.mock('../services/featureService');

const mockedGenerateTextLLM = generateTextLLM as jest.MockedFunction<typeof generateTextLLM>;
const mockedGetFeatures = featureService.getFeatures as jest.MockedFunction<typeof featureService.getFeatures>;

// Helper to get the mocked Quill instance
const getMockedQuillInstance = () => (ReactQuill as any).getMostRecentQuillInstance() as MockQuillInstance | undefined;

const defaultProps: React.ComponentProps<typeof CampaignSectionView> = {
  section: { id: 1, title: 'Test Section', content: 'Initial content', order: 0, campaign_id: 1, type: 'generic' }, // Added type as it's part of CampaignSection
  onSave: jest.fn().mockResolvedValue(undefined),
  isSaving: false,
  saveError: null,
  onDelete: jest.fn(),
  forceCollapse: false,
  campaignId: 1, // Assuming campaignId is number
  onSectionUpdated: jest.fn(),
  // onSectionTypeUpdate: jest.fn(), // Optional, add if tests require it
  expandSectionId: null, // <--- Add this line
  // onSetThematicImageFromSection: jest.fn(), // Optional, add if tests require it
};

describe('CampaignSectionView', () => {
  let mockQuillEditorInstance: any;

  beforeEach(() => {
    mockedGenerateTextLLM.mockClear();
    mockedGetFeatures.mockClear(); // Clear features mock
    mockLastQuillInstance = undefined;
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

  describe('API Calls, Context, and Text Insertion Logic', () => {
    test('inserts generated text after selection (no deletion)', async () => {
      renderAndEdit();
      const currentMockInstance = getMockedQuillInstance();
      expect(currentMockInstance).toBeDefined();

      const initialContent = defaultProps.section.content; // "Initial content"
      const selectedText = "content";
      const selectionStartIndex = initialContent.indexOf(selectedText);
      const selectionRange = { index: selectionStartIndex, length: selectedText.length };

      currentMockInstance!.getSelection.mockReturnValue(selectionRange); // Simulate this was the selection when "Generate" was clicked
      currentMockInstance!.getText // Simulate getText for context
        .mockImplementation((index?: number, length?: number) => {
          if (index === selectionRange.index && length === selectionRange.length) return selectedText;
          return initialContent;
        });

      const generatedText = "newly generated ideas";
      mockedGenerateTextLLM.mockResolvedValueOnce({ text: generatedText, model_used: 'test-model' });

      fireEvent.click(screen.getByRole('button', { name: /Generate Content/i }));

      await waitFor(() => expect(mockedGenerateTextLLM).toHaveBeenCalled());

      expect(currentMockInstance!.deleteText).not.toHaveBeenCalled(); // Key assertion: no deletion

      const expectedInsertionPoint = selectionRange.index + selectionRange.length;
      const expectedTextToInsert = " " + generatedText;
      expect(currentMockInstance!.insertText).toHaveBeenCalledWith(
        expectedInsertionPoint,
        expectedTextToInsert,
        'user'
      );
      expect(currentMockInstance!.setSelection).toHaveBeenCalledWith(
        expectedInsertionPoint + expectedTextToInsert.length,
        0,
        'user'
      );
    });

    test('inserts text at current cursor if no initial selection (with space heuristic)', async () => {
      const initialFullContent = "Some initial text.";
      renderAndEdit({ ...defaultProps, section: { ...defaultProps.section, content: initialFullContent }});
      const currentMockInstance = getMockedQuillInstance();
      expect(currentMockInstance).toBeDefined();

      // Simulate no initial selection when "Generate" was clicked (for context gathering)
      currentMockInstance!.getSelection.mockReturnValueOnce(null);
      currentMockInstance!.getText.mockReturnValueOnce(initialFullContent); // For context

      // Simulate current cursor position for insertion
      const cursorPosition = 5; // e.g., after "Some "
      currentMockInstance!.getSelection.mockReturnValueOnce({ index: cursorPosition, length: 0 });
      // For the space heuristic (getText(insertionPoint - 1, 1))
      currentMockInstance!.getText.mockImplementation((index?: number, length?: number) => {
        if (index === cursorPosition -1 && length === 1) return initialFullContent.charAt(cursorPosition -1); // char before cursor
        return initialFullContent;
      });


      const generatedText = "inserted stuff";
      mockedGenerateTextLLM.mockResolvedValueOnce({ text: generatedText, model_used: 'test-model' });

      fireEvent.click(screen.getByRole('button', { name: /Generate Content/i }));

      await waitFor(() => expect(mockedGenerateTextLLM).toHaveBeenCalled());

      // Heuristic: if char before cursor is not space, prepend space. 'e' is not a space.
      const expectedTextWithSpace = " " + generatedText;
      expect(currentMockInstance!.insertText).toHaveBeenCalledWith(
        cursorPosition,
        expectedTextWithSpace,
        'user'
      );
      expect(currentMockInstance!.setSelection).toHaveBeenCalledWith(
        cursorPosition + expectedTextWithSpace.length,
        0,
        'user'
      );
    });
  });

  describe('Feature Integration', () => {
    const mockFeatures: Feature[] = [
      { id: 1, name: 'Summarize', template: 'Summarize this: {}' },
      { id: 2, name: 'Explain', template: 'Explain this simply: {}' },
      { id: 3, name: 'Brainstorm Ideas (No Placeholder)', template: 'Brainstorm some cool ideas.' },
    ];

    test('feature dropdown is visible and loads features in edit mode', async () => {
      mockedGetFeatures.mockResolvedValueOnce([]);
      render(<CampaignSectionView {...defaultProps} />);

      expect(screen.queryByRole('combobox')).not.toBeInTheDocument(); // Using a generic role for select

      fireEvent.click(screen.getByRole('button', { name: /Edit Section Content/i }));

      await waitFor(() => expect(mockedGetFeatures).toHaveBeenCalledTimes(1));

      const featureSelect = screen.getByRole('combobox'); // More specific after edit mode
      expect(featureSelect).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /-- No Specific Feature --/i })).toBeInTheDocument();
    });

    test('feature dropdown populates and allows selection', async () => {
      mockedGetFeatures.mockResolvedValueOnce(mockFeatures);
      renderAndEdit(); // Enters edit mode and calls getFeatures via useEffect

      await waitFor(() => expect(screen.getByRole('option', { name: 'Summarize' })).toBeInTheDocument());
      expect(screen.getByRole('option', { name: 'Explain' })).toBeInTheDocument();

      const featureSelect = screen.getByRole('combobox');
      fireEvent.change(featureSelect, { target: { value: '1' } }); // Select "Summarize" by its ID

      // Check if selectedFeatureId state updated (indirectly by checking select's value)
      expect((featureSelect as HTMLSelectElement).value).toBe('1');
    });

    test('displays error if feature fetching fails', async () => {
      mockedGetFeatures.mockRejectedValueOnce(new Error('Failed to fetch features'));
      renderAndEdit();

      await waitFor(() => expect(screen.getByText(/An unknown error occurred while fetching features./i)).toBeInTheDocument());
    });
  });

  describe('Prompt Construction with Features', () => {
    const mockFeatures: Feature[] = [
      { id: 1, name: 'Summarize', template: 'Summarize: {}' },
      { id: 2, name: 'Brainstorm Ideas', template: 'Brainstorm some ideas about dragons.' },
    ];

    beforeEach(() => {
        mockedGetFeatures.mockResolvedValue(mockFeatures); // Provide features for all tests in this suite
    });

    test('uses feature template with placeholder and context text', async () => {
        renderAndEdit();
        const currentMockInstance = getMockedQuillInstance();
        expect(currentMockInstance).toBeDefined();

        await waitFor(() => expect(screen.getByRole('option', { name: 'Summarize' })).toBeInTheDocument());
        fireEvent.change(screen.getByRole('combobox'), { target: { value: '1' } }); // Select "Summarize"

        const selectedText = "some context to summarize";
        currentMockInstance!.getSelection.mockReturnValue({ index: 0, length: selectedText.length });
        currentMockInstance!.getText.mockReturnValue(selectedText);
        mockedGenerateTextLLM.mockResolvedValueOnce({ text: 'Generated summary.', model_used: 'test' });

        fireEvent.click(screen.getByRole('button', { name: /Generate Content/i }));

        await waitFor(() => expect(mockedGenerateTextLLM).toHaveBeenCalledWith(expect.objectContaining({
            prompt: "Summarize: some context to summarize"
        })));
    });

    test('uses feature template without placeholder (ignores context text)', async () => {
        renderAndEdit();
        const currentMockInstance = getMockedQuillInstance();
        expect(currentMockInstance).toBeDefined();

        await waitFor(() => expect(screen.getByRole('option', { name: 'Brainstorm Ideas' })).toBeInTheDocument());
        fireEvent.change(screen.getByRole('combobox'), { target: { value: '2' } });

        currentMockInstance!.getSelection.mockReturnValue({ index: 0, length: 10 }); // Some selection
        currentMockInstance!.getText.mockReturnValue("this should be ignored"); // This text will be ignored
        mockedGenerateTextLLM.mockResolvedValueOnce({ text: 'Dragon ideas.', model_used: 'test' });

        fireEvent.click(screen.getByRole('button', { name: /Generate Content/i }));

        await waitFor(() => expect(mockedGenerateTextLLM).toHaveBeenCalledWith(expect.objectContaining({
            prompt: "Brainstorm some ideas about dragons."
        })));
    });

    test('uses default prompt if no feature selected', async () => {
        renderAndEdit(); // Features will be loaded, but none selected by default
        const currentMockInstance = getMockedQuillInstance();
        expect(currentMockInstance).toBeDefined();

        const contextText = "some context";
        currentMockInstance!.getSelection.mockReturnValue(null); // No selection, use full text
        currentMockInstance!.getText.mockReturnValue(contextText); // Full text is "some context"
        mockedGenerateTextLLM.mockResolvedValueOnce({ text: 'Generated.', model_used: 'test' });

        // Ensure no feature is selected (value should be "")
        expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe("");

        fireEvent.click(screen.getByRole('button', { name: /Generate Content/i }));

        await waitFor(() => expect(mockedGenerateTextLLM).toHaveBeenCalledWith(expect.objectContaining({
            prompt: `Generate content based on the following context: ${contextText}`
        })));
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
