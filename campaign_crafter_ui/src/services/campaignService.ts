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
export interface ModelInfo {
  id: str;
  name: str;
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
}

export interface CampaignUpdatePayload {
  title?: string;
  initial_user_prompt?: string;
  // Concept is not directly updatable via this payload as per current backend
}

// Fetch all campaigns
export const getAllCampaigns = async (): Promise<Campaign[]> => {
  try {
    const response = await apiClient.get<Campaign[]>('/campaigns/');
    return response.data;
  } catch (error) {
    console.error('Error fetching campaigns:', error);
    // In a real app, you might want to transform the error or log it to a service
    throw error; 
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

// Add other service functions as needed (update, delete, etc.)

// Update an existing campaign
export const updateCampaign = async (campaignId: string | number, campaignData: CampaignUpdatePayload): Promise<Campaign> => {
  try {
    // The backend PUT endpoint for campaigns currently uses CampaignCreate model,
    // which means both title and initial_user_prompt might be expected.
    // If the backend allows partial updates with this model, this is fine.
    // If not, the backend might need a different Pydantic model for PATCH,
    // or this payload needs to ensure all fields expected by CampaignCreate are sent.
    // For now, proceeding with the assumption that the backend can handle this payload for PUT.
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

// export const deleteCampaign = async (campaignId: string | number): Promise<void> => { ... }

// Generate Table of Contents for a campaign
export const generateCampaignTOC = async (campaignId: string | number): Promise<Campaign> => {
  try {
    const response = await apiClient.post<Campaign>(`/campaigns/${campaignId}/toc`);
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
export const generateCampaignTitles = async (campaignId: string | number, count?: number): Promise<CampaignTitlesResponse> => {
  try {
    const params = count ? { count } : {};
    const response = await apiClient.post<CampaignTitlesResponse>(
      `/campaigns/${campaignId}/titles`,
      null, // No request body for this POST, params are query params
      { params }
    );
    return response.data;
  } catch (error) {
    console.error(`Error generating titles for campaign ID ${campaignId}:`, error);
    throw error;
  }
};

// Define the payload for creating a new section (client-side)
// Matches backend's CampaignSectionCreateInput
export interface CampaignSectionCreateClientPayload {
  title?: string;
  prompt?: string;
  modelId?: string; // Add modelId
  temperature?: number; // Add temperature (conceptual for now)
}

// Add a new section to a campaign
export const addCampaignSection = async (
  campaignId: string | number,
  data: CampaignSectionCreateClientPayload
): Promise<CampaignSection> => { 
  try {
    // Prepare backend payload, mapping modelId to model
    const backendPayload: { title?: string; prompt?: string; model?: string; /* temperature not yet sent */ } = {
        title: data.title,
        prompt: data.prompt,
        model: data.modelId, 
    };
    const response = await apiClient.post<CampaignSection>(
      `/campaigns/${campaignId}/sections`,
      backendPayload // Send the transformed payload
    );
    return response.data;
  } catch (error) {
    console.error(`Error adding section to campaign ID ${campaignId}:`, error);
    throw error;
  }
};

// Generate Table of Contents for a campaign
export const generateCampaignTOC = async (campaignId: string | number, modelId?: string, temperature?: number): Promise<Campaign> => {
  try {
    const payload = { model: modelId /*, temperature */ }; // Temperature conceptual for now
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
export const generateCampaignTitles = async (campaignId: string | number, modelId?: string, count?: number, temperature?: number): Promise<CampaignTitlesResponse> => {
  try {
    const payload = { model: modelId /*, temperature */ }; // Temperature conceptual for now
    const params = count ? { count } : {}; // Count remains a query parameter
    const response = await apiClient.post<CampaignTitlesResponse>(
      `/campaigns/${campaignId}/titles`,
      payload, // Send modelId in body
      { params }
    );
    return response.data;
  } catch (error) {
    console.error(`Error generating titles for campaign ID ${campaignId}:`, error);
    throw error;
  }
};

// Fetch available LLM Models
export const getLLMModels = async (): Promise<ModelInfo[]> => {
  try {
    const response = await apiClient.get<{models: ModelInfo[]}>('/llm/models');
    return response.data.models;
  } catch (error) {
    console.error('Error fetching LLM models:', error);
    throw error;
  }
};

// Export campaign to Homebrewery Markdown
export const exportCampaignToHomebrewery = async (campaignId: string | number): Promise<string> => {
  try {
    const response = await apiClient.get<string>( // Expect a string response
      `/campaigns/${campaignId}/export/homebrewery`,
      {
        responseType: 'text', // Important: ensures Axios handles the response as plain text
        // The backend already sets Content-Disposition and media-type,
        // but responseType: 'text' helps Axios parse it correctly from the start.
      }
    );
    return response.data; // This should be the raw Markdown string
  } catch (error) {
    console.error(`Error exporting campaign ID ${campaignId} to Homebrewery:`, error);
    throw error;
  }
};


// Fetch sections for a specific campaign
export const getCampaignSections = async (campaignId: string | number): Promise<CampaignSection[]> => {
  try {
    const response = await apiClient.get<{ sections: CampaignSection[] }>(`/campaigns/${campaignId}/sections`);
    return response.data.sections; // The backend returns { "sections": [...] }
  } catch (error) {
    console.error(`Error fetching sections for campaign ID ${campaignId}:`, error);
    throw error;
  }
};
