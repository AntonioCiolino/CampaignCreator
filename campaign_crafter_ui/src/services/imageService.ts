// campaign_crafter_ui/src/services/imageService.ts
import apiClient from './apiClient';

export interface UploadedImageResponse {
  imageUrl: string;
  filename: string;
  content_type: string;
  size: number;
}

/**
 * Uploads an image file to the backend.
 *
 * @param file The image file to upload.
 * @returns A promise that resolves to the UploadedImageResponse containing the URL of the uploaded image.
 */
export const uploadImage = async (file: File): Promise<UploadedImageResponse> => {
  const formData = new FormData();
  formData.append('file', file); // FastAPI's File(...) by default expects the field name to be 'file'
                                 // if the parameter is named 'file', unless a specific alias is given.
                                 // In our file_uploads.py, it's `file: UploadFile = File(...)`
                                 // So, the key here should be 'file'.

  console.log(`[imageService.uploadImage] Attempting to upload: ${file.name}`);

  try {
    const response = await apiClient.post<UploadedImageResponse>('/api/v1/files/upload_image', formData, {
      headers: {
        'Content-Type': undefined, // Let axios set the correct Content-Type for FormData
      },
      // If apiClient requires explicit timeout for uploads, configure it here or in apiClient defaults
    });
    console.log(`[imageService.uploadImage] Successfully uploaded ${file.name}, response:`, response.data);
    return response.data; // apiClient typically wraps response in a data object
  } catch (error: any) {
    console.error(`[imageService.uploadImage] Failed to upload ${file.name}:`, error.response?.data || error.message || error);
    // Re-throw a more specific error or a generic one for the UI to handle
    const detail = error.response?.data?.detail;
    let errorMessage = `Failed to upload ${file.name}`;
    if (detail) {
      if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
        errorMessage = detail[0].msg;
      } else if (typeof detail === 'string') {
        errorMessage = detail;
      }
    }
    throw new Error(errorMessage);
  }
};

// --- AI Image Generation ---

export interface ImageGenerationResponse {
  image_url: string;
  prompt_used: string;
  model_used: string; // e.g., "dall-e", "stable-diffusion", "gemini"
  size_used: string;
  quality_used?: string;
  steps_used?: number;
  cfg_scale_used?: number;
  gemini_model_name_used?: string;
}

export interface ImageGenerationRequestPayload {
  prompt: string;
  model: 'dall-e' | 'stable-diffusion' | 'gemini';
  size?: string; // e.g., "1024x1024"
  quality?: 'standard' | 'hd'; // For DALL-E
  steps?: number; // For Stable Diffusion
  cfg_scale?: number; // For Stable Diffusion
  gemini_model_name?: string; // For Gemini
}

/**
 * Generates an image using an AI model via the backend.
 * @param payload The parameters for image generation (prompt, model, etc.).
 * @returns A promise that resolves to the ImageGenerationResponse.
 */
