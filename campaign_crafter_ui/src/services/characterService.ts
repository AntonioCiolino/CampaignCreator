import apiClient from './apiClient';
import {
    Character,
    CharacterCreate,
    CharacterUpdate,
    CharacterImageGenerationRequest,
    CharacterAspectGenerationRequestPayload, // New import
    CharacterAspectGenerationResponseData, // New import
    // CharacterStats is used internally by other types but not directly as a param/return type of service functions here
    // CharacterBase is also implicitly handled by Character, CharacterCreate
} from '../types/characterTypes';
import { Campaign } from '../types/campaignTypes';
import { LLMTextGenerationParams, LLMTextGenerationResponse } from './llmService';
import { ChatMessage } from '../types/characterTypes';

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

/**
 * Fetches all campaigns associated with a specific character.
 */
export const getCharacterCampaigns = async (characterId: number): Promise<Campaign[]> => {
    const response = await apiClient.get<Campaign[]>(`${CHARACTER_API_URL}/${characterId}/campaigns`);
    return response.data;
};

/**
 * Generates a text response from a character using an LLM.
 */
export const generateCharacterResponse = async (
    characterId: number,
    requestBody: LLMTextGenerationParams // Use the imported type
): Promise<LLMTextGenerationResponse> => { // Use the imported type
    const response = await apiClient.post<LLMTextGenerationResponse>(
        `${CHARACTER_API_URL}/${characterId}/generate-response`,
        requestBody
    );
    return response.data;
};

/**
 * Clears the chat history for a character.
 */
export const clearChatHistory = async (characterId: number): Promise<void> => {
    await apiClient.delete(`${CHARACTER_API_URL}/${characterId}/chat`);
};

export const getMemorySummary = async (characterId: number): Promise<{ memory_summary: string }> => {
    const response = await apiClient.get<{ memory_summary: string }>(`${CHARACTER_API_URL}/${characterId}/memory-summary`);
    return response.data;
};

// --- Chat Message Service Functions ---

// The saveChatMessage function is now obsolete as the backend's
// generate-response endpoint handles persistence of both user and AI messages
// into the new JSON conversation history structure.
// import { ChatMessage, ChatMessageCreate } from '../types/characterTypes'; // ChatMessageCreate removed


/**
 * Fetches the chat history for a character.
 * @param characterId The ID of the character.
 * @param skip Optional number of messages to skip (for pagination).
 * @param limit Optional limit on the number of messages to retrieve.
 * @returns A list of chat messages.
 */
export const getChatHistory = async (characterId: number, skip?: number, limit?: number): Promise<ChatMessage[]> => {
  const params: Record<string, number> = {};
  if (skip !== undefined) params.skip = skip;
  if (limit !== undefined) params.limit = limit;

  const response = await apiClient.get<ChatMessage[]>(`${CHARACTER_API_URL}/${characterId}/chat`, { params });
  return response.data;
};

/**
 * Generates text for a specific aspect of a character (e.g., description, appearance).
 */
export const generateCharacterAspect = async (
    payload: CharacterAspectGenerationRequestPayload
): Promise<CharacterAspectGenerationResponseData> => {
    const response = await apiClient.post<CharacterAspectGenerationResponseData>(
        `${CHARACTER_API_URL}/generate-aspect`,
        payload
    );
    return response.data;
};

/**
 * Generates an image for a character and returns the updated character data.
 */
export const generateCharacterImage = async (
    characterId: number,
    payload: CharacterImageGenerationRequest
): Promise<Character> => {
    const response = await apiClient.post<Character>(
        `${CHARACTER_API_URL}/${characterId}/generate-image`,
        payload
    );
    return response.data;
};
