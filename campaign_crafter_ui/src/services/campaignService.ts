import axios from 'axios';
import apiClient from './apiClient';
import { fetchEventSource, EventSourceMessage } from '@microsoft/fetch-event-source';
import { BlobFileMetadata } from '../types/fileTypes'; // Moved import to top

// Types matching backend Pydantic models
export interface TOCEntry {
  title: string;
  type: string; // Could be 'unknown' or a specific type like 'NPC', 'Location'
}

export interface CampaignSection {
  id: number;
  title: string | null;
  content: string;
  order: number;
  campaign_id: number;
  type?: string; // Added type field, optional as it might not be present in all contexts initially
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
  homebrewery_toc: TOCEntry[] | null; // Changed from string | null
  display_toc: TOCEntry[] | null; // Changed from string | null
  badge_image_url?: string | null; // Added
  thematic_image_url?: string | null;
  thematic_image_prompt?: string | null;
  selected_llm_id?: string | null;
  temperature?: number | null;
  // owner_id: number; 
  // sections: CampaignSection[]; // Backend doesn't nest this in the Campaign Pydantic model by default

  // New Theme Properties
  theme_primary_color?: string | null;
  theme_secondary_color?: string | null;
  theme_background_color?: string | null;
  theme_text_color?: string | null;
  theme_font_family?: string | null;
  theme_background_image_url?: string | null;
  theme_background_image_opacity?: number | null;

  // Mood Board URLs
  mood_board_image_urls?: string[] | null;
}

export interface CampaignCreatePayload {
  title: string;
  initial_user_prompt?: string; // Made optional as it can be undefined if skipping
  skip_concept_generation?: boolean; // New field
  model_id_with_prefix_for_concept?: string | null; // Added based on backend changes
  badge_image_url?: string | null;
  selected_llm_id?: string | null;
  temperature?: number | null;
  thematic_image_url?: string | null;
  thematic_image_prompt?: string | null;

  // New Theme Properties
  theme_primary_color?: string | null;
  theme_secondary_color?: string | null;
  theme_background_color?: string | null;
  theme_text_color?: string | null;
  theme_font_family?: string | null;
  theme_background_image_url?: string | null;
  theme_background_image_opacity?: number | null;

  // Mood Board URLs
  mood_board_image_urls?: string[] | null;
}

export interface CampaignUpdatePayload {
  title?: string;
  initial_user_prompt?: string;
  badge_image_url?: string | null; // Added
  thematic_image_url?: string | null;
  thematic_image_prompt?: string | null;
  selected_llm_id?: string | null;
  temperature?: number | null;
  display_toc?: TOCEntry[] | null; // Added
  homebrewery_toc?: TOCEntry[] | null; // Added
  concept?: string | null; // Added field for direct concept updates
  // Concept is typically updated via specific generation endpoints // Comment might be partially outdated

  // New Theme Properties
  theme_primary_color?: string | null;
  theme_secondary_color?: string | null;
  theme_background_color?: string | null;
  theme_text_color?: string | null;
  theme_font_family?: string | null;
  theme_background_image_url?: string | null;
  theme_background_image_opacity?: number | null;

  // Mood Board URLs
  mood_board_image_urls?: string[] | null;
}

// For LLM Generation requests common to TOC, Titles, etc.
export interface LLMGenerationPayload {
    prompt: string;
    model_id_with_prefix?: string | null;
    // temperature?: number; // If you want to control this from client
}

// Fetch all campaigns
export const getAllCampaigns = async (): Promise<Campaign[]> => {
  try {
    const response = await apiClient.get<Campaign[] | null>('/api/v1/campaigns/'); // Expect Campaign[] or null
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
        const response = await apiClient.get<Campaign>(`/api/v1/campaigns/${campaignId}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching campaign with ID ${campaignId}:`, error);
        throw error;
    }
};

// Create a new campaign
export const createCampaign = async (campaignData: CampaignCreatePayload): Promise<Campaign> => {
    try {
        const response = await apiClient.post<Campaign>('/api/v1/campaigns/', campaignData);
        return response.data;
    } catch (error) {
        console.error('Error creating campaign:', error);
        throw error;
    }
};

// Update an existing campaign
export const updateCampaign = async (campaignId: string | number, campaignData: CampaignUpdatePayload): Promise<Campaign> => {
  try {
    const response = await apiClient.put<Campaign>(`/api/v1/campaigns/${campaignId}`, campaignData);
    return response.data;
  } catch (error) {
    console.error(`Error updating campaign with ID ${campaignId}:`, error);
    throw error;
  }
};

