import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import TOCEditor from './TOCEditor';
import { TOCEntry } from '../../types/campaignTypes'; // Corrected import path
import { jest } from '@jest/globals'; // For mocking

// Mock react-beautiful-dnd as it's not needed for these basic tests and can cause issues
jest.mock('react-beautiful-dnd', () => ({
  DragDropContext: ({ children }: { children: React.ReactNode }) => <div data-testid="dnd-context">{children}</div>,
  Droppable: ({ children }: { children: (provided: any, snapshot: any) => React.ReactNode }) =>
    <div data-testid="droppable">{children({ innerRef: jest.fn(), droppableProps: {}, placeholder: <div data-testid="placeholder" /> }, {})}</div>,
  Draggable: ({ children }: { children: (provided: any, snapshot: any) => React.ReactNode }) =>
    <div data-testid="draggable">{children({ innerRef: jest.fn(), draggableProps: {}, dragHandleProps: {} }, {})}</div>,
}));


const mockToc: TOCEntry[] = [
  { title: 'Chapter 1', type: 'chapter' },
  { title: 'NPC Alice', type: 'character' },
];

describe('TOCEditor', () => {
  // Corrected generic signature for jest.fn: jest.fn<ReturnType, ArgsType[]>()
  const mockOnTOCChange = jest.fn<void, [TOCEntry[]]>();

  beforeEach(() => {
    // Clear mock history before each test
    mockOnTOCChange.mockClear();
  });

  test('renders initial TOC entries correctly', () => {
    render(<TOCEditor toc={mockToc} onTOCChange={mockOnTOCChange} />);

    expect(screen.getByDisplayValue('Chapter 1')).toBeInTheDocument();
    // Check select by its current value; MUI Select renders differently
    // We can check if an element with the text 'chapter' (as value) is present
    // For MUI v5, the Select renders a hidden input with the value for forms
    const allComboboxesInitial = screen.getAllByRole('combobox', { hidden: true });
    expect(allComboboxesInitial[0]).toHaveValue('chapter');


    expect(screen.getByDisplayValue('NPC Alice')).toBeInTheDocument();
    // For the second entry, find its specific combobox
    expect(allComboboxesInitial[1]).toHaveValue('character');
  });

  test('calls onTOCChange when a title is edited', () => {
    render(<TOCEditor toc={mockToc} onTOCChange={mockOnTOCChange} />);

    const titleInputs = screen.getAllByLabelText('Title'); // MUI TextFields have labels associated
    fireEvent.change(titleInputs[0], { target: { value: 'Chapter 1 Updated' } });

    expect(mockOnTOCChange).toHaveBeenCalledTimes(1);
    expect(mockOnTOCChange).toHaveBeenCalledWith([
      { title: 'Chapter 1 Updated', type: 'chapter' },
      { title: 'NPC Alice', type: 'character' },
    ]);
  });

  test('calls onTOCChange when a type is edited', () => {
    render(<TOCEditor toc={mockToc} onTOCChange={mockOnTOCChange} />);

    // MUI Select interaction for testing:
    // 1. Click the select to open it (the div with role button)
    // 2. Click the desired option from the listbox that appears
    const typeSelectDisplays = screen.getAllByRole('button', { name: /Type .*/i }); // Gets the display part of the Select
    fireEvent.mouseDown(typeSelectDisplays[0]); // Open the first select

    // Find and click the 'Location' option in the listbox (which should now be visible)
    // The listbox role is usually on a `ul` element that appears.
    const listbox = screen.getByRole('listbox');
    const locationOption = Array.from(listbox.querySelectorAll('li')).find(li => li.textContent === 'Location');
    if (!locationOption) throw new Error("Location option not found");
    fireEvent.click(locationOption);


    expect(mockOnTOCChange).toHaveBeenCalledTimes(1);
    expect(mockOnTOCChange).toHaveBeenCalledWith([
      { title: 'Chapter 1', type: 'location' },
      { title: 'NPC Alice', type: 'character' },
    ]);
  });

  test('adds a new entry when "Add TOC Entry" button is clicked', () => {
    render(<TOCEditor toc={mockToc} onTOCChange={mockOnTOCChange} />);

    const addButton = screen.getByRole('button', { name: /Add TOC Entry/i });
    fireEvent.click(addButton);

    expect(mockOnTOCChange).toHaveBeenCalledTimes(1);
    expect(mockOnTOCChange).toHaveBeenCalledWith([
      ...mockToc,
      { title: 'New Section', type: 'generic' },
    ]);
  });

  test('deletes an entry when delete button is clicked', () => {
    render(<TOCEditor toc={mockToc} onTOCChange={mockOnTOCChange} />);

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]); // Delete the first entry

    expect(mockOnTOCChange).toHaveBeenCalledTimes(1);
    expect(mockOnTOCChange).toHaveBeenCalledWith([
      { title: 'NPC Alice', type: 'character' }, // Only the second entry should remain
    ]);
  });
});
