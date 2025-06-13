import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MoodBoardPanel, { MoodBoardPanelProps } from './MoodBoardPanel';
import { DragEndEvent } from '@dnd-kit/core';

// Mock dnd-kit components and hooks
// We are not testing dnd-kit itself, but our logic around it.
jest.mock('@dnd-kit/core', () => ({
  ...jest.requireActual('@dnd-kit/core'), // Import and retain default behavior
  DndContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useSensor: jest.fn(),
  useSensors: jest.fn(),
  closestCenter: jest.fn(),
}));

jest.mock('@dnd-kit/sortable', () => ({
  ...jest.requireActual('@dnd-kit/sortable'),
  SortableContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useSortable: jest.fn(() => ({
    attributes: {},
    listeners: {},
    setNodeRef: jest.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  })),
  sortableKeyboardCoordinates: jest.fn(),
  rectSortingStrategy: jest.fn(),
})
);

// Mock image upload service
jest.mock('../../services/imageService', () => ({
  uploadImage: jest.fn(),
}));


const mockOnUpdateMoodBoardUrls = jest.fn();
const mockOnClose = jest.fn();
const mockOnRequestOpenGenerateImageModal = jest.fn();

const defaultProps: MoodBoardPanelProps = {
  moodBoardUrls: [],
  isLoading: false,
  error: null,
  onClose: mockOnClose,
  isVisible: true,
  title: 'Test Mood Board',
  onUpdateMoodBoardUrls: mockOnUpdateMoodBoardUrls,
  campaignId: 'test-campaign-id',
  onRequestOpenGenerateImageModal: mockOnRequestOpenGenerateImageModal,
};

