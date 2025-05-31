// Defines the structure of an LLM model object
export interface LLMModel {
  id: string; // Prefixed ID, e.g., "openai/gpt-3.5-turbo"
  name: string; // User-friendly name, e.g., "OpenAI GPT-3.5 Turbo"
}

// Defines the structure of the response from the /api/llm/models endpoint
interface LLMModelsResponse {
  models: LLMModel[];
}

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

/**
 * Fetches the list of available LLM models from the backend.
 * @returns A promise that resolves to an array of LLMModel objects.
 * @throws Will throw an error if the network request fails or the API returns an error.
 */
export const getAvailableLLMs = async (): Promise<LLMModel[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/llm/models`);

    if (!response.ok) {
      // Attempt to get more specific error information
      const contentType = response.headers.get("content-type");
      let errorDetail = `Failed to fetch LLM models: ${response.status} ${response.statusText}`;
      if (contentType && contentType.includes("application/json")) {
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorDetail;
        } catch (jsonError) {
          // If parsing JSON fails, stick with the status text or provide raw text
          console.error("Failed to parse error response as JSON:", jsonError);
          // Optionally, try to read as text if JSON parsing fails
          // errorDetail = await response.text();
        }
      } else if (contentType && contentType.includes("text/html")) {
        // If we received HTML, it's likely a misconfiguration or server error page
        errorDetail = `Received HTML response from server (status ${response.status}). Check API proxy configuration or server logs.`;
        // To get a snippet of the HTML for debugging, you could do:
        // const htmlSnippet = (await response.text()).substring(0, 200);
        // errorDetail += ` HTML Snippet: ${htmlSnippet}`;
      }
      throw new Error(errorDetail);
    }

    // If response.ok is true, we still need to verify Content-Type
    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      // If response.ok is true but content is not JSON, this is unexpected.
      let responseText = await response.text(); // Get the actual response text
      throw new Error(
        `Expected JSON response but received ${contentType || 'unknown content type'}. ` +
        `Status: ${response.status}. Response: ${responseText.substring(0, 200)}...` // Show a snippet
      );
    }

    const data: LLMModelsResponse = await response.json();
    if (!data.models) {
        console.warn('No models found in response (but was valid JSON):', data);
        return []; 
    }
    return data.models;

  } catch (error) {
    // Log the full error object if it's not just a string message
    if (error instanceof Error) {
        console.error("Error fetching available LLM models:", error.message, error.stack);
    } else {
        console.error("Error fetching available LLM models (unknown type):", error);
    }
    // Re-throw the original error or a new one if you transformed it
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

        const response = await fetch(`${API_BASE_URL}/llm/generate-text`, {
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


    const response = await fetch(`${API_BASE_URL}/images/generate`, { // Updated endpoint path
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