export const generateAiImage = async (
  payload: ImageGenerationRequestPayload
): Promise<ImageGenerationResponse> => {
  console.log('[imageService.generateAiImage] Attempting to generate image with payload:', payload);
  try {
    // The apiClient is expected to handle token injection and base URL.
    // The endpoint '/images/generate' is relative to the API base URL configured in apiClient.
    const response = await apiClient.post<ImageGenerationResponse>('/images/generate', payload);
    // Assuming apiClient returns the actual data in response.data, similar to Axios.
    // If apiClient returns the raw Fetch response, you'd need response.json() here.
    // Based on existing code, it seems apiClient.post already extracts .data or similar.
    console.log('[imageService.generateAiImage] Successfully generated image, response:', response); // Log the whole response object from apiClient

    // If apiClient.post returns { data: ActualData }, then use response.data
    // If apiClient.post returns ActualData directly, then use response
    // Adjust based on your apiClient's specific implementation.
    // For now, assuming 'response' is the actual data based on existing uploadImage.
    // However, the previous log for uploadImage says `response.data`, so let's stick to that pattern.
    // This implies apiClient.post<T> returns an object like { data: T }
    // This needs to be consistent. Let's assume apiClient returns the data directly for now,
    // as per the type hint T in `apiClient.post<T>`.
    // If it wraps it in `data`, the calling code in the component will need to access `response.data.image_url`.
    // To simplify, let's assume `apiClient.post` returns the payload directly.
    // The existing `uploadImage` uses `response.data`, so `apiClient.post` likely returns an Axios-like response.

    // Correcting based on the existing pattern in `uploadImage`:
    // It calls `apiClient.post<UploadedImageResponse>(...)` and then returns `response.data`.
    // So, `apiClient.post` itself returns an object that *has* a `data` property.
    // The generic type `T` in `apiClient.post<T>` should refer to the type of `response.data`.

    // Let's refine the apiClient call assumption. If apiClient.post<Type> returns an Axios-like response,
    // then the actual data is in response.data.
    // If apiClient.post<Type> returns Type directly, then it's just response.
    // Given the existing code: `const response = await apiClient.post<UploadedImageResponse>(...)`
    // and then `return response.data;`, it means `apiClient.post` returns something like `AxiosResponse<UploadedImageResponse>`.
    // So, the `response` variable here will be `AxiosResponse<ImageGenerationResponse>`.

    // The type of `response` from `apiClient.post<ImageGenerationResponse>` should be the actual data `ImageGenerationResponse`
    // if `apiClient` is designed to return the data directly.
    // If `apiClient` returns a wrapper (like Axios does, e.g. `{ data: ImageGenerationResponse, status: ..., ...}`),
    // then the type hint for `apiClient.post` should reflect that, or it should extract `.data` internally.

    // Let's assume `apiClient.post` is like this: `async post<R>(url, data): Promise<R>` where R is the response body.
    // This means `response` below *is* `ImageGenerationResponse`.

    const resultData = response; // Assuming apiClient.post returns the data directly.
                                 // If it returns { data: ... }, then this should be response.data.
                                 // The existing uploadImage returns response.data, so apiClient.post gives an object with a data field.
                                 // So, the 'response' variable above IS that object.

    // Sticking to the pattern in `uploadImage`:
    // The `response` variable from `apiClient.post<T>` is an object where `response.data` is `T`.
    // This is confusing. Let's simplify the expectation for `apiClient.post<T>` to return `T` directly.
    // If `apiClient.ts` `apiClient.post` returns `response.data` from its internal fetch, then `response` here is `ImageGenerationResponse`.
    // If `apiClient.ts` `apiClient.post` returns the raw `fetch` response, then `response.json()` is needed.
    // Given the structure of `apiClient.ts` (it calls `response.json()` internally), `apiClient.post<T>` should return `T`.

    // Final decision: apiClient.post<T> returns T directly. -> This assumption was wrong.
    // Correcting based on the error and existing code pattern (e.g. in uploadImage).
    // The apiClient.post<T> returns an object where `data` property holds T.
    // const resultData = response; // This line was unused and removed.
    console.log('[imageService.generateAiImage] Successfully generated image, response object:', response);
    return response.data; // Return the actual data part of the response.

  } catch (error: any) {
    // error.response.data should contain the backend's error detail.
    console.error('[imageService.generateAiImage] Failed to generate image:', error.response?.data || error.message || error);
    const detail = error.response?.data?.detail; // Assumes error has a response.data.detail structure
    let errorMessage = 'Failed to generate AI image.';
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
// --- End AI Image Generation ---

// Optional: Group exports if you prefer a single service object, though named exports are fine.
// export const imageService = {
//   uploadImage,
//   uploadMoodboardImageApi,
//   generateAiImage,
// };

export interface MoodboardUploadResponse {
  image_url: string;
  campaign: any; // Define a proper Campaign type if available and needed for frontend state
}

/**
 * Uploads an image file to a specific campaign's moodboard.
 *
 * @param campaignId The ID of the campaign.
 * @param file The image file to upload.
 * @returns A promise that resolves to the MoodboardUploadResponse.
 */
export const uploadMoodboardImageApi = async (
  campaignId: string,
  file: File
): Promise<MoodboardUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file, file.name);

  console.log(`[imageService.uploadMoodboardImageApi] Attempting to upload: ${file.name} to campaign ${campaignId}`);

  try {
    // The URL should match the new API endpoint
    const response = await apiClient.post<MoodboardUploadResponse>(
      `/api/v1/campaigns/${campaignId}/moodboard/upload`,
      formData,
      {
        headers: {
          // Axios typically sets Content-Type automatically for FormData.
          // 'Content-Type': 'multipart/form-data', // Explicitly setting might be needed if apiClient doesn't default correctly
          'Content-Type': undefined, // Or let axios handle it by setting it to undefined
        },
      }
    );
    console.log(`[imageService.uploadMoodboardImageApi] Successfully uploaded ${file.name} to campaign ${campaignId}, response:`, response.data);
    return response.data;
  } catch (error: any) {
    console.error(`[imageService.uploadMoodboardImageApi] Failed to upload ${file.name} to campaign ${campaignId}:`, error.response?.data || error.message || error);
    const detail = error.response?.data?.detail;
    let errorMessage = `Failed to upload ${file.name} to moodboard.`;
    if (detail) {
      if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
        errorMessage = detail[0].msg;
      } else if (typeof detail === 'string') {
        errorMessage = detail;
      }
    }
    throw new Error(errorMessage);
  }
};
