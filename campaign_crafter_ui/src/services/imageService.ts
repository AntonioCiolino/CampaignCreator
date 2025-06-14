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
