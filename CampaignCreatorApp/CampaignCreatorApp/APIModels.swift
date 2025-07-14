import Foundation

// MARK: - User Models

struct User: Codable {
    let id: Int
    let username: String
    let email: String?
    let fullName: String?
    let disabled: Bool
    let isSuperuser: Bool
    let openaiApiKeyProvided: Bool?
    let sdApiKeyProvided: Bool?
    let sdEnginePreference: String?
    let geminiApiKeyProvided: Bool?
    let otherLlmApiKeyProvided: Bool?
    let avatarUrl: String?
    var campaigns: [Campaign]?
    var llmConfigs: [LLMConfig]?
}

struct UserCreate: Codable {
    let username: String
    let email: String?
    let fullName: String?
    let password_hash: String
}

struct UserUpdate: Codable {
    let username: String?
    let email: String?
    let fullName: String?
    let password_hash: String?
    let disabled: Bool?
}

struct UserAPIKeyUpdate: Codable {
    let openai_api_key: String?
    let sd_api_key: String?
    let gemini_api_key: String?
    let other_llm_api_key: String?
}


// MARK: - Campaign Models

struct CampaignCreate: Codable {
    let title: String
    let initial_user_prompt: String?
    let model_id_with_prefix_for_concept: String?
    let skip_concept_generation: Bool?
}

struct CampaignUpdate: Codable {
    var title: String?
    var initial_user_prompt: String?
    var concept: String?
    var homebrewery_toc: [String: String]?
    var display_toc: [String: String]?
    var homebrewery_export: String?
    var badge_image_url: String?
    var thematic_image_url: String?
    var thematic_image_prompt: String?
    var selected_llm_id: String?
    var temperature: Float?

    // Theme Properties
    var theme_primary_color: String?
    var theme_secondary_color: String?
    var theme_background_color: String?
    var theme_text_color: String?
    var theme_font_family: String?
    var theme_background_image_url: String?
    var theme_background_image_opacity: Float?

    // Mood Board
    var mood_board_image_urls: [String]?
}

struct CampaignSectionCreate: Codable {
    var title: String?
    var content: String
    var order: Int
    var type: String?
}

struct CampaignSectionUpdate: Codable {
    var title: String?
    var content: String?
    var order: Int?
    var type: String?
}

struct CampaignTitlesResponse: Codable {
    let titles: [String]
}

struct CampaignFullContentResponse: Codable {
    let campaign_id: Int
    let title: String?
    let full_content: String
}

struct CampaignSectionListResponse: Codable {
    let sections: [CampaignSection]
}


// MARK: - LLM and Model Models

struct LLMConfig: Codable, Identifiable {
    let id: Int
    let owner_id: Int
    var name: String
    var api_key: String?
    var api_url: String?
}

struct LLMConfigCreate: Codable {
    var name: String
    var api_key: String?
    var api_url: String?
}

struct ModelInfo: Codable {
    let id: String
    let name: String
    let model_type: String
    let supports_temperature: Bool
    let capabilities: [String]
}

struct ModelListResponse: Codable {
    let models: [ModelInfo]
}

struct LLMGenerationRequest: Codable {
    let prompt: String
    let model_id_with_prefix: String?
    let temperature: Float?
    let max_tokens: Int?
    let chat_history: [ConversationMessageContext]?
    let campaign_id: Int?
    let section_title_suggestion: String?
    let section_type: String?
    let section_creation_prompt: String?
}

struct ConversationMessageContext: Codable {
    let speaker: String
    let text: String
}

struct ConversationMessageEntry: Codable {
    let speaker: String
    let text: String
    let timestamp: Date
}

struct LLMTextGenerationResponse: Codable {
    let text: String
}

// MARK: - Feature Models

struct Feature: Codable, Identifiable {
    let id: Int
    var name: String
    var template: String
    var user_id: Int?
    var required_context: [String]?
    var compatible_types: [String]?
    var feature_category: String?
}

