// Contains TypeScript interfaces related to Campaign data models.

export interface TOCEntry {
  title: string;
  type: string;
}

export interface CampaignSection {
  id: number;
  title: string | null;
  content: string;
  order: number;
  campaign_id: number;
  type?: string;
}

export interface ModelInfo { // This might also belong in a more general 'llmTypes.ts' or similar
  id: string;
  name: string;
  capabilities: string[];
}

export interface Campaign {
  id: number;
  title: string;
  initial_user_prompt: string | null;
  concept: string | null;
  homebrewery_toc: TOCEntry[] | null;
  display_toc: TOCEntry[] | null;
  badge_image_url?: string | null;
  thematic_image_url?: string | null;
  thematic_image_prompt?: string | null;
  selected_llm_id?: string | null;
  temperature?: number | null;
  theme_primary_color?: string | null;
  theme_secondary_color?: string | null;
  theme_background_color?: string | null;
  theme_text_color?: string | null;
  theme_font_family?: string | null;
  theme_background_image_url?: string | null;
  theme_background_image_opacity?: number | null;
  mood_board_image_urls?: string[] | null;
  // If characters are directly nested in campaign responses (check backend Campaign Pydantic model):
  // characters?: BasicCharacterInfo[]; // Define BasicCharacterInfo if needed
}

export interface CampaignCreatePayload {
  title: string;
  initial_user_prompt?: string;
  skip_concept_generation?: boolean;
  model_id_with_prefix_for_concept?: string | null;
  badge_image_url?: string | null;
  selected_llm_id?: string | null;
  temperature?: number | null;
  thematic_image_url?: string | null;
  thematic_image_prompt?: string | null;
  theme_primary_color?: string | null;
  theme_secondary_color?: string | null;
  theme_background_color?: string | null;
  theme_text_color?: string | null;
  theme_font_family?: string | null;
  theme_background_image_url?: string | null;
  theme_background_image_opacity?: number | null;
  mood_board_image_urls?: string[] | null;
}

export interface CampaignUpdatePayload {
  title?: string;
  initial_user_prompt?: string;
  badge_image_url?: string | null;
  thematic_image_url?: string | null;
  thematic_image_prompt?: string | null;
  selected_llm_id?: string | null;
  temperature?: number | null;
  display_toc?: TOCEntry[] | null;
  homebrewery_toc?: TOCEntry[] | null;
  concept?: string | null;
  theme_primary_color?: string | null;
  theme_secondary_color?: string | null;
  theme_background_color?: string | null;
  theme_text_color?: string | null;
  theme_font_family?: string | null;
  theme_background_image_url?: string | null;
  theme_background_image_opacity?: number | null;
  mood_board_image_urls?: string[] | null;
}

export interface LLMGenerationPayload { // Might belong in a general llmTypes.ts
    prompt: string;
    model_id_with_prefix?: string | null;
}

export interface CampaignTitlesResponse { // Specific to campaignService responses
  titles: string[];
}

export interface CampaignSectionUpdatePayload {
  title?: string;
  content?: string;
  order?: number;
  type?: string;
}

export interface CampaignSectionCreatePayload {
  title?: string | null;
  prompt?: string | null; // This will map to the backend's section_creation_prompt for the LLM
  model_id_with_prefix?: string | null;
  type?: string | null; // Added to align with backend CampaignSectionCreateInput
}

export interface PrepareHomebreweryPostResponse {
    markdown_content: string;
    homebrewery_new_url: string;
    filename_suggestion: string;
    notes?: string;
}

// SSE Event types (could also be in a more general sseTypes.ts or feature-specific)
export interface SeedSectionsProgressEvent {
  event_type: "section_update";
  progress_percent: number;
  current_section_title: string;
  section_data: CampaignSection;
}

export interface SeedSectionsCompleteEvent {
  event_type: "complete";
  message: string;
  total_sections_processed: number;
}

export type SeedSectionsEvent = SeedSectionsProgressEvent | SeedSectionsCompleteEvent;

export interface SeedSectionsCallbacks {
  onOpen?: (event: Event) => void;
  onProgress?: (data: SeedSectionsProgressEvent) => void;
  onSectionComplete?: (data: CampaignSection) => void;
  onDone?: (message: string, totalProcessed: number) => void;
  onError?: (error: Event | { message: string }) => void;
}

export interface SectionRegeneratePayload {
  new_prompt?: string; // This will be the selected text or full content from editor
  new_title?: string; // Current section title
  section_type?: string; // Current section type
  model_id_with_prefix?: string; // LLM model to use
  feature_id?: number; // ID of the selected feature to guide generation
  context_data?: { [key: string]: any }; // Additional context data required by the feature
}
