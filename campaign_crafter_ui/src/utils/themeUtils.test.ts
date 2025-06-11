import { applyThemeToDocument, CampaignThemeData } from './themeUtils'; // Adjust path as necessary

describe('applyThemeToDocument', () => {
  const mockSetProperty = jest.fn();
  const mockRemoveProperty = jest.fn();
  let originalDocumentElementStyle: any;

  beforeAll(() => {
    // Store original style descriptor if it exists
    originalDocumentElementStyle = Object.getOwnPropertyDescriptor(document.documentElement, 'style');
  });

  beforeEach(() => {
    jest.clearAllMocks();
    // Define document.documentElement.style for each test
    Object.defineProperty(document.documentElement, 'style', {
      value: {
        setProperty: mockSetProperty,
        removeProperty: mockRemoveProperty,
        // Add any other style properties accessed by your code if necessary
      },
      configurable: true, // Make it configurable so it can be redefined/restored
      writable: true,
    });
  });

  afterAll(() => {
    // Restore original style descriptor if it was stored
    if (originalDocumentElementStyle) {
      Object.defineProperty(document.documentElement, 'style', originalDocumentElementStyle);
    } else {
      // If it didn't exist, delete the mock one (less common for documentElement.style)
      // delete (document.documentElement as any).style;
    }
  });

  it('should set CSS variables for all provided theme properties', () => {
    const themeData: CampaignThemeData = {
      theme_primary_color: '#ff0000',
      theme_secondary_color: '#00ff00',
      theme_background_color: '#0000ff',
      theme_text_color: '#ffff00',
      theme_font_family: 'Arial, sans-serif',
      theme_background_image_url: 'http://example.com/bg.png',
      theme_background_image_opacity: 0.5,
    };
    applyThemeToDocument(themeData);

    expect(mockSetProperty).toHaveBeenCalledWith('--campaign-primary-color', '#ff0000');
    expect(mockSetProperty).toHaveBeenCalledWith('--campaign-secondary-color', '#00ff00');
    expect(mockSetProperty).toHaveBeenCalledWith('--campaign-background-color', '#0000ff');
    expect(mockSetProperty).toHaveBeenCalledWith('--campaign-text-color', '#ffff00');
    expect(mockSetProperty).toHaveBeenCalledWith('--campaign-font-family', 'Arial, sans-serif');
    expect(mockSetProperty).toHaveBeenCalledWith('--campaign-background-image-url', 'url("http://example.com/bg.png")');
    expect(mockSetProperty).toHaveBeenCalledWith('--campaign-background-image-opacity', '0.5');
    expect(mockRemoveProperty).not.toHaveBeenCalled(); // No properties should be removed if all are provided
  });

  it('should remove CSS variables if themeData properties are null or empty strings', () => {
    const themeData: CampaignThemeData = {
      theme_primary_color: null,
      theme_font_family: '',
      theme_background_image_url: '  ', // Test with whitespace only string
      theme_text_color: '#121212', // A valid value to ensure it's not removed
    };
    applyThemeToDocument(themeData);

    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-primary-color');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-font-family');
    // For background image, if URL is empty/null, both URL and opacity are removed
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-background-image-url');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-background-image-opacity');

    expect(mockSetProperty).toHaveBeenCalledWith('--campaign-text-color', '#121212');
    // Ensure setProperty wasn't called for the null/empty ones that should be removed
    expect(mockSetProperty).not.toHaveBeenCalledWith('--campaign-primary-color', expect.anything());
    expect(mockSetProperty).not.toHaveBeenCalledWith('--campaign-font-family', expect.anything());
  });

  it('should remove all theme CSS variables if themeData is null', () => {
    applyThemeToDocument(null);
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-primary-color');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-secondary-color');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-background-color');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-text-color');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-font-family');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-background-image-url');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-background-image-opacity');
    expect(mockSetProperty).not.toHaveBeenCalled();
  });

  it('should correctly handle opacity when background image URL is present but opacity is null/undefined', () => {
    const themeData: CampaignThemeData = {
      theme_background_image_url: 'http://example.com/bg.png',
      theme_background_image_opacity: null, // Opacity is null
    };
    applyThemeToDocument(themeData);
    expect(mockSetProperty).toHaveBeenCalledWith('--campaign-background-image-url', 'url("http://example.com/bg.png")');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-background-image-opacity');

    jest.clearAllMocks();
    const themeDataUndefinedOpacity: CampaignThemeData = {
        theme_background_image_url: 'http://example.com/bg.png',
        theme_background_image_opacity: undefined, // Opacity is undefined
      };
    applyThemeToDocument(themeDataUndefinedOpacity);
    expect(mockSetProperty).toHaveBeenCalledWith('--campaign-background-image-url', 'url("http://example.com/bg.png")');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-background-image-opacity');
  });

  it('should not set opacity if background image URL is missing', () => {
    const themeData: CampaignThemeData = {
      theme_background_image_url: null,
      theme_background_image_opacity: 0.7,
    };
    applyThemeToDocument(themeData);
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-background-image-url');
    expect(mockRemoveProperty).toHaveBeenCalledWith('--campaign-background-image-opacity');
    expect(mockSetProperty).not.toHaveBeenCalledWith('--campaign-background-image-url', expect.anything());
    expect(mockSetProperty).not.toHaveBeenCalledWith('--campaign-background-image-opacity', expect.anything());
  });
});
