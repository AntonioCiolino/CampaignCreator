// campaign_crafter_ui/src/utils/themeUtils.ts
export interface CampaignThemeData {
  theme_primary_color?: string | null;
  theme_secondary_color?: string | null;
  theme_background_color?: string | null;
  theme_text_color?: string | null;
  theme_font_family?: string | null;
  theme_background_image_url?: string | null;
  theme_background_image_opacity?: number | null;
}

export const applyThemeToDocument = (themeData: CampaignThemeData | null) => {
  // Ensure this code only runs in the browser environment
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return;
  }

  const root = document.documentElement;
  if (!root || !root.style) {
    // Fallback or log error if document.documentElement.style is not available
    // This might happen in some testing environments if not properly mocked
    console.warn('document.documentElement.style is not available. Cannot apply theme.');
    return;
  }

  if (!themeData) {
    root.style.removeProperty('--campaign-primary-color');
    root.style.removeProperty('--campaign-secondary-color');
    root.style.removeProperty('--campaign-background-color');
    root.style.removeProperty('--campaign-text-color');
    root.style.removeProperty('--campaign-font-family');
    root.style.removeProperty('--campaign-background-image-url');
    root.style.removeProperty('--campaign-background-image-opacity');
    return;
  }

  const setOrRemoveProperty = (property: string, value: string | number | null | undefined) => {
    if (value !== null && value !== undefined && String(value).trim() !== '') {
      root.style.setProperty(property, String(value));
    } else {
      root.style.removeProperty(property);
    }
  };

  setOrRemoveProperty('--campaign-primary-color', themeData.theme_primary_color);
  setOrRemoveProperty('--campaign-secondary-color', themeData.theme_secondary_color);
  setOrRemoveProperty('--campaign-background-color', themeData.theme_background_color);
  setOrRemoveProperty('--campaign-text-color', themeData.theme_text_color);
  setOrRemoveProperty('--campaign-font-family', themeData.theme_font_family);

  if (themeData.theme_background_image_url && String(themeData.theme_background_image_url).trim() !== '') {
    setOrRemoveProperty('--campaign-background-image-url', `url("${themeData.theme_background_image_url}")`);
    // Opacity should only be set if there's an image URL.
    // If opacity is null/undefined, it might fall back to a CSS default (e.g., 1).
    // If explicitly set to empty string or null, it should be removed or handled by CSS default.
    if (themeData.theme_background_image_opacity !== null && themeData.theme_background_image_opacity !== undefined) {
        setOrRemoveProperty('--campaign-background-image-opacity', themeData.theme_background_image_opacity);
    } else {
        root.style.removeProperty('--campaign-background-image-opacity'); // Or set to a default like '1'
    }
  } else {
    root.style.removeProperty('--campaign-background-image-url');
    root.style.removeProperty('--campaign-background-image-opacity');
  }
};