describe('MoodBoardPanel', () => {
  beforeEach(() => {
    // Clear mock calls before each test
    jest.clearAllMocks();
    // Reset sensors mock for dnd-kit to a basic implementation
    (jest.requireMock('@dnd-kit/core').useSensors as jest.Mock).mockReturnValue(undefined);
     // Reset useSortable mock
     (jest.requireMock('@dnd-kit/sortable').useSortable as jest.Mock).mockImplementation(() => ({
        attributes: {},
        listeners: {},
        setNodeRef: jest.fn(),
        transform: null,
        transition: null,
        isDragging: false,
      }));
  });

  test('renders correctly when visible', () => {
    render(<MoodBoardPanel {...defaultProps} />);
    expect(screen.getByText('Test Mood Board')).toBeInTheDocument();
    expect(screen.getByLabelText('Close mood board')).toBeInTheDocument();
    expect(screen.getByLabelText('Add new image to mood board')).toBeInTheDocument();
  });

  test('does not render when isVisible is false', () => {
    render(<MoodBoardPanel {...defaultProps} isVisible={false} />);
    expect(screen.queryByText('Test Mood Board')).not.toBeInTheDocument();
  });

  test('shows loading message when isLoading is true', () => {
    render(<MoodBoardPanel {...defaultProps} isLoading={true} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('shows error message when error prop is provided', () => {
    render(<MoodBoardPanel {...defaultProps} error="Test error message" />);
    expect(screen.getByText('Error: Test error message')).toBeInTheDocument();
  });

  test('shows "no images" message when moodBoardUrls is empty and not loading/error', () => {
    render(<MoodBoardPanel {...defaultProps} moodBoardUrls={[]} />);
    expect(screen.getByText('No mood board images added yet.')).toBeInTheDocument();
  });

  test('renders mood board items when moodBoardUrls are provided', () => {
    const urls = ['url1.jpg', 'url2.jpg'];
    render(<MoodBoardPanel {...defaultProps} moodBoardUrls={urls} />);
    urls.forEach((url, index) => {
      expect(screen.getByAltText(`Mood board ${index + 1}`)).toHaveAttribute('src', url);
    });
    expect(screen.getAllByRole('img').length).toBe(urls.length);
  });

  test('calls onClose when close button is clicked', () => {
    render(<MoodBoardPanel {...defaultProps} />);
    fireEvent.click(screen.getByLabelText('Close mood board'));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  test('opens AddImageModal when add button is clicked', () => {
    render(<MoodBoardPanel {...defaultProps} />);
    fireEvent.click(screen.getByLabelText('Add new image to mood board'));
    // Assuming AddMoodBoardImageModal has a distinct element, e.g., a title or input
    // For this test, we'll check if the modal's "Add URL" or "Generate Image" button is present
    // This depends on the modal's implementation.
    // If the modal is complex to test here, consider this an integration point.
    // For now, we assume the modal becomes visible. The test for AddMoodBoardImageModal itself should cover its internals.
    // Here, we are just checking if the action to open it is triggered.
    // Let's assume the modal, when open, contains text "Add Image URL" or similar.
    // This is a placeholder, adjust based on actual modal content.
    expect(screen.getByText(/Add Image from URL/i)).toBeInTheDocument(); // Placeholder, depends on AddMoodBoardImageModal
  });

  // Test for CSS class names related to width/wrapping
  test('applies correct CSS classes for panel and list', () => {
    render(<MoodBoardPanel {...defaultProps} moodBoardUrls={['url1.jpg']} />);
    const panel = screen.getByRole('dialog'); // The main panel div
    expect(panel).toHaveClass('mood-board-panel');
    // The list div is within SortableContext, then DndContext in the implementation.
    // We need to ensure our mock structure allows finding it or adjust the query.
    // Since SortableContext and DndContext are mocked as divs, we can search within them.
    const list = panel.querySelector('.mood-board-list');
    expect(list).toBeInTheDocument();
    expect(list).toHaveClass('mood-board-list');
  });

  describe('Drag and Drop Reordering', () => {
    const initialUrls = ['url1.jpg', 'url2.jpg', 'url3.jpg'];

    // Helper to get the handleDragEnd function from the component instance
    // This is a bit of a workaround because handleDragEnd is not directly exposed.
    // We find DndContext and extract its onDragEnd prop.
    const getHandleDragEnd = (props: MoodBoardPanelProps): ((event: DragEndEvent) => void) | undefined => {
      const { container } = render(<MoodBoardPanel {...props} />);
      // DndContext is mocked as a simple div. We need to find where onDragEnd is passed.
      // In the actual component, DndContext receives onDragEnd.
      // Since we can't directly access internal functions of the React component instance easily with RTL,
      // we rely on the onDragEnd prop of the DndContext.
      // This requires our DndContext mock to capture the onDragEnd prop.

      // Update mock to capture onDragEnd
      let capturedOnDragEnd;
      (jest.requireMock('@dnd-kit/core').DndContext as jest.Mock).mockImplementationOnce(({ children, onDragEnd }) => {
        capturedOnDragEnd = onDragEnd;
        return <div>{children}</div>;
      });
      render(<MoodBoardPanel {...props} />);
      return capturedOnDragEnd;
    };


    test('updates moodBoardUrls on drag end', () => {
      const handleDragEnd = getHandleDragEnd({ ...defaultProps, moodBoardUrls: initialUrls });
      expect(handleDragEnd).toBeDefined();

      if (handleDragEnd) {
        const dragEndEvent: DragEndEvent = {
          active: { id: 'url1.jpg', data: { current: undefined }, over: null },
          over: { id: 'url3.jpg', data: { current: undefined }, rect: { width:0, height:0, top:0, left:0, bottom:0, right:0 } },
          collisions: null, delta: { x:0, y:0 }, activators: { keyboard: false, mouse: false, pointer: false, touch: false }
        };
        handleDragEnd(dragEndEvent);
      }

      expect(mockOnUpdateMoodBoardUrls).toHaveBeenCalledTimes(1);
      // Expected order: url2.jpg, url3.jpg, url1.jpg (url1 moved after url3)
      // arrayMove logic: (array, from, to)
      // url1 (index 0) moved to position of url3 (index 2)
      // old: [url1, url2, url3]
      // new: [url2, url3, url1]
      expect(mockOnUpdateMoodBoardUrls).toHaveBeenCalledWith(['url2.jpg', 'url3.jpg', 'url1.jpg']);
    });

    test('does not update if active and over are the same', () => {
      const handleDragEnd = getHandleDragEnd({ ...defaultProps, moodBoardUrls: initialUrls });
      expect(handleDragEnd).toBeDefined();

      if (handleDragEnd) {
        const dragEndEvent: DragEndEvent = {
            active: { id: 'url1.jpg', data: { current: undefined }, over: null },
            over: { id: 'url1.jpg', data: { current: undefined }, rect: { width:0, height:0, top:0, left:0, bottom:0, right:0 } },
            collisions: null, delta: { x:0, y:0 }, activators: { keyboard: false, mouse: false, pointer: false, touch: false }
        };
        handleDragEnd(dragEndEvent);
      }
      expect(mockOnUpdateMoodBoardUrls).not.toHaveBeenCalled();
    });

     test('handles drag to the same position effectively (no change)', () => {
      const handleDragEnd = getHandleDragEnd({ ...defaultProps, moodBoardUrls: initialUrls });
      expect(handleDragEnd).toBeDefined();

      if (handleDragEnd) {
        // Simulating dragging url1 and dropping it back onto url1 (or its original spot)
        // In arrayMove, if oldIndex and newIndex are the same, it should return the same array.
        const dragEndEvent: DragEndEvent = {
            active: { id: 'url1.jpg', data: { current: undefined }, over: null },
            // 'over' could be the same ID or an ID that results in the same index after lookup
            over: { id: 'url1.jpg', data: { current: undefined }, rect: { width:0, height:0, top:0, left:0, bottom:0, right:0 } },
            collisions: null, delta: { x:0, y:0 }, activators: { keyboard: false, mouse: false, pointer: false, touch: false }
        };
        handleDragEnd(dragEndEvent);
      }
      // onUpdateMoodBoardUrls should not be called if the order doesn't actually change.
      // The component's handleDragEnd has `if (over && active.id !== over.id)`
      // So this case is already handled and should not call onUpdateMoodBoardUrls
      expect(mockOnUpdateMoodBoardUrls).not.toHaveBeenCalled();
    });

    test('handles drag when over is null (no valid drop target)', () => {
        const handleDragEnd = getHandleDragEnd({ ...defaultProps, moodBoardUrls: initialUrls });
        expect(handleDragEnd).toBeDefined();

        if (handleDragEnd) {
          const dragEndEvent: DragEndEvent = {
              active: { id: 'url1.jpg', data: { current: undefined }, over: null },
              over: null, // Simulate dropping outside a valid target
              collisions: null, delta: { x:0, y:0 }, activators: { keyboard: false, mouse: false, pointer: false, touch: false }
          };
          handleDragEnd(dragEndEvent);
        }
        expect(mockOnUpdateMoodBoardUrls).not.toHaveBeenCalled();
      });
  });

  describe('Image Removal within Sortable Items', () => {
    const initialUrls = ['url1.jpg', 'url2.jpg', 'url3.jpg'];

    beforeEach(() => {
        // Mock useSortable to include listeners for simulating clicks on remove buttons
        (jest.requireMock('@dnd-kit/sortable').useSortable as jest.Mock).mockImplementation(({ id }) => ({
            attributes: { 'data-testid': `sortable-item-${id}` }, // Add data-testid for easy querying
            listeners: {}, // Mock listeners, not directly used for remove click
            setNodeRef: jest.fn(),
            transform: null,
            transition: null,
            isDragging: false,
          }));
    });

    test('removes an image when its close button is clicked and preserves order', () => {
      render(<MoodBoardPanel {...defaultProps} moodBoardUrls={initialUrls} />);

      // Find the remove button for the second item (url2.jpg)
      // The button is inside the SortableMoodBoardItem, which is associated with the URL 'url2.jpg'
      // The button itself has aria-label="Remove image 2"
      const removeButton = screen.getByLabelText('Remove image 2'); // Index is 1-based in label
      fireEvent.click(removeButton);

      expect(mockOnUpdateMoodBoardUrls).toHaveBeenCalledTimes(1);
      expect(mockOnUpdateMoodBoardUrls).toHaveBeenCalledWith(['url1.jpg', 'url3.jpg']);
    });

    test('removes the first image', () => {
        render(<MoodBoardPanel {...defaultProps} moodBoardUrls={initialUrls} />);
        const removeButton = screen.getByLabelText('Remove image 1');
        fireEvent.click(removeButton);
        expect(mockOnUpdateMoodBoardUrls).toHaveBeenCalledWith(['url2.jpg', 'url3.jpg']);
    });

    test('removes the last image', () => {
        render(<MoodBoardPanel {...defaultProps} moodBoardUrls={initialUrls} />);
        const removeButton = screen.getByLabelText('Remove image 3');
        fireEvent.click(removeButton);
        expect(mockOnUpdateMoodBoardUrls).toHaveBeenCalledWith(['url1.jpg', 'url2.jpg']);
    });

    test('removes the only image', () => {
        render(<MoodBoardPanel {...defaultProps} moodBoardUrls={['url1.jpg']} />);
        const removeButton = screen.getByLabelText('Remove image 1');
        fireEvent.click(removeButton);
        expect(mockOnUpdateMoodBoardUrls).toHaveBeenCalledWith([]);
    });
  });
});
