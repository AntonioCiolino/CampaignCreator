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
}

// Interface for creating a new character. Inherits all fields from CharacterBase.
export interface CharacterCreate extends CharacterBase {}

// Interface for updating an existing character. All fields are optional.
export interface CharacterUpdate {
    name?: string;
    description?: string | null;
    appearance_description?: string | null;
    image_urls?: string[] | null;
    video_clip_urls?: string[] | null;
    notes_for_llm?: string | null;
    stats?: CharacterStats | null;
}

// Full character interface, representing a character retrieved from the backend.
export interface Character extends CharacterBase {
    id: number;
    owner_id: number;
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
