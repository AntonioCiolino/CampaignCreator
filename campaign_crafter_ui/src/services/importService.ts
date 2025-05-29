import apiClient from './apiClient'; // Assuming apiClient is already set up (e.g., Axios instance)

// --- TypeScript Interfaces (matching backend Pydantic models) ---

export interface ImportErrorDetail {
  file_name?: string | null;
  item_identifier?: string | null;
  error: string;
}

export interface ImportSummaryResponse {
  message: string;
  imported_campaigns_count: number;
  imported_sections_count: number;
  created_campaign_ids: number[];
  updated_campaign_ids: number[];
  errors: ImportErrorDetail[];
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'; // Consistent with other services

/**
 * Imports campaign data from a JSON file.
 * @param file The JSON File object to upload.
 * @param targetCampaignId Optional ID of an existing campaign to add sections to.
 * @returns A promise that resolves to an ImportSummaryResponse.
 */
export const importJsonFile = async (
  file: File,
  targetCampaignId?: string | number | null 
): Promise<ImportSummaryResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (targetCampaignId !== null && targetCampaignId !== undefined && targetCampaignId !== '') {
    formData.append('target_campaign_id', String(targetCampaignId));
  }

  try {
    // Adjust endpoint path if your apiClient is not pre-configured with /api/v1
    const response = await apiClient.post<ImportSummaryResponse>(`/import/json_file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error: any) {
    console.error('Error importing JSON file:', error);
    // Try to extract backend error message if available
    if (error.response && error.response.data && error.response.data.detail) {
      throw new Error(error.response.data.detail);
    }
    throw new Error(error.message || 'An unknown error occurred during JSON file import.');
  }
};

/**
 * Imports campaign data from a Zip archive.
 * @param file The Zip File object to upload.
 * @param targetCampaignId Optional ID of an existing campaign to add content to.
 * @param processFoldersAsStructure If true, interpret folder structures within the Zip.
 * @returns A promise that resolves to an ImportSummaryResponse.
 */
export const importZipFile = async (
  file: File,
  targetCampaignId?: string | number | null,
  processFoldersAsStructure?: boolean
): Promise<ImportSummaryResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (targetCampaignId !== null && targetCampaignId !== undefined && targetCampaignId !== '') {
    formData.append('target_campaign_id', String(targetCampaignId));
  }
  if (processFoldersAsStructure !== undefined) {
    formData.append('process_folders_as_structure', String(processFoldersAsStructure));
  }

  try {
    const response = await apiClient.post<ImportSummaryResponse>(`/import/zip_file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error: any) {
    console.error('Error importing Zip file:', error);
    if (error.response && error.response.data && error.response.data.detail) {
      throw new Error(error.response.data.detail);
    }
    throw new Error(error.message || 'An unknown error occurred during Zip file import.');
  }
};
