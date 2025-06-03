import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import CampaignSectionEditor from './CampaignSectionEditor';
// Import the actual CampaignSectionView to test its presence, though its internals are complex for this test.
// For interaction tests like delete, we need to ensure the button within CampaignSectionView is found if delete is there.
// However, the provided mock is fine for testing if CampaignSectionEditor passes props correctly.
// The current test structure relies on the mock.
import { CampaignSection } from '../../services/campaignService'; // Corrected import path

// Mock CampaignSectionView as it's a child component and not the focus of this unit test
jest.mock('../CampaignSectionView', () => {
  return jest.fn(({ section, onTitleChange, onContentChange }) => (
    <div data-testid={`mock-section-view-${section.id}`}>
      <input
        type="text"
        value={section.title}
        onChange={(e) => onTitleChange(e.target.value)}
        aria-label={`Title for ${section.id}`}
      />
      <textarea
        value={section.content}
        onChange={(e) => onContentChange(e.target.value)}
        aria-label={`Content for ${section.id}`}
      />
    </div>
  ));
});

describe('CampaignSectionEditor', () => {
  const mockSetSections = jest.fn();
  const mockHandleAddNewSection = jest.fn();
  const mockHandleDeleteSection = jest.fn();
  const mockHandleUpdateSectionContent = jest.fn();
  const mockHandleUpdateSectionTitle = jest.fn();
  const mockOnUpdateSectionOrder = jest.fn().mockResolvedValue(undefined); // Added from dnd test

  // Clear mocks before each test
  beforeEach(() => {
    mockSetSections.mockClear();
    mockHandleAddNewSection.mockClear();
    mockHandleDeleteSection.mockClear();
    mockHandleUpdateSectionContent.mockClear();
    mockHandleUpdateSectionTitle.mockClear();
    mockOnUpdateSectionOrder.mockClear();
    // Clear mock for CampaignSectionView if it's a jest.fn() and you want to check calls on it
    if (jest.isMockFunction(require('../CampaignSectionView').default)) {
      require('../CampaignSectionView').default.mockClear();
    }
  });

  const section1: CampaignSection = { id: 1, title: 'Section One', content: 'Content One', order: 0 };
  const section2: CampaignSection = { id: 2, title: 'Section Two', content: 'Content Two', order: 1 };

  const defaultProps = {
    sections: [],
    setSections: mockSetSections,
    handleAddNewSection: mockHandleAddNewSection,
    handleDeleteSection: mockHandleDeleteSection,
    handleUpdateSectionContent: mockHandleUpdateSectionContent,
    handleUpdateSectionTitle: mockHandleUpdateSectionTitle,
    onUpdateSectionOrder: mockOnUpdateSectionOrder, // Added
  };

  test('renders correctly with no sections', () => {
    render(<CampaignSectionEditor {...defaultProps} />);

    expect(screen.getByText(/Campaign Sections/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Add New Section/i })).toBeInTheDocument();
    expect(screen.getByText(/No sections yet. Click "Add New Section" to begin./i)).toBeInTheDocument();
  });

  test('renders sections when provided', () => {
    render(<CampaignSectionEditor {...defaultProps} sections={[section1, section2]} />);

    expect(screen.getByText(/Campaign Sections/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Add New Section/i })).toBeInTheDocument();
    
    // Check for mocked CampaignSectionView instances
    expect(screen.getByTestId(`mock-section-view-${section1.id}`)).toBeInTheDocument();
    expect(screen.getByLabelText(`Title for ${section1.id}`)).toHaveValue(section1.title);
    expect(screen.getByLabelText(`Content for ${section1.id}`)).toHaveValue(section1.content);

    expect(screen.getByTestId(`mock-section-view-${section2.id}`)).toBeInTheDocument();
    expect(screen.getByLabelText(`Title for ${section2.id}`)).toHaveValue(section2.title);
    expect(screen.getByLabelText(`Content for ${section2.id}`)).toHaveValue(section2.content);

    // Check for delete buttons (aria-label "delete" is default for IconButton with DeleteIcon)
    // This relies on the mock rendering something identifiable for delete.
    // The current mock doesn't explicitly render a delete button, but the real component would have one.
    // The Paper component in CampaignSectionEditor has the IconButton for delete.
    expect(screen.getAllByRole('button', { name: /delete/i })).toHaveLength(2);
  });

  test('calls handleAddNewSection when "Add New Section" button is clicked', () => {
    render(<CampaignSectionEditor {...defaultProps} />);
    const addButton = screen.getByRole('button', { name: /Add New Section/i });
    fireEvent.click(addButton);
    expect(mockHandleAddNewSection).toHaveBeenCalledTimes(1);
  });

  test('calls handleDeleteSection when a section delete button is clicked', () => {
    // This test assumes the delete button is part of the CampaignSectionEditor's direct rendering per section,
    // not deeply nested within CampaignSectionView in a way that the mock hides it.
    // In the actual implementation, the IconButton for delete is directly in CampaignSectionEditor's map.
    render(<CampaignSectionEditor {...defaultProps} sections={[section1]} />);
    
    const deleteButton = screen.getByRole('button', { name: /delete/i }); // Should find one
    fireEvent.click(deleteButton);
    
    expect(mockHandleDeleteSection).toHaveBeenCalledWith(section1.id);
  });

  // Test for onUpdateSectionOrder is in CampaignSectionEditor.dnd.test.tsx
});
