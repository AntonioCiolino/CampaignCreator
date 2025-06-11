// Defines the structure of an LLM model object
export interface LLMModel {
  id: string; // Prefixed ID, e.g., "openai/gpt-3.5-turbo"
  name: string; // User-friendly name, e.g., "OpenAI GPT-3.5 Turbo"
  capabilities?: string[]; // Added optional capabilities field
}

// Defines the structure of the response from the /api/llm/models endpoint
interface LLMModelsResponse {
  models: LLMModel[];
}

// const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
// API_BASE_URL will be handled by apiClient
import apiClient from './apiClient';


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

export interface ImageGenerationRequest {
  prompt: string;
  size?: string | null;    // e.g., "1024x1024", "1792x1024", "1024x1792" for DALL-E 3
  quality?: string | null; // e.g., "standard", "hd" for DALL-E 3
  model?: string | null;   // e.g., "dall-e-3", "dall-e-2"
  // style?: string | null; // Optional: "vivid", "natural" for DALL-E 3
}

export interface ImageGenerationResponse {
  image_url: string; // HttpUrl from Pydantic will be a string here
  prompt_used: string;
  model_used: string;
  size_used: string;
  quality_used: string;
  // revised_prompt?: string | null; // If backend sends it
}

/**
 * Generates an image using the backend's DALL-E service.
 * @param request The image generation parameters.
 * @returns A promise that resolves to the image generation response.
 * @throws Will throw an error if the network request fails or the API returns an error.
 */
export const generateImage = async (request: ImageGenerationRequest): Promise<ImageGenerationResponse> => {
  try {
    // Construct body, only including optional fields if they have values
    const requestBody: Record<string, any> = { prompt: request.prompt };
    if (request.model) requestBody.model = request.model;
    if (request.size) requestBody.size = request.size;
    if (request.quality) requestBody.quality = request.quality;
    // if (request.style) requestBody.style = request.style;

    // New apiClient call:
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
