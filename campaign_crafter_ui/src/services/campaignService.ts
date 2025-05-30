import axios from 'axios';
import apiClient from './apiClient';

// Types matching backend Pydantic models
export interface CampaignSection {
  id: number;
  title: string | null;
  content: string;
  order: number;
  campaign_id: number;
}

// Model information type from the backend /llm/models endpoint
// This might be better placed in llmService.ts if not already there
export interface ModelInfo {
  id: string;
  name: string;
  capabilities: string[]; // Added field
}

export interface Campaign {
  id: number;
  title: string;
  initial_user_prompt: string | null; 
  concept: string | null;
  toc: string | null;
  // owner_id: number; 
  // sections: CampaignSection[]; // Backend doesn't nest this in the Campaign Pydantic model by default
}

export interface CampaignCreatePayload {
  title: string;
  initial_user_prompt: string;
  model_id_with_prefix_for_concept?: string | null; // Added based on backend changes
}

export interface CampaignUpdatePayload {
  title?: string;
  initial_user_prompt?: string;
  // Concept & TOC are typically updated via specific generation endpoints, not direct PUT
}

// For LLM Generation requests common to TOC, Titles, etc.
export interface LLMGenerationPayload {
    model_id_with_prefix?: string | null;
    // temperature?: number; // If you want to control this from client
}

// Fetch all campaigns
export const getAllCampaigns = async (): Promise<Campaign[]> => {
  try {
    const response = await apiClient.get<Campaign[] | null>('/campaigns/'); // Expect Campaign[] or null
    // Ensure we always return an array. If response.data is null or undefined, or not an array, return [].
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    console.error('Error details in campaignService.getAllCampaigns:', error); // Enhanced logging
    if (axios.isAxiosError(error)) {
        console.error('Axios error response status:', error.response?.status);
        console.error('Axios error response data:', error.response?.data);
        console.error('Axios error request config:', error.config);
    }
    throw error; // Re-throw to be caught by UI component
  }
};

// Fetch a single campaign by ID
export const getCampaignById = async (campaignId: string | number): Promise<Campaign> => {
    try {
        const response = await apiClient.get<Campaign>(`/campaigns/${campaignId}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching campaign with ID ${campaignId}:`, error);
        throw error;
    }
};

// Create a new campaign
export const createCampaign = async (campaignData: CampaignCreatePayload): Promise<Campaign> => {
    try {
        const response = await apiClient.post<Campaign>('/campaigns/', campaignData);
        return response.data;
    } catch (error) {
        console.error('Error creating campaign:', error);
        throw error;
    }
};

// Update an existing campaign
export const updateCampaign = async (campaignId: string | number, campaignData: CampaignUpdatePayload): Promise<Campaign> => {
  try {
    const response = await apiClient.put<Campaign>(`/campaigns/${campaignId}`, campaignData);
    return response.data;
  } catch (error) {
    console.error(`Error updating campaign with ID ${campaignId}:`, error);
    throw error;
  }
};

// Define the payload for updating a section
export interface CampaignSectionUpdatePayload {
  title?: string;
  content?: string;
  order?: number;
}

// Update a specific campaign section
export const updateCampaignSection = async (
  campaignId: string | number,
  sectionId: string | number,
  data: CampaignSectionUpdatePayload
): Promise<CampaignSection> => {
  try {
    const response = await apiClient.put<CampaignSection>(
      `/campaigns/${campaignId}/sections/${sectionId}`,
      data
    );
    return response.data;
  } catch (error) {
    console.error(`Error updating section ID ${sectionId} for campaign ID ${campaignId}:`, error);
    throw error;
  }
};

// Generate Table of Contents for a campaign
export const generateCampaignTOC = async (campaignId: string | number, payload: LLMGenerationPayload): Promise<Campaign> => {
  try {
    const response = await apiClient.post<Campaign>(`/campaigns/${campaignId}/toc`, payload);
    return response.data;
  } catch (error) {
    console.error(`Error generating TOC for campaign ID ${campaignId}:`, error);
    throw error;
  }
};

// Define the response type for generating titles
export interface CampaignTitlesResponse {
  titles: string[];
}

// Generate alternative titles for a campaign
export const generateCampaignTitles = async (campaignId: string | number, payload: LLMGenerationPayload, count?: number): Promise<CampaignTitlesResponse> => {
  try {
    const params = count ? { count } : {};
    const response = await apiClient.post<CampaignTitlesResponse>(
      `/campaigns/${campaignId}/titles`,
      payload,
      { params }
    );
    return response.data;
  } catch (error) {
    console.error(`Error generating titles for campaign ID ${campaignId}:`, error);
    throw error;
  }
};