// --- Campaign Files ---
/**
 * Fetches the list of files for a specific campaign.
 * @param campaignId The ID of the campaign.
 * @returns A promise that resolves to an array of BlobFileMetadata.
 */
export const getCampaignFiles = async (campaignId: string): Promise<BlobFileMetadata[]> => {
  console.log(`[campaignService.getCampaignFiles] Fetching files for campaign ID: ${campaignId}`);
  try {
    const response = await apiClient.get<BlobFileMetadata[]>(`/api/v1/campaigns/${campaignId}/files`);
    console.log(`[campaignService.getCampaignFiles] Successfully fetched files for campaign ${campaignId}:`, response.data);
    return response.data; // Consistent with other functions in this service
  } catch (error: any) {
    console.error(`[campaignService.getCampaignFiles] Error fetching files for campaign ${campaignId}:`, error.response?.data || error.message || error);
    const detail = error.response?.data?.detail;
    let errorMessage = `Failed to fetch files for campaign ${campaignId}.`;
    if (typeof detail === 'string') {
      errorMessage = detail;
    } else if (Array.isArray(detail) && detail.length > 0 && typeof detail[0].msg === 'string') {
      errorMessage = detail[0].msg;
    } else if (error.message) {
      errorMessage = error.message;
    }
    throw new Error(errorMessage);
  }
};

/**
 * Deletes a specific file from a campaign.
 * @param campaignId The ID of the campaign.
 * @param fileName The name of the file (blob_name) to delete.
 * @returns A promise that resolves when the file is deleted.
 */
export const deleteCampaignFile = async (campaignId: string, fileName: string): Promise<void> => {
  console.log(`[campaignService.deleteCampaignFile] Deleting file: ${fileName} for campaign ID: ${campaignId}`);
  try {
    // The backend endpoint expects the filename as a path parameter.
    // Ensure the URL is correctly formed, e.g., /api/v1/campaigns/{campaign_id}/files/{file_name}
    // The file_name path parameter in FastAPI needs to be able to handle paths with slashes if blob_name contains them.
    // This might require the file_name to be URL-encoded if it contains special characters or slashes.
    // However, if file.name from BlobFileMetadata is just the final segment (e.g., "image.png"), direct use is fine.
    // If file.name is the full blob path (e.g., "user_uploads/.../image.png"), it needs to be handled carefully.
    // Assuming for now `fileName` is the part that uniquely identifies the file to the backend endpoint.
    // If the backend route is `/api/v1/campaigns/{campaign_id}/files/{blob_name:path}`, then `fileName` can be the full path.
    // Let's assume `fileName` is the unique identifier the backend expects (e.g., the base name or full blob path if the route supports it).
    // For a simple case where `fileName` is just the end part:
    // const response = await apiClient.delete(`/api/v1/campaigns/${campaignId}/files/${encodeURIComponent(fileName)}`);
    // If `fileName` is expected to be the full blob path and the route is set up for it (e.g. using :path converter):
    const response = await apiClient.delete(`/api/v1/campaigns/${campaignId}/files/${fileName}`); // Assuming fileName is the blob_name

    // console.log(`[campaignService.deleteCampaignFile] File "${fileName}" deleted successfully for campaign ${campaignId}. Status: ${response.status}`); // Backend returns 204
    // No need to return response.data for a 204 No Content
  } catch (error: any) {
    console.error(`[campaignService.deleteCampaignFile] Error deleting file "${fileName}" for campaign ${campaignId}:`, error.response?.data || error.message || error);
    const detail = error.response?.data?.detail;
    let errorMessage = `Failed to delete file "${fileName}".`;
    if (typeof detail === 'string') {
      errorMessage = detail;
    } else if (Array.isArray(detail) && detail.length > 0 && typeof detail[0].msg === 'string') {
      errorMessage = detail[0].msg;
    } else if (error.message) {
      errorMessage = error.message;
    }
    throw new Error(errorMessage);
  }
};
// --- End Campaign Files ---

// Define the payload for updating a section
// Removed ImageData interface

export interface CampaignSectionUpdatePayload {
  title?: string;
  content?: string;
  order?: number;
  type?: string; // Added type field
  // Removed images field
}

