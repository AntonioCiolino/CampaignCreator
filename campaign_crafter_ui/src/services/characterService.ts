import apiClient from './apiClient';
import {
    Character,
    CharacterCreate,
    CharacterUpdate,
    // CharacterStats is used internally by other types but not directly as a param/return type of service functions here
    // CharacterBase is also implicitly handled by Character, CharacterCreate
} from '../types/characterTypes';

// --- API Service Functions ---

const CHARACTER_API_URL = '/api/v1/characters';

/**
 * Creates a new character.
 */
export const createCharacter = async (characterData: CharacterCreate): Promise<Character> => {
    const response = await apiClient.post<Character>(CHARACTER_API_URL + '/', characterData);
    return response.data;
};

/**
 * Fetches all characters for the current user.
 */
export const getUserCharacters = async (): Promise<Character[]> => {
    const response = await apiClient.get<Character[]>(CHARACTER_API_URL + '/');
    return response.data;
};

/**
 * Fetches a single character by its ID.
 */
export const getCharacterById = async (characterId: number): Promise<Character> => {
    const response = await apiClient.get<Character>(`${CHARACTER_API_URL}/${characterId}`);
    return response.data;
};

/**
 * Updates an existing character.
 */
export const updateCharacter = async (characterId: number, characterData: CharacterUpdate): Promise<Character> => {
    const response = await apiClient.put<Character>(`${CHARACTER_API_URL}/${characterId}`, characterData);
    return response.data;
};

/**
 * Deletes a character by its ID.
 */
export const deleteCharacter = async (characterId: number): Promise<void> => {
    await apiClient.delete(`${CHARACTER_API_URL}/${characterId}`);
};

/**
 * Links a character to a campaign.
 */
export const linkCharacterToCampaign = async (characterId: number, campaignId: number): Promise<Character> => {
    const response = await apiClient.post<Character>(`${CHARACTER_API_URL}/${characterId}/campaigns/${campaignId}`);
    return response.data;
};

/**
 * Unlinks a character from a campaign.
 */
export const unlinkCharacterFromCampaign = async (characterId: number, campaignId: number): Promise<Character> => {
    const response = await apiClient.delete<Character>(`${CHARACTER_API_URL}/${characterId}/campaigns/${campaignId}`);
    return response.data;
};

/**
 * Fetches all characters associated with a specific campaign.
 * Note: The endpoint in the backend plan was GET /characters/campaign/{campaign_id}/characters
 * Adjusting here to match that.
 */
export const getCampaignCharacters = async (campaignId: number): Promise<Character[]> => {
    const response = await apiClient.get<Character[]>(`${CHARACTER_API_URL}/campaign/${campaignId}/characters`);
    return response.data;
};
