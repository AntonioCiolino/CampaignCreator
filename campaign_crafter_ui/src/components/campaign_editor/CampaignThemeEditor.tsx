// Example structure for CampaignThemeEditor.tsx
import React from 'react';
import { applyThemeToDocument } from '../../utils/themeUtils';
// Assuming Campaign type includes theme fields, if not, CampaignThemeData will be primary
// import { Campaign } from '../../services/campaignService';
import './CampaignThemeEditor.css'; // Create this CSS file

export interface CampaignThemeData {
  theme_primary_color?: string | null;
  theme_secondary_color?: string | null;
  theme_background_color?: string | null;
  theme_text_color?: string | null;
  theme_font_family?: string | null;
  theme_background_image_url?: string | null;
  theme_background_image_opacity?: number | null;
}

interface CampaignThemeEditorProps {
  themeData: CampaignThemeData;
  onThemeDataChange: (newThemeData: CampaignThemeData) => void;
  onSaveTheme: () => void;
  isSaving: boolean;
  saveError: string | null;
  saveSuccess: string | null;
  currentThematicImageUrl?: string | null; // New prop
}

const CampaignThemeEditor: React.FC<CampaignThemeEditorProps> = ({
  themeData,
  onThemeDataChange,
  onSaveTheme,
  isSaving,
  saveError,
  saveSuccess,
  currentThematicImageUrl, // Destructure new prop
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    let processedValue: string | number | null = value;

    if (name === 'theme_background_image_opacity') {
      processedValue = value === '' ? null : parseFloat(value);
    } else if (value === '' && type !== 'color') { // For color inputs, value might be #000000, handle separately or rely on defaultColor
      processedValue = null; // Treat empty strings as null for optional text/url fields
    }


    const newThemeData = {
      ...themeData,
      [name]: processedValue,
    };
    onThemeDataChange(newThemeData);
    applyThemeToDocument(newThemeData);
  };

  const handleColorChange = (name: keyof CampaignThemeData, value: string) => {
    // For color inputs, if a user picks black, it's a valid color.
    // If we want a "clear" behavior, it needs a separate button or a specific "null" color.
    // For now, any chosen color is set.
    const newThemeData = { ...themeData, [name]: value };
    onThemeDataChange(newThemeData);
    applyThemeToDocument(newThemeData);
  };

  const defaultColor = (colorValue: string | null | undefined, fallback: string = "#ffffff"): string => {
    return colorValue || fallback;
  };

  const defaultOpacity = (opacityValue: number | null | undefined): number => {
    return opacityValue === null || opacityValue === undefined ? 1 : opacityValue;
  }

  const handleUseThematicImageAsBackground = () => {
    if (currentThematicImageUrl) {
      const newThemeData = {
        ...themeData,
        theme_background_image_url: currentThematicImageUrl,
        // Optionally set a default opacity if desired, e.g.:
        // theme_background_image_opacity: themeData.theme_background_image_opacity === null || themeData.theme_background_image_opacity === undefined
        //                                ? 0.7
        //                                : themeData.theme_background_image_opacity,
      };
      onThemeDataChange(newThemeData);
      applyThemeToDocument(newThemeData);
    }
  };

  return (
    <div className="campaign-theme-editor editor-section card-like">
      <h3>Campaign Theme Settings</h3>
      <form onSubmit={(e) => { e.preventDefault(); onSaveTheme(); }}>
        <div className="form-grid">
          {/* Primary Color */}
          <div className="form-group">
            <label htmlFor="theme_primary_color">Primary Color:</label>
            <input
              type="color"
              id="theme_primary_color"
              name="theme_primary_color"
              value={defaultColor(themeData.theme_primary_color)}
              onChange={(e) => handleColorChange('theme_primary_color', e.target.value)}
            />
          </div>

          {/* Secondary Color */}
          <div className="form-group">
            <label htmlFor="theme_secondary_color">Secondary Color:</label>
            <input
              type="color"
              id="theme_secondary_color"
              name="theme_secondary_color"
              value={defaultColor(themeData.theme_secondary_color)}
              onChange={(e) => handleColorChange('theme_secondary_color', e.target.value)}
            />
          </div>

          {/* Background Color */}
          <div className="form-group">
            <label htmlFor="theme_background_color">Background Color:</label>
            <input
              type="color"
              id="theme_background_color"
              name="theme_background_color"
              value={defaultColor(themeData.theme_background_color)}
              onChange={(e) => handleColorChange('theme_background_color', e.target.value)}
            />
          </div>

          {/* Text Color */}
          <div className="form-group">
            <label htmlFor="theme_text_color">Text Color:</label>
            <input
              type="color"
              id="theme_text_color"
              name="theme_text_color"
              value={defaultColor(themeData.theme_text_color, "#000000")}
              onChange={(e) => handleColorChange('theme_text_color', e.target.value)}
            />
          </div>
        </div>

        {/* Font Family */}
        <div className="form-group">
          <label htmlFor="theme_font_family">Font Family:</label>
          <input
            type="text"
            id="theme_font_family"
            name="theme_font_family"
            placeholder="e.g., Arial, sans-serif"
            value={themeData.theme_font_family || ''}
            onChange={handleChange}
            className="form-input"
          />
        </div>

        {/* Background Image URL */}
        <div className="form-group">
          <label htmlFor="theme_background_image_url">Background Image URL:</label>
          <input
            type="url"
            id="theme_background_image_url"
            name="theme_background_image_url"
            placeholder="https://example.com/image.png"
            value={themeData.theme_background_image_url || ''}
            onChange={handleChange}
            className="form-input"
          />
          {currentThematicImageUrl && (
            <button
              type="button"
              onClick={handleUseThematicImageAsBackground}
              className="utility-button"
              style={{ marginTop: '8px' }}
              disabled={!currentThematicImageUrl}
            >
              Use Current Thematic Image as Background
            </button>
          )}
        </div>

        {/* Background Image Opacity */}
        <div className="form-group">
          <label htmlFor="theme_background_image_opacity">Background Image Opacity:</label>
          <div className="range-input-group">
            <input
              type="range"
              id="theme_background_image_opacity"
              name="theme_background_image_opacity"
              min="0"
              max="1"
              step="0.05"
              value={defaultOpacity(themeData.theme_background_image_opacity)}
              onChange={handleChange}
              disabled={!themeData.theme_background_image_url}
            />
            <span>{defaultOpacity(themeData.theme_background_image_opacity).toFixed(2)}</span>
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary action-button" disabled={isSaving}>
            {isSaving ? 'Saving Theme...' : 'Save Theme Settings'}
          </button>
        </div>
        {saveError && <p className="error-message feedback-message">{saveError}</p>}
        {saveSuccess && <p className="success-message feedback-message">{saveSuccess}</p>}
      </form>
    </div>
  );
};

export default CampaignThemeEditor;
