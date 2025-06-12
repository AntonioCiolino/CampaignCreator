// campaign_crafter_ui/src/services/imageService.ts
import apiClient from './apiClient'; // Assuming a common API client setup

export interface UploadedImageResponse {
  imageUrl: string;
  // Potentially other metadata like filename, size, etc.
}

/**
 * Uploads an image file to the backend.
 * NOTE: The backend API endpoint for this does not exist yet.
 * This is a placeholder for the frontend integration.
 *
 * @param file The image file to upload.
 * @returns A promise that resolves to the UploadedImageResponse containing the URL of the uploaded image.
 */
export const uploadImage = async (file: File): Promise<UploadedImageResponse> => {
  const formData = new FormData();
  formData.append('imageFile', file); // 'imageFile' is an example key, backend will define it

  console.log(`[imageService.uploadImage] Simulating upload for: ${file.name}`);
  // TODO: Replace with actual API call when the endpoint is available.
  // Example using apiClient if it supports file uploads:
  // return apiClient.post<UploadedImageResponse>('/images/upload', formData, {
  //   headers: {
  //     'Content-Type': 'multipart/form-data',
  //   },
  // });

  // Placeholder response:
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // Simulate success with a placeholder URL
      // In a real scenario, this URL would come from the backend response.
      const placeholderUrl = `https://example.com/uploads/placeholder_${file.name}`;
      console.log(`[imageService.uploadImage] Simulated success for ${file.name}, URL: ${placeholderUrl}`);
      resolve({ imageUrl: placeholderUrl });

      // To simulate an error:
      // reject(new Error(`Simulated upload failed for ${file.name}`));
    }, 1000); // Simulate network delay
  });
};