// Define the payload for creating a new section
export interface CampaignSectionCreatePayload {
  title?: string | null;
  prompt?: string | null;
  model_id_with_prefix?: string | null;
}

// Add a new section to a campaign
export const addCampaignSection = async (
  campaignId: string | number,
  data: CampaignSectionCreatePayload
): Promise<CampaignSection> => { 
  try {
    const response = await apiClient.post<CampaignSection>(
      `/campaigns/${campaignId}/sections`,
      data
    );
    return response.data;
  } catch (error) {
    console.error(`Error adding section to campaign ID ${campaignId}:`, error);
    throw error;
  }
};

// Export campaign to Homebrewery Markdown (download)
export const exportCampaignToHomebrewery = async (campaignId: string | number): Promise<string> => {
  try {
    const response = await apiClient.get<string>(
      `/campaigns/${campaignId}/export/homebrewery`,
      {
        responseType: 'text', 
      }
    );
    return response.data; 
  } catch (error) {
    console.error(`Error exporting campaign ID ${campaignId} to Homebrewery:`, error);
    throw error;
  }
};

// --- New Functionality for "Direct Posting" Preparation ---
export interface PrepareHomebreweryPostResponse {
    markdown_content: string;
    homebrewery_new_url: string;
    filename_suggestion: string;
    notes?: string;
}

/**
 * Prepares campaign content for manual posting to Homebrewery.
 * Fetches the full Markdown content and a link to Homebrewery's "new brew" page.
 * @param campaignId The ID of the campaign to prepare.
 * @returns A promise that resolves to PrepareHomebreweryPostResponse.
 */
export const prepareCampaignForHomebrewery = async (campaignId: string | number): Promise<PrepareHomebreweryPostResponse> => {
    try {
        const response = await apiClient.get<PrepareHomebreweryPostResponse>(`/campaigns/${campaignId}/prepare_for_homebrewery`);
        return response.data;
    } catch (error) {
        console.error(`Error preparing campaign ID ${campaignId} for Homebrewery posting:`, error);
        // In a real app, you might want to transform the error or log it to a service
        throw error;
    }
};
// --- End New Functionality ---


// Fetch sections for a specific campaign
export const getCampaignSections = async (campaignId: string | number): Promise<CampaignSection[]> => {
  try {
    const response = await apiClient.get<{ sections: CampaignSection[] }>(`/campaigns/${campaignId}/sections`);
    // Ensure that the response structure matches what's expected.
    // If backend returns an object like { "sections": [...] }, then access response.data.sections.
    // If backend returns the array directly, then response.data is the array.
    // Based on existing list_campaign_sections in backend, it should be { "sections": [...] }
    if (response.data && Array.isArray((response.data as any).sections)) {
        return (response.data as any).sections;
    }
    // Fallback if the structure is different or if response.data is already the array
    // This part might need adjustment based on actual backend response for this specific endpoint
    // if (Array.isArray(response.data)) {
    //     return response.data;
    // }
    console.warn("Unexpected response structure for getCampaignSections:", response.data);
    return []; // Or throw an error
  } catch (error) {
    console.error(`Error fetching sections for campaign ID ${campaignId}:`, error);
    throw error;
  }
};

// apiClient.ts should be something like:
// import axios from 'axios';
// const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
// const apiClient = axios.create({
//   baseURL: API_BASE_URL,
// });
// export default apiClient;

// Note: Corrected ModelInfo id type from `str` to `string`.
// Added `model_id_with_prefix_for_concept` to `CampaignCreatePayload`.
// Standardized `LLMGenerationPayload` for TOC and Titles generation.
// Corrected `addCampaignSection` payload to match backend `CampaignSectionCreateInput`.
// Corrected `getCampaignSections` to expect `{ sections: [...] }` based on backend.
// The problematic text block below this line has been removed.

export async function getLLMModels(): Promise<ModelInfo[]> { // Added return type
  // Use process.env.REACT_APP_API_BASE_URL, consistent with apiClient.ts (implicitly)
  // Fallback is provided if the env var is not set.
  // Ensure no double slashes if REACT_APP_API_BASE_URL has a trailing slash.
  const baseUrl = (process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');
  const response = await fetch(`${baseUrl}/llm/models`);
  if (!response.ok) {
    // Optionally, log more details from response if needed for debugging
    // const errorBody = await response.text();
    // console.error(`Failed to fetch LLM models. Status: ${response.status}. Body: ${errorBody}`);
    throw new Error('Failed to fetch LLM models');
  }
  const data = await response.json();
  // Ensure data exists and data.models is an array before returning, otherwise return empty array.
  return (data && Array.isArray(data.models)) ? data.models : [];
}
