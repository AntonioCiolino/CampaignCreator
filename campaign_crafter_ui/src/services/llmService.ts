import apiClient from './apiClient';

// Defines the structure of an LLM model object
export interface LLMModel {
  id: string; // Prefixed ID, e.g., "openai/gpt-3.5-turbo"
  name: string; // User-friendly name, e.g., "OpenAI GPT-3.5 Turbo"
  model_type: string; // Added model_type field
  supports_temperature: boolean; // Added supports_temperature field
  capabilities?: string[]; // Added optional capabilities field
}

// Defines the structure of the response from the /api/llm/models endpoint
interface LLMModelsResponse {
  models: LLMModel[];
}

// const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
// API_BASE_URL will be handled by apiClient


/**
 * Fetches the list of available LLM models from the backend.
 * @returns A promise that resolves to an array of LLMModel objects.
 * @throws Will throw an error if the network request fails or the API returns an error.
 */
export const getAvailableLLMs = async (): Promise<LLMModel[]> => {
  try {
    // Assuming /api/v1/llm/models is public and doesn't need auth,
    // using apiClient here for consistency in base URL handling.
    // If it strictly needs to be fetch without any auth headers apiClient might add,
    // then the original fetch was fine, just ensure API_BASE_URL is correct.
    // For now, let's switch to apiClient for base URL consistency.
    const response = await apiClient.get<LLMModelsResponse>('/api/v1/llm/models');

    // Axios automatically checks for response.ok and throws for non-2xx.
    // It also parses JSON by default.
    // We might still want to check Content-Type if strict validation is needed,
    // but usually apiClient handles this.

    if (!response.data || !response.data.models) {
        console.warn('No models found in response or unexpected structure:', response.data);
        return []; 
    }
    return response.data.models;

  } catch (error: any) {
    console.error("Error fetching available LLM models:", error);
    if (error.response && error.response.data && error.response.data.detail) {
        throw new Error(error.response.data.detail);
    } else if (error.message) {
        throw new Error(error.message);
    }
    throw new Error("An unknown error occurred while fetching LLM models.");
  }
};

export interface LLMTextGenerationParams {
    prompt: string;
    model_id_with_prefix?: string | null; 
    temperature?: number;
    max_tokens?: number;
    chat_history?: Array<{ speaker: string; text: string; }>; // Added chat_history

    // New optional fields for campaign context
    campaign_id?: number | null;
    section_title_suggestion?: string | null;
    section_type?: string | null;
    section_creation_prompt?: string | null; // Added missing field
}

export interface LLMTextGenerationResponse {
    text: string;
    model_used?: string; 
}

export const generateTextLLM = async (params: LLMTextGenerationParams): Promise<LLMTextGenerationResponse> => {
    try {
        const requestBody: Record<string, any> = {
            prompt: params.prompt,
        };
        if (params.model_id_with_prefix) {
            requestBody.model_id_with_prefix = params.model_id_with_prefix;
        }
        if (params.temperature !== undefined) {
            requestBody.temperature = params.temperature;
        }
        if (params.max_tokens !== undefined) {
            requestBody.max_tokens = params.max_tokens;
        }
        if (params.chat_history) { // Add chat_history to the request body if present
            requestBody.chat_history = params.chat_history;
        }

        // Add new context fields if provided
        if (params.campaign_id !== undefined && params.campaign_id !== null) {
            requestBody.campaign_id = params.campaign_id;
        }
        if (params.section_title_suggestion) {
            requestBody.section_title_suggestion = params.section_title_suggestion;
        }
        if (params.section_type) {
            requestBody.section_type = params.section_type;
        }

        // New apiClient call:
        const response = await apiClient.post<LLMTextGenerationResponse>('/api/v1/llm/generate-text', requestBody);
        return response.data; // Axios wraps the response in a `data` object

    } catch (error: any) { // Axios errors can be handled more specifically if needed
        console.error("Error generating text with LLM:", error);
        if (error.response && error.response.data && error.response.data.detail) {
            throw new Error(error.response.data.detail);
        } else if (error.message) {
            throw new Error(error.message);
        }
        throw new Error("An unknown error occurred during text generation.");
    }
};

// --- New Image Generation Interfaces and Function ---

// Matches ImageModelName enum in the backend
export type ImageModelName = "dall-e" | "stable-diffusion" | "gemini";

export interface ImageGenerationParams { // Renamed from ImageGenerationRequest for clarity if used elsewhere
  prompt: string;
  model: ImageModelName; // Use the defined type
  size?: string | null;
  // DALL-E specific
  quality?: string | null;
  // style?: string | null; // DALL-E 3 specific, if added later

  // Stable Diffusion specific
  steps?: number | null;
  cfg_scale?: number | null;
  // sd_model_checkpoint?: string | null; // If UI allows selecting SD model

  // Gemini specific
  gemini_model_name?: string | null;

  // Campaign ID for associating the image
  campaign_id?: string; // Changed from campaignId to match backend snake_case
}

export interface ImageGenerationResponse {
  image_url: string;
  prompt_used: string;
  model_used: ImageModelName; // Reflects the primary model type used
  size_used: string;
  // DALL-E specific response fields
  quality_used?: string | null;
  // revised_prompt?: string | null; // DALL-E 3 might return this

  // Stable Diffusion specific response fields
  steps_used?: number | null;
  cfg_scale_used?: number | null;
  // sd_model_checkpoint_used?: string | null;

  // Gemini specific response fields
  gemini_model_name_used?: string | null;
}

/**
 * Generates an image using the backend's image generation service.
 * @param params The image generation parameters.
 * @returns A promise that resolves to the image generation response.
 * @throws Will throw an error if the network request fails or the API returns an error.
 */
export const generateImage = async (params: ImageGenerationParams): Promise<ImageGenerationResponse> => {
  try {
    // Construct body, including only relevant fields for the selected model
    const requestBody: Record<string, any> = {
      prompt: params.prompt,
      model: params.model, // This now refers to "dall-e", "stable-diffusion", or "gemini"
    };

    if (params.size) requestBody.size = params.size;

    if (params.model === "dall-e") {
      if (params.quality) requestBody.quality = params.quality;
      // Potentially add DALL-E specific model name if backend needs it, e.g. "dall-e-3" vs "dall-e-2"
      // This is currently handled by backend settings for OPENAI_DALLE_MODEL_NAME
    } else if (params.model === "stable-diffusion") {
      if (params.steps) requestBody.steps = params.steps;
      if (params.cfg_scale) requestBody.cfg_scale = params.cfg_scale;
      // if (params.sd_model_checkpoint) requestBody.sd_model_checkpoint = params.sd_model_checkpoint;
    } else if (params.model === "gemini") {
      if (params.gemini_model_name) requestBody.gemini_model_name = params.gemini_model_name;
    }

    // Add campaign_id if present in params
    if (params.campaign_id) {
      requestBody.campaign_id = params.campaign_id;
    }

    const response = await apiClient.post<ImageGenerationResponse>('/api/v1/images/generate', requestBody);
    return response.data;

  } catch (error: any) {
    console.error("Error generating image:", error);
    if (error.response && error.response.data && error.response.data.detail) {
        throw new Error(error.response.data.detail);
    } else if (error.message) {
        throw new Error(error.message);
    }
    throw new Error("An unknown error occurred during image generation.");
  }
};
// --- End New Image Generation ---
