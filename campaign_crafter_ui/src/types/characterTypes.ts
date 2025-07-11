// Contains all TypeScript interfaces related to Character data models.

// Interface for character statistics, matching D&D style attributes.
export interface CharacterStats {
    strength?: number;
    dexterity?: number;
    constitution?: number;
    intelligence?: number;
    wisdom?: number;
    charisma?: number;
}

// Base interface for character data, used for creation and as part of the full Character model.
export interface CharacterBase {
    name: string;
    description?: string | null;
    appearance_description?: string | null;
    image_urls?: string[] | null;       // URLs for character images
    video_clip_urls?: string[] | null;  // URLs for future video integration
    notes_for_llm?: string | null;      // Notes for front-loading LLM interactions
    stats?: CharacterStats | null;      // Embeds CharacterStats
    export_format_preference?: string | null; // Added new field
}

// Interface for creating a new character. Inherits all fields from CharacterBase.
export interface CharacterCreate extends CharacterBase {
    export_format_preference?: string | null; // Explicitly add here for clarity, though CharacterBase has it
}

// Interface for updating an existing character. All fields are optional.
export interface CharacterUpdate {
    name?: string;
    description?: string | null;
    appearance_description?: string | null;
    image_urls?: string[] | null;
    video_clip_urls?: string[] | null;
    notes_for_llm?: string | null;
    stats?: CharacterStats | null;
    export_format_preference?: string | null; // Added new field
}

// Full character interface, representing a character retrieved from the backend.
export interface Character extends CharacterBase {
    id: number;
    owner_id: number;
    export_format_preference?: string | null; // Ensure it's part of the full Character type
    // campaigns: Campaign[]; // Placeholder for potential future inclusion of campaign details
                           // Requires Campaign type to be defined and imported if used.
}

// Example of how Campaign might look if needed for the above (define elsewhere if used broadly)
// export interface Campaign {
//   id: number;
//   title: string;
//   // ... other campaign properties
// }

// Type for the payload when requesting character image generation
// Corresponds to ImageModelName: "dall-e" | "stable-diffusion" | "gemini" from llmService.ts (consider moving ImageModelName to a shared types file)
export interface CharacterImageGenerationRequest {
    additional_prompt_details?: string | null;
    model_name?: string | null;
    size?: string | null;
    quality?: string | null;        // For DALL-E
    steps?: number | null;          // For Stable Diffusion
    cfg_scale?: number | null;      // For Stable Diffusion
    gemini_model_name?: string | null; // Specific model for Gemini image gen
}

// For Character Aspect Generation (e.g., description, appearance)
export interface CharacterAspectGenerationRequestPayload {
    character_name?: string | null;
    aspect_to_generate: "description" | "appearance_description" | "backstory_snippet"; // Use a literal type for known aspects
    existing_description?: string | null;
    existing_appearance_description?: string | null;
    notes_for_llm?: string | null; // Added field for LLM notes
    prompt_override?: string | null;
    model_id_with_prefix?: string | null;
}

export interface CharacterAspectGenerationResponseData {
    generated_text: string;
}

// --- Chat Message Types (New Architecture) ---

// This interface defines the structure of individual messages
// as stored in the backend's JSON conversation history
// and as returned by the GET /chat endpoint.
export interface ChatMessage {
    speaker: string; // "user" or "assistant" (or character name)
    text: string;
    timestamp: string; // ISO date string

    // The following fields are for UI enrichment on the client-side (in CharacterDetailPage.tsx)
    // and are not part of the direct backend response structure for each message object.
    uiKey?: string; // Client-side unique key for React list rendering
    senderType?: 'user' | 'llm'; // Derived from 'speaker' for UI styling/logic
    user_avatar_url?: string;
    character_avatar_url?: string;
}

// Old ChatMessageBase, ChatMessageCreate, and the old ChatMessage (with id, character_id)
// are now obsolete with the new JSON storage architecture.

// LLMChatGenerationRequest is also obsolete here, as CharacterDetailPage.tsx
// now directly constructs an LLMTextGenerationParams object imported from llmService.ts.
