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

import { getApiBaseUrl } from './env'; // Import the new function
const API_BASE_URL = getApiBaseUrl();

/**
 * Fetches the list of available LLM models from the backend.
 * @returns A promise that resolves to an array of LLMModel objects.
 * @throws Will throw an error if the network request fails or the API returns an error.
 */
export const getAvailableLLMs = async (): Promise<LLMModel[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/llm/models`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Network response was not ok.' }));
      throw new Error(errorData.detail || `Failed to fetch LLM models: ${response.statusText}`);
    }
    const data: LLMModelsResponse = await response.json();
    if (!data.models) {
        console.warn('No models found in response:', data);
        return []; 
    }
    return data.models;
  } catch (error) {
    console.error("Error fetching available LLM models:", error);
    throw error;
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

        const response = await fetch(`${API_BASE_URL}/api/v1/llm/generate-text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Network response was not ok during text generation.' }));
            throw new Error(errorData.detail || `Failed to generate text: ${response.statusText}`);
        }
        const data: LLMTextGenerationResponse = await response.json();
        return data;
    } catch (error) {
        console.error("Error generating text with LLM:", error);
        throw error;
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


    const response = await fetch(`${API_BASE_URL}/api/v1/images/generate`, { // Updated endpoint path
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Network response was not ok during image generation.' }));
      throw new Error(errorData.detail || `Failed to generate image: ${response.statusText} (Status: ${response.status})`);
    }
    const data: ImageGenerationResponse = await response.json();
    return data;
  } catch (error) {
    console.error("Error generating image:", error);
    throw error;
  }
};
// --- End New Image Generation ---
