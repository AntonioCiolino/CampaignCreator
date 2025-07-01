import apiClient from './apiClient';
import { PydanticCharacter, CharacterCreatePayload, CharacterUpdatePayload } from '../types/characterTypes'; // Assuming types will be defined here

const CHARACTER_API_BASE_PATH = '/api/v1'; // Adjusted base path if necessary

// Helper function to construct URLs
const urls = {
  charactersForCampaign: (campaignId: number | string) =>
    `${CHARACTER_API_BASE_PATH}/campaigns/${campaignId}/characters`,
  characterById: (characterId: number | string) =>
    `${CHARACTER_API_BASE_PATH}/characters/${characterId}`,
};

/**
 * Creates a new character for a specific campaign.
 * @param campaignId - The ID of the campaign.
 * @param characterData - The data for the new character.
 * @returns A promise that resolves to the created character.
 */
export const createCharacter = async (
  campaignId: number | string,
  characterData: CharacterCreatePayload
): Promise<PydanticCharacter> => {
  try {
    const response = await apiClient.post<PydanticCharacter>(
      urls.charactersForCampaign(campaignId),
      characterData
    );
    return response.data;
  } catch (error) {
    console.error(`Error creating character for campaign ${campaignId}:`, error);
    throw error; // Re-throw to allow caller to handle
  }
};

/**
 * Fetches all characters for a specific campaign.
 * @param campaignId - The ID of the campaign.
 * @returns A promise that resolves to a list of characters.
 */
export const getCharactersByCampaign = async (
  campaignId: number | string
): Promise<PydanticCharacter[]> => {
  try {
    const response = await apiClient.get<PydanticCharacter[]>(
      urls.charactersForCampaign(campaignId)
    );
    return response.data;
  } catch (error) {
    console.error(`Error fetching characters for campaign ${campaignId}:`, error);
    throw error;
  }
};

/**
 * Fetches a single character by its ID.
 * @param characterId - The ID of the character.
 * @returns A promise that resolves to the character data.
 */
export const getCharacterById = async (
  characterId: number | string
): Promise<PydanticCharacter> => {
  try {
    const response = await apiClient.get<PydanticCharacter>(
      urls.characterById(characterId)
    );
    return response.data;
  } catch (error)
 {
    console.error(`Error fetching character ${characterId}:`, error);
    throw error;
  }
};

/**
 * Updates an existing character.
 * @param characterId - The ID of the character to update.
 * @param characterData - The data to update the character with.
 * @returns A promise that resolves to the updated character.
 */
export const updateCharacter = async (
  characterId: number | string,
  characterData: CharacterUpdatePayload
): Promise<PydanticCharacter> => {
  try {
    const response = await apiClient.put<PydanticCharacter>(
      urls.characterById(characterId),
      characterData
    );
    return response.data;
  } catch (error) {
    console.error(`Error updating character ${characterId}:`, error);
    throw error;
  }
};

/**
 * Deletes a character by its ID.
 * @param characterId - The ID of the character to delete.
 * @returns A promise that resolves when the character is deleted.
 */
export const deleteCharacter = async (
  characterId: number | string
): Promise<void> => {
  try {
    await apiClient.delete(urls.characterById(characterId));
  } catch (error) {
    console.error(`Error deleting character ${characterId}:`, error);
    throw error;
  }
};

// Example of a more specific function if needed, e.g., for exporting
/**
 * Exports character data (placeholder - implement actual export logic if API supports it).
 * @param characterId - The ID of the character to export.
 * @returns A promise that resolves to the exported data (e.g., a JSON string or Blob).
 */
export const exportCharacterData = async (
  characterId: number | string
): Promise<any> => {
  try {
    // This is a placeholder. The actual implementation will depend on how
    // the backend API supports character export (e.g., a specific endpoint).
    // const response = await apiClient.get(`/api/v1/characters/${characterId}/export`);
    // return response.data;
    console.warn(`Export function for character ${characterId} is a placeholder.`);
    const character = await getCharacterById(characterId);
    return JSON.stringify(character, null, 2); // Example: return character data as JSON string
  } catch (error) {
    console.error(`Error exporting data for character ${characterId}:`, error);
    throw error;
  }
};
