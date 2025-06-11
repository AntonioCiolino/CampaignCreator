import React from 'react';
import { render, fireEvent, screen, within } from '@testing-library/react';
import '@testing-library/jest-dom'; // For extended matchers like .toBeDisabled()
import CampaignThemeEditor, { CampaignThemeData } from './CampaignThemeEditor';

describe('CampaignThemeEditor', () => {
  const mockOnThemeDataChange = jest.fn();
  const mockOnSaveTheme = jest.fn();

  const initialThemeData: CampaignThemeData = {
    theme_primary_color: '#111111',
    theme_secondary_color: '#222222',
    theme_background_color: '#333333',
    theme_text_color: '#444444',
    theme_font_family: 'Arial, sans-serif',
    theme_background_image_url: 'https://example.com/initial.png',
    theme_background_image_opacity: 0.8,
  };

  const renderEditor = (props?: Partial<React.ComponentProps<typeof CampaignThemeEditor>>) => {
    const defaultProps: React.ComponentProps<typeof CampaignThemeEditor> = {
      themeData: initialThemeData,
      onThemeDataChange: mockOnThemeDataChange,
      onSaveTheme: mockOnSaveTheme,
      isSaving: false,
      saveError: null,
      saveSuccess: null,
      currentThematicImageUrl: null,
      ...props,
    };
    return render(<CampaignThemeEditor {...defaultProps} />);
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Test color inputs
  it.each([
    { label: /Primary Color/i, name: 'theme_primary_color', initial: initialThemeData.theme_primary_color, newValue: '#ff0000' },
    { label: /Secondary Color/i, name: 'theme_secondary_color', initial: initialThemeData.theme_secondary_color, newValue: '#00ff00' },
    { label: /Background Color/i, name: 'theme_background_color', initial: initialThemeData.theme_background_color, newValue: '#0000ff' },
    { label: /Text Color/i, name: 'theme_text_color', initial: initialThemeData.theme_text_color, newValue: '#ffff00' },
  ])('calls onThemeDataChange when $label input changes', ({ label, name, newValue }) => {
    renderEditor();
    const colorInput = screen.getByLabelText(label);
    fireEvent.input(colorInput, { target: { value: newValue } }); // 'input' event for color pickers
    expect(mockOnThemeDataChange).toHaveBeenCalledWith(
      expect.objectContaining({ [name]: newValue })
    );
  });

  it('calls onThemeDataChange when Font Family input changes', () => {
    renderEditor();
    const fontFamilyInput = screen.getByLabelText(/Font Family/i);
    fireEvent.change(fontFamilyInput, { target: { value: 'Impact, fantasy' } });
    expect(mockOnThemeDataChange).toHaveBeenCalledWith(
      expect.objectContaining({ theme_font_family: 'Impact, fantasy' })
    );
  });

  it('calls onThemeDataChange with null when Font Family input is cleared', () => {
    renderEditor();
    const fontFamilyInput = screen.getByLabelText(/Font Family/i);
    fireEvent.change(fontFamilyInput, { target: { value: '' } });
    expect(mockOnThemeDataChange).toHaveBeenCalledWith(
      expect.objectContaining({ theme_font_family: null })
    );
  });

  it('calls onThemeDataChange when Background Image URL input changes', () => {
    renderEditor();
    const bgUrlInput = screen.getByLabelText(/Background Image URL/i);
    fireEvent.change(bgUrlInput, { target: { value: 'https://example.com/new.png' } });
    expect(mockOnThemeDataChange).toHaveBeenCalledWith(
      expect.objectContaining({ theme_background_image_url: 'https://example.com/new.png' })
    );
  });

  it('calls onThemeDataChange with null when Background Image URL input is cleared', () => {
    renderEditor();
    const bgUrlInput = screen.getByLabelText(/Background Image URL/i);
    fireEvent.change(bgUrlInput, { target: { value: '' } });
    expect(mockOnThemeDataChange).toHaveBeenCalledWith(
      expect.objectContaining({ theme_background_image_url: null })
    );
  });

  it('calls onThemeDataChange when Background Image Opacity input changes', () => {
    renderEditor({ themeData: { ...initialThemeData, theme_background_image_url: 'https://example.com/image.jpg' }});
    const bgOpacityInput = screen.getByLabelText(/Background Image Opacity/i);
    // For range inputs, 'input' or 'change' event can be used.
    // The value is a string, so parseFloat will be used by the component.
    fireEvent.change(bgOpacityInput, { target: { value: '0.35' } });
    expect(mockOnThemeDataChange).toHaveBeenCalledWith(
      expect.objectContaining({ theme_background_image_opacity: 0.35 })
    );
  });

  describe('"Use Thematic Image as Background" button', () => {
    const thematicUrl = 'http://example.com/thematic.jpg';

    it('is visible and enabled if currentThematicImageUrl is provided', () => {
      renderEditor({ currentThematicImageUrl: thematicUrl });
      const useThematicButton = screen.getByText(/Use Current Thematic Image as Background/i);
      expect(useThematicButton).toBeInTheDocument();
      expect(useThematicButton).not.toBeDisabled();
    });

    it('is not rendered if currentThematicImageUrl is not provided', () => {
      renderEditor({ currentThematicImageUrl: null });
      const useThematicButton = screen.queryByText(/Use Current Thematic Image as Background/i);
      expect(useThematicButton).not.toBeInTheDocument();
    });

    it('calls onThemeDataChange with thematic image URL when clicked', () => {
      renderEditor({ currentThematicImageUrl: thematicUrl });
      const useThematicButton = screen.getByText(/Use Current Thematic Image as Background/i);
      fireEvent.click(useThematicButton);
      expect(mockOnThemeDataChange).toHaveBeenCalledWith(
        expect.objectContaining({ theme_background_image_url: thematicUrl })
      );
    });
  });

  it('calls onSaveTheme when "Save Theme Settings" button is clicked', () => {
    renderEditor();
    // The button is inside a form, so we can get it by its submit role or text.
    const saveButton = screen.getByRole('button', { name: /Save Theme Settings/i });
    fireEvent.click(saveButton);
    expect(mockOnSaveTheme).toHaveBeenCalledTimes(1);
  });

  describe('Feedback Messages and Button States', () => {
    it('disables save button and shows "Saving..." text when isSaving is true', () => {
      renderEditor({ isSaving: true });
      const saveButton = screen.getByRole('button', { name: /Saving Theme.../i });
      expect(saveButton).toBeDisabled();
    });

    it('displays error message when saveError is provided', () => {
      const errorMessage = 'Failed to save theme.';
      renderEditor({ saveError: errorMessage });
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      // Check it's in the right place (e.g., within the form or a specific feedback area)
      const form = screen.getByRole('button', { name: /Save Theme Settings/i }).closest('form');
      expect(within(form!).getByText(errorMessage)).toBeInTheDocument();
    });

    it('displays success message when saveSuccess is provided', () => {
      const successMessage = 'Theme saved successfully!';
      renderEditor({ saveSuccess: successMessage });
      expect(screen.getByText(successMessage)).toBeInTheDocument();
      const form = screen.getByRole('button', { name: /Save Theme Settings/i }).closest('form');
      expect(within(form!).getByText(successMessage)).toBeInTheDocument();
    });
  });

  it('disables opacity slider if background image URL is not set', () => {
    renderEditor({ themeData: { ...initialThemeData, theme_background_image_url: null }});
    const bgOpacityInput = screen.getByLabelText(/Background Image Opacity/i);
    expect(bgOpacityInput).toBeDisabled();
  });

  it('enables opacity slider if background image URL is set', () => {
    renderEditor({ themeData: { ...initialThemeData, theme_background_image_url: 'http://example.com/image.jpg' }});
    const bgOpacityInput = screen.getByLabelText(/Background Image Opacity/i);
    expect(bgOpacityInput).not.toBeDisabled();
  });
});