struct FeatureCreate: Codable {
    var name: String
    var template: String
    var user_id: Int?
    var required_context: [String]?
    var compatible_types: [String]?
    var feature_category: String?
}

struct FeatureUpdate: Codable {
    var name: String?
    var template: String?
    var required_context: [String]?
    var compatible_types: [String]?
    var feature_category: String?
}

struct FeaturePromptItem: Codable {
    let name: String
    let template: String
}

struct FeaturePromptListResponse: Codable {
    let features: [FeaturePromptItem]
}

// MARK: - RollTable Models

struct RollTable: Codable, Identifiable {
    let id: Int
    var name: String
    var description: String?
    var user_id: Int?
    var items: [RollTableItem]
}

struct RollTableCreate: Codable {
    var name: String
    var description: String?
    var user_id: Int?
    var items: [RollTableItemCreate]
}

struct RollTableUpdate: Codable {
    var name: String?
    var description: String?
    var items: [RollTableItemCreate]?
}

struct RollTableItem: Codable, Identifiable {
    let id: Int
    let roll_table_id: Int
    var min_roll: Int
    var max_roll: Int
    var description: String
}

struct RollTableItemCreate: Codable {
    var min_roll: Int
    var max_roll: Int
    var description: String
}

struct RollTableItemUpdate: Codable {
    var min_roll: Int?
    var max_roll: Int?
    var description: String?
}

struct RandomItemResponse: Codable {
    let table_name: String
    let item: String?
}

struct TableNameListResponse: Codable {
    let table_names: [String]
}

// MARK: - Character Models

struct CharacterCreate: Codable {
    var name: String
    var description: String?
    var appearance_description: String?
    var image_urls: [String]?
    var video_clip_urls: [String]?
    var notes_for_llm: String?
    var stats: CharacterStats?
    var export_format_preference: String?

    func toCharacterCreateDTO() -> CampaignCreatorLib.CharacterCreateDTO {
        return CampaignCreatorLib.CharacterCreateDTO(
            name: self.name,
            description: self.description,
            appearanceDescription: self.appearance_description,
            imageURLs: self.image_urls,
            notesForLLM: self.notes_for_llm,
            stats: self.stats?.toCharacterStatsDTO(),
            exportFormatPreference: self.export_format_preference
        )
    }
}

struct CharacterUpdate: Codable {
    var name: String?
    var description: String?
    var appearance_description: String?
    var image_urls: [String]?
    var video_clip_urls: [String]?
    var notes_for_llm: String?
    var stats: CharacterStats?
    var export_format_preference: String?
}

struct CharacterCampaignLink: Codable {
    let character_id: Int
    let campaign_id: Int
}

struct CharacterImageGenerationRequest: Codable {
    let additional_prompt_details: String?
    let model_name: String?
    let size: String?
    let quality: String?
    let steps: Int?
    let cfg_scale: Float?
    let gemini_model_name: String?
}

struct CharacterAspectGenerationRequest: Codable {
    let character_name: String?
    let aspect_to_generate: String
    let existing_description: String?
    let existing_appearance_description: String?
    let notes_for_llm: String?
    let prompt_override: String?
    let model_id_with_prefix: String?
}

struct CharacterAspectGenerationResponse: Codable {
    let generated_text: String
}

// MARK: - Other Models

struct Token: Codable {
    let access_token: String
    let token_type: String
}

struct TokenData: Codable {
    let username: String?
}

struct BlobFileMetadata: Codable {
    let name: String
    let blob_name: String
    let url: String
    let size: Int
    let last_modified: Date
    let content_type: String?
}

struct SectionRegenerateInput: Codable {
    let new_prompt: String?
    let new_title: String?
    let section_type: String?
    let model_id_with_prefix: String?
    let feature_id: Int?
    let context_data: [String: String]? // Simplified for Swift
}

struct MemorySummary: Codable {
    let memory_summary: String
}
