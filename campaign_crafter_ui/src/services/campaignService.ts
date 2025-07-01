import axios from 'axios';
import apiClient from './apiClient';
import { fetchEventSource, EventSourceMessage } from '@microsoft/fetch-event-source';
import { BlobFileMetadata } from '../types/fileTypes';
import {
    Campaign,
    CampaignCreatePayload,
    CampaignUpdatePayload,
    CampaignSection,
    CampaignSectionCreatePayload,
    CampaignSectionUpdatePayload,
    CampaignTitlesResponse,
    LLMGenerationPayload,
    PrepareHomebreweryPostResponse,
    SeedSectionsCallbacks,
    SeedSectionsEvent,
    SectionRegeneratePayload,
    TOCEntry // Assuming TOCEntry is also needed by Campaign model here
    // ModelInfo might be needed if Campaign type references it, or by other functions.
} from '../types/campaignTypes';

// Fetch all campaigns
export const getAllCampaigns = async (): Promise<Campaign[]> => {
  try {
    const response = await apiClient.get<Campaign[] | null>('/api/v1/campaigns/');
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    console.error('Error details in campaignService.getAllCampaigns:', error);
    if (axios.isAxiosError(error)) {
        console.error('Axios error response status:', error.response?.status);
        console.error('Axios error response data:', error.response?.data);
        console.error('Axios error request config:', error.config);
    }
    throw error;
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
export const getCampaignFiles = async (campaignId: string): Promise<BlobFileMetadata[]> => {
  console.log(`[campaignService.getCampaignFiles] Fetching files for campaign ID: ${campaignId}`);
  try {
    const response = await apiClient.get<BlobFileMetadata[]>(`/api/v1/campaigns/${campaignId}/files`);
    console.log(`[campaignService.getCampaignFiles] Successfully fetched files for campaign ${campaignId}:`, response.data);
    return response.data;
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

export const deleteCampaignFile = async (campaignId: string, fileName: string): Promise<void> => {
  console.log(`[campaignService.deleteCampaignFile] Deleting file: ${fileName} for campaign ID: ${campaignId}`);
  try {
    await apiClient.delete(`/api/v1/campaigns/${campaignId}/files/${fileName}`);
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
  } catch (error) {
    console.error(`Error deleting section ID ${sectionId} for campaign ID ${campaignId}:`, error);
    throw error;
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

export const prepareCampaignForHomebrewery = async (campaignId: string | number): Promise<PrepareHomebreweryPostResponse> => {
    try {
        const response = await apiClient.get<PrepareHomebreweryPostResponse>(`/api/v1/campaigns/${campaignId}/prepare_for_homebrewery`);
        return response.data;
    } catch (error) {
        console.error(`Error preparing campaign ID ${campaignId} for Homebrewery posting:`, error);
        throw error;
    }
};

export const getCampaignSections = async (campaignId: string | number): Promise<CampaignSection[]> => {
  try {
    const response = await apiClient.get<{ sections: CampaignSection[] }>(`/api/v1/campaigns/${campaignId}/sections`);
    if (response.data && Array.isArray((response.data as any).sections)) {
        return (response.data as any).sections;
    }
    console.warn("Unexpected response structure for getCampaignSections:", response.data);
    return [];
  } catch (error) {
    console.error(`Error fetching sections for campaign ID ${campaignId}:`, error);
    throw error;
  }
};

export const updateCampaignSectionOrder = async (
  campaignId: string | number,
  section_ids: number[]
): Promise<void> => {
  try {
    await apiClient.put(`/api/v1/campaigns/${campaignId}/sections/order`, { section_ids });
  } catch (error) {
    console.error(`Error updating section order for campaign ID ${campaignId}:`, error);
    throw error;
  }
};

export const seedSectionsFromToc = (
  campaignId: string | number,
  autoPopulate: boolean,
  callbacks: SeedSectionsCallbacks
): (() => void) => {
  const baseUrl = (process.env.REACT_APP_API_BASE_URL || apiClient.defaults.baseURL || window.location.origin).replace(/\/$/, '');
  const endpointPath = `/api/v1/campaigns/${campaignId}/seed_sections_from_toc?auto_populate=${autoPopulate}`;
  const url = `${baseUrl}${endpointPath}`;
  const controller = new AbortController();
  const requestHeaders: Record<string, string> = {
    'Accept': 'text/event-stream',
    'Content-Type': 'application/json',
  };
  const token = localStorage.getItem('token');
  if (token) {
    requestHeaders['Authorization'] = `Bearer ${token}`;
  } else {
    console.warn("No auth token found in localStorage for SSE request.");
  }

  fetchEventSource(url, {
    method: 'POST',
    headers: requestHeaders,
    body: JSON.stringify({}),
    signal: controller.signal,
    onopen: async (response) => {
      if (response.ok) {
        callbacks.onOpen?.(new Event('open'));
      } else {
        const errorPayload = { message: `Failed to open SSE connection: ${response.status} ${response.statusText}` };
        try {
             const errorBody = await response.json();
             if (errorBody && errorBody.detail) {
                 errorPayload.message = typeof errorBody.detail === 'string' ? errorBody.detail : JSON.stringify(errorBody.detail);
             }
        } catch(e) { /* ignore */ }
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
      const prefix = "data: ";
      if (jsonData.startsWith(prefix)) {
        jsonData = jsonData.substring(prefix.length);
      }
      try {
        const parsedData = JSON.parse(jsonData) as SeedSectionsEvent;
        if (parsedData.event_type === "section_update") {
          callbacks.onProgress?.(parsedData);
          if (parsedData.section_data) {
            callbacks.onSectionComplete?.(parsedData.section_data);
          }
        } else if (parsedData.event_type === "complete") {
          callbacks.onDone?.(parsedData.message, parsedData.total_sections_processed);
        } else {
          console.warn("Received unknown SSE event type:", parsedData);
        }
      } catch (e) {
        console.error("Failed to parse SSE event data:", jsonData, e);
        callbacks.onError?.({ message: "Failed to parse event data: " + String(jsonData) });
      }
    },
    onclose: () => {
      console.log("SSE Connection Closed for seedSectionsFromToc.");
    },
    onerror: (err: any) => {
      console.error("SSE Error for seedSectionsFromToc:", err);
      callbacks.onError?.({ message: err.message || "An unknown error occurred with SSE connection." });
      throw err;
    }
  });
  return () => {
    console.log("Aborting SSE connection for seedSectionsFromToc.");
    controller.abort();
  };
};

export const regenerateCampaignSection = async (
  campaignId: string | number,
  sectionId: number,
  payload?: SectionRegeneratePayload
): Promise<CampaignSection> => {
  try {
    const response = await apiClient.post<CampaignSection>(
      `/api/v1/campaigns/${campaignId}/sections/${sectionId}/regenerate`,
      payload || {}
    );
    return response.data;
  } catch (error) {
    console.error(`Error regenerating section ID ${sectionId} for campaign ID ${campaignId}:`, error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || `Failed to regenerate section: ${error.message}`);
    }
    throw error;
  }
};

export const generateCampaignConcept = async (
  campaignId: string | number,
  payload: LLMGenerationPayload
): Promise<Campaign> => {
  try {
    const response = await apiClient.post<Campaign>(`/api/v1/campaigns/${campaignId}/generate-concept`, payload);
    return response.data;
  } catch (error) {
    console.error(`Error generating concept for campaign ID ${campaignId}:`, error);
    throw error;
  }
};