// Update a specific campaign section
export const updateCampaignSection = async (
  campaignId: string | number,
  sectionId: string | number,
  data: CampaignSectionUpdatePayload
): Promise<CampaignSection> => {
  try {
    const response = await apiClient.put<CampaignSection>(
      `/api/v1/campaigns/${campaignId}/sections/${sectionId}`,
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
    const response = await apiClient.post<Campaign>(`/api/v1/campaigns/${campaignId}/toc`, payload);
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
      `/api/v1/campaigns/${campaignId}/titles`,
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
      `/api/v1/campaigns/${campaignId}/sections`,
      data
    );
    return response.data;
  } catch (error) {
    console.error(`Error adding section to campaign ID ${campaignId}:`, error);
    throw error;
  }
};

// Delete a specific campaign section
export const deleteCampaignSection = async (campaignId: string | number, sectionId: string | number): Promise<void> => {
  try {
    await apiClient.delete(`/api/v1/campaigns/${campaignId}/sections/${sectionId}`);
    // No specific data is expected to be returned on successful DELETE for this void function
  } catch (error) {
    console.error(`Error deleting section ID ${sectionId} for campaign ID ${campaignId}:`, error);
    throw error; // Re-throw to be handled by the calling component
  }
};

// Export campaign to Homebrewery Markdown (download)
export const exportCampaignToHomebrewery = async (campaignId: string | number): Promise<string> => {
  try {
    const response = await apiClient.get<string>(
      `/api/v1/campaigns/${campaignId}/export/homebrewery`,
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
        const response = await apiClient.get<PrepareHomebreweryPostResponse>(`/api/v1/campaigns/${campaignId}/prepare_for_homebrewery`);
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
    const response = await apiClient.get<{ sections: CampaignSection[] }>(`/api/v1/campaigns/${campaignId}/sections`);
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

// Update the order of sections in a campaign
export const updateCampaignSectionOrder = async (
  campaignId: string | number,
  section_ids: number[] // Array of section IDs in the new order
): Promise<void> => {
  try {
    await apiClient.put(`/api/v1/campaigns/${campaignId}/sections/order`, { section_ids });
    // The endpoint returns 204 No Content, so no data to return here.
  } catch (error) {
    console.error(`Error updating section order for campaign ID ${campaignId}:`, error);
    throw error;
  }
};

// --- Server-Sent Events (SSE) for Seeding Sections ---

export interface SeedSectionsProgressEvent {
  event_type: "section_update";
  progress_percent: number;
  current_section_title: string;
  section_data: CampaignSection;
}

export interface SeedSectionsCompleteEvent {
  event_type: "complete";
  message: string;
  total_sections_processed: number; // Added to match backend
}

export type SeedSectionsEvent = SeedSectionsProgressEvent | SeedSectionsCompleteEvent;

export interface SeedSectionsCallbacks {
  onOpen?: (event: Event) => void;
  onProgress?: (data: SeedSectionsProgressEvent) => void;
  onSectionComplete?: (data: CampaignSection) => void; // For convenience
  onDone?: (message: string, totalProcessed: number) => void;
  onError?: (error: Event | { message: string }) => void;
}

export const seedSectionsFromToc = (
  campaignId: string | number,
  autoPopulate: boolean,
  callbacks: SeedSectionsCallbacks
): (() => void) => { // Returns an abort function
  const baseUrl = (process.env.REACT_APP_API_BASE_URL || apiClient.defaults.baseURL || window.location.origin).replace(/\/$/, '');
  const endpointPath = `/api/v1/campaigns/${campaignId}/seed_sections_from_toc?auto_populate=${autoPopulate}`;
  const url = `${baseUrl}${endpointPath}`;

  const controller = new AbortController();

  // Prepare headers
  const requestHeaders: Record<string, string> = {
    'Accept': 'text/event-stream',
    'Content-Type': 'application/json', // Added as body is now JSON
  };

  // Get token from localStorage
  const token = localStorage.getItem('token');
  if (token) {
    requestHeaders['Authorization'] = `Bearer ${token}`;
  } else {
    console.warn("No auth token found in localStorage for SSE request. Request will likely fail if endpoint is protected.");
  }

  fetchEventSource(url, {
    method: 'POST',
    headers: requestHeaders, // Use the prepared headers
    body: JSON.stringify({}), // Send an empty JSON body for POST, Content-Type is application/json
    signal: controller.signal,

    onopen: async (response) => {
      if (response.ok) {
        console.log("SSE Connection Opened (fetchEventSource) for seedSectionsFromToc to URL:", url);
        callbacks.onOpen?.(new Event('open'));
      } else {
        const errorPayload = { message: `Failed to open SSE connection: ${response.status} ${response.statusText}` };
        try {
             const errorBody = await response.json();
             if (errorBody && errorBody.detail) {
                 errorPayload.message = typeof errorBody.detail === 'string' ? errorBody.detail : JSON.stringify(errorBody.detail);
             }
        } catch(e) { /* ignore if body isn't json */ }
        callbacks.onError?.(errorPayload);
      }
    },
    onmessage: (event: EventSourceMessage) => {
      if (event.event === 'error') {
         callbacks.onError?.({ message: event.data || "An error event was received from server."});
         return;
      }
      if (!event.data) {
         console.warn("Received SSE message with no data:", event);
         return;
      }

      let jsonData = event.data;
      const prefix = "data: "; // Standard SSE prefix, though fetchEventSource usually strips it.
                              // This is a safeguard or for servers that might double-prefix.
      if (jsonData.startsWith(prefix)) {
        jsonData = jsonData.substring(prefix.length);
      }

      try {
        const parsedData = JSON.parse(jsonData) as SeedSectionsEvent; // Use cleaned jsonData

        if (parsedData.event_type === "section_update") {
          const progressEvent = parsedData as SeedSectionsProgressEvent;
          callbacks.onProgress?.(progressEvent);
          if (progressEvent.section_data) {
            callbacks.onSectionComplete?.(progressEvent.section_data);
          }
        } else if (parsedData.event_type === "complete") {
          const completeEvent = parsedData as SeedSectionsCompleteEvent;
          callbacks.onDone?.(completeEvent.message, completeEvent.total_sections_processed);
          // controller.abort(); // Optional: fetchEventSource might close automatically on server close.
        } else {
          console.warn("Received unknown SSE event type via fetchEventSource:", parsedData);
        }
      } catch (e) {
        console.error("Failed to parse SSE event data (fetchEventSource):", jsonData, e); // Log cleaned jsonData
        callbacks.onError?.({ message: "Failed to parse event data: " + String(jsonData) });
      }
    },
    onclose: () => {
      console.log("SSE Connection Closed (fetchEventSource) for seedSectionsFromToc.");
      // This is called when the connection is definitively closed.
      // Consider if onDone should be called here if not already by a "complete" event.
      // For example, if the server just closes the connection without a final "complete" message.
      // However, the current backend sends "complete", so this might be mostly for logging.
    },
    onerror: (err: any) => {
      console.error("SSE Error (fetchEventSource) for seedSectionsFromToc:", err);
      callbacks.onError?.({ message: err.message || "An unknown error occurred with SSE connection." });
      // fetchEventSource will retry on some errors. To stop retries, re-throw the error.
      // For this application, if an error occurs, we probably want to stop.
      throw err;
    }
  });

  return () => {
    console.log("Aborting SSE connection for seedSectionsFromToc.");
    controller.abort();
  };
};

// Payload for regenerating a section (matches backend SectionRegenerateInput)
export interface SectionRegeneratePayload {
  new_prompt?: string;
  new_title?: string;
  section_type?: string; // E.g., "NPC", "Location", "Chapter/Quest", "Generic"
  model_id_with_prefix?: string;
}

// Regenerate a specific campaign section
export const regenerateCampaignSection = async (
  campaignId: string | number,
  sectionId: number, // sectionId is a number
  payload?: SectionRegeneratePayload
): Promise<CampaignSection> => {
  try {
    const response = await apiClient.post<CampaignSection>(
      `/api/v1/campaigns/${campaignId}/sections/${sectionId}/regenerate`,
      payload || {} // Send payload or an empty object if undefined
    );
    return response.data;
  } catch (error) {
    console.error(`Error regenerating section ID ${sectionId} for campaign ID ${campaignId}:`, error);
    if (axios.isAxiosError(error) && error.response) {
      // Rethrow with more specific error message if available from backend
      throw new Error(error.response.data.detail || `Failed to regenerate section: ${error.message}`);
    }
    throw error; // Re-throw original error if not AxiosError or no response detail
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
// The standalone getLLMModels function that used process.env and fetch directly has also been removed
// to ensure consistency with API calls going through apiClient or services using getApiBaseUrl.
// Functionality for fetching LLM models is available in llmService.ts via getAvailableLLMs.

// Generate campaign concept manually
export const generateCampaignConcept = async (
  campaignId: string | number,
  payload: LLMGenerationPayload // Reuse existing payload type for prompt & model
): Promise<Campaign> => {
  try {
    // This endpoint will need to be created in the backend API
    const response = await apiClient.post<Campaign>(`/api/v1/campaigns/${campaignId}/generate-concept`, payload);
    return response.data;
  } catch (error) {
    console.error(`Error generating concept for campaign ID ${campaignId}:`, error);
    throw error;
  }
};
