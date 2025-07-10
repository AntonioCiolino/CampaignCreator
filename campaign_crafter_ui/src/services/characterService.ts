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

// --- Chat Message Service Functions ---

// Assuming ChatMessage and ChatMessageCreate types will be defined in characterTypes.ts
// If not, they need to be imported from their actual location or defined here.
import { ChatMessage, ChatMessageCreate } from '../types/characterTypes'; // Ensure these are added to types

/**
 * Saves a chat message for a character.
 * @param characterId The ID of the character.
 * @param message The chat message payload.
 * @returns The saved chat message.
 */
export const saveChatMessage = async (characterId: number, message: ChatMessageCreate): Promise<ChatMessage> => {
  const response = await apiClient.post<ChatMessage>(`${CHARACTER_API_URL}/${characterId}/chat`, message);
  return response.data;
};

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
