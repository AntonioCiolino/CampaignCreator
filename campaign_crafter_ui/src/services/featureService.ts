// Defines the structure of a Feature Prompt object
export interface FeaturePrompt {
  name: string;
  template: string;
}

// Defines the structure of the response from the /api/features endpoint
interface FeaturePromptsResponse {
  features: FeaturePrompt[];
}

import { getApiBaseUrl } from './env'; // Import the new function
const API_BASE_URL = getApiBaseUrl();

/**
 * Fetches the list of all available feature prompts from the backend.
 * @returns A promise that resolves to an array of FeaturePrompt objects.
 * @throws Will throw an error if the network request fails or the API returns an error.
 */
export const getAllFeaturePrompts = async (): Promise<FeaturePrompt[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/features`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Network response was not ok.' }));
      throw new Error(errorData.detail || `Failed to fetch feature prompts: ${response.statusText}`);
    }
    const data: FeaturePromptsResponse = await response.json();
    if (!data.features) {
        console.warn('No features found in response:', data);
        return [];
    }
    return data.features;
  } catch (error) {
    console.error("Error fetching all feature prompts:", error);
    throw error;
  }
};

/**
 * Fetches a specific feature prompt by its name from the backend.
 * @param featureName The name of the feature prompt to retrieve.
 * @returns A promise that resolves to a FeaturePrompt object, or null if not found.
 * @throws Will throw an error if the network request fails (excluding 404) or the API returns an unexpected error.
 */
export const getFeaturePromptByName = async (featureName: string): Promise<FeaturePrompt | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/features/${featureName}`);
    if (!response.ok) {
      if (response.status === 404) {
        return null; // Feature not found, return null as per requirement
      }
      const errorData = await response.json().catch(() => ({ detail: 'Network response was not ok.' }));
      throw new Error(errorData.detail || `Failed to fetch feature prompt '${featureName}': ${response.statusText}`);
    }
    const data: FeaturePrompt = await response.json();
    return data;
  } catch (error) {
    // Don't re-throw for 404, as it's handled by returning null.
    // Error objects might not have a 'status' property directly unless they are custom error objects.
    // The check for response.status === 404 above handles the 404 case before this catch block.
    if (error instanceof Error && error.message.includes("404")) {
        // This specific check might be redundant if 404s are always caught by !response.ok
        console.warn(`Feature prompt '${featureName}' not found (404).`);
        return null;
    }
    console.error(`Error fetching feature prompt '${featureName}':`, error);
    throw error;
  }
};
