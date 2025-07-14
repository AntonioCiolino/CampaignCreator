import Foundation
import CampaignCreatorLib

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
    var llmConfigs: [LLMConfig]?

    enum CodingKeys: String, CodingKey {
        case id, username, email, disabled
        case fullName = "full_name"
        case isSuperuser = "is_superuser"
        case openaiApiKeyProvided = "openai_api_key_provided"
        case sdApiKeyProvided = "sd_api_key_provided"
        case sdEnginePreference = "sd_engine_preference"
        case geminiApiKeyProvided = "gemini_api_key_provided"
        case otherLlmApiKeyProvided = "other_llm_api_key_provided"
        case avatarUrl = "avatar_url"
        case llmConfigs = "llm_configs"
    }
}

struct UserCreate: Codable {
    let username: String
    let email: String?
    let fullName: String?
    let passwordHash: String

    enum CodingKeys: String, CodingKey {
        case username, email
        case fullName = "full_name"
        case passwordHash = "password_hash"
    }
}

struct UserUpdate: Codable {
    let username: String?
    let email: String?
    let fullName: String?
    let passwordHash: String?
    let disabled: Bool?

    enum CodingKeys: String, CodingKey {
        case username, email, disabled
        case fullName = "full_name"
        case passwordHash = "password_hash"
    }
}

struct UserAPIKeyUpdate: Codable {
    let openaiApiKey: String?
    let sdApiKey: String?
    let geminiApiKey: String?
    let otherLlmApiKey: String?

    enum CodingKeys: String, CodingKey {
        case openaiApiKey = "openai_api_key"
        case sdApiKey = "sd_api_key"
        case geminiApiKey = "gemini_api_key"
        case otherLlmApiKey = "other_llm_api_key"
    }
}


// MARK: - Campaign Models

struct CampaignCreate: Codable {
    let title: String
    let initialUserPrompt: String?
    let modelIdWithPrefixForConcept: String?
    let skipConceptGeneration: Bool?

    enum CodingKeys: String, CodingKey {
        case title
        case initialUserPrompt = "initial_user_prompt"
        case modelIdWithPrefixForConcept = "model_id_with_prefix_for_concept"
        case skipConceptGeneration = "skip_concept_generation"
    }
}

struct CampaignUpdate: Codable {
    var title: String?
    var initialUserPrompt: String?
    var concept: String?
    var homebreweryToc: [String: String]?
    var displayToc: [String: String]?
    var homebreweryExport: String?
    var badgeImageUrl: String?
    var thematicImageUrl: String?
    var thematicImagePrompt: String?
    var selectedLlmId: String?
    var temperature: Float?

    // Theme Properties
    var themePrimaryColor: String?
    var themeSecondaryColor: String?
    var themeBackgroundColor: String?
    var themeTextColor: String?
    var themeFontFamily: String?
    var themeBackgroundImageUrl: String?
    var themeBackgroundImageOpacity: Float?

    // Mood Board
    var moodBoardImageUrls: [String]?

    enum CodingKeys: String, CodingKey {
        case title, concept, temperature
        case initialUserPrompt = "initial_user_prompt"
        case homebreweryToc = "homebrewery_toc"
        case displayToc = "display_toc"
        case homebreweryExport = "homebrewery_export"
        case badgeImageUrl = "badge_image_url"
        case thematicImageUrl = "thematic_image_url"
        case thematicImagePrompt = "thematic_image_prompt"
        case selectedLlmId = "selected_llm_id"
        case themePrimaryColor = "theme_primary_color"
        case themeSecondaryColor = "theme_secondary_color"
        case themeBackgroundColor = "theme_background_color"
        case themeTextColor = "theme_text_color"
        case themeFontFamily = "theme_font_family"
        case themeBackgroundImageUrl = "theme_background_image_url"
        case themeBackgroundImageOpacity = "theme_background_image_opacity"
        case moodBoardImageUrls = "mood_board_image_urls"
    }
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
    let campaignId: Int
    let title: String?
    let fullContent: String

    enum CodingKeys: String, CodingKey {
        case title
        case campaignId = "campaign_id"
        case fullContent = "full_content"
    }
}

struct CampaignSectionListResponse: Codable {
    let sections: [CampaignSection]
}


// MARK: - LLM and Model Models

struct LLMConfig: Codable, Identifiable {
    let id: Int
    let ownerId: Int
    var name: String
    var apiKey: String?
    var apiUrl: String?

    enum CodingKeys: String, CodingKey {
        case id, name
        case ownerId = "owner_id"
        case apiKey = "api_key"
        case apiUrl = "api_url"
    }
}

struct LLMConfigCreate: Codable {
    var name: String
    var apiKey: String?
    var apiUrl: String?

    enum CodingKeys: String, CodingKey {
        case name
        case apiKey = "api_key"
        case apiUrl = "api_url"
    }
}

struct ModelInfo: Codable {
    let id: String
    let name: String
    let modelType: String
    let supportsTemperature: Bool
    let capabilities: [String]

    enum CodingKeys: String, CodingKey {
        case id, name, capabilities
        case modelType = "model_type"
        case supportsTemperature = "supports_temperature"
    }
}

struct ModelListResponse: Codable {
    let models: [ModelInfo]
}

struct LLMGenerationRequest: Codable {
    let prompt: String
    let modelIdWithPrefix: String?
    let temperature: Float?
    let maxTokens: Int?
    let chatHistory: [ConversationMessageContext]?
    let campaignId: Int?
    let sectionTitleSuggestion: String?
    let sectionType: String?
    let sectionCreationPrompt: String?

    enum CodingKeys: String, CodingKey {
        case prompt, temperature
        case modelIdWithPrefix = "model_id_with_prefix"
        case maxTokens = "max_tokens"
        case chatHistory = "chat_history"
        case campaignId = "campaign_id"
        case sectionTitleSuggestion = "section_title_suggestion"
        case sectionType = "section_type"
        case sectionCreationPrompt = "section_creation_prompt"
    }
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
    var userId: Int?
    var requiredContext: [String]?
    var compatibleTypes: [String]?
    var featureCategory: String?

    enum CodingKeys: String, CodingKey {
        case id, name, template
        case userId = "user_id"
        case requiredContext = "required_context"
        case compatibleTypes = "compatible_types"
        case featureCategory = "feature_category"
    }
}

struct FeatureCreate: Codable {
    var name: String
    var template: String
    var userId: Int?
    var requiredContext: [String]?
    var compatibleTypes: [String]?
    var featureCategory: String?

    enum CodingKeys: String, CodingKey {
        case name, template
        case userId = "user_id"
        case requiredContext = "required_context"
        case compatibleTypes = "compatible_types"
        case featureCategory = "feature_category"
    }
}

struct FeatureUpdate: Codable {
    var name: String?
    var template: String?
    var requiredContext: [String]?
    var compatibleTypes: [String]?
    var featureCategory: String?

    enum CodingKeys: String, CodingKey {
        case name, template
        case requiredContext = "required_context"
        case compatibleTypes = "compatible_types"
        case featureCategory = "feature_category"
    }
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
    var userId: Int?
    var items: [RollTableItem]

    enum CodingKeys: String, CodingKey {
        case id, name, description, items
        case userId = "user_id"
    }
}

struct RollTableCreate: Codable {
    var name: String
    var description: String?
    var userId: Int?
    var items: [RollTableItemCreate]

    enum CodingKeys: String, CodingKey {
        case name, description, items
        case userId = "user_id"
    }
}

struct RollTableUpdate: Codable {
    var name: String?
    var description: String?
    var items: [RollTableItemCreate]?
}

struct RollTableItem: Codable, Identifiable {
    let id: Int
    let rollTableId: Int
    var minRoll: Int
    var maxRoll: Int
    var description: String

    enum CodingKeys: String, CodingKey {
        case id, description
        case rollTableId = "roll_table_id"
        case minRoll = "min_roll"
        case maxRoll = "max_roll"
    }
}

struct RollTableItemCreate: Codable {
    var minRoll: Int
    var maxRoll: Int
    var description: String

    enum CodingKeys: String, CodingKey {
        case description
        case minRoll = "min_roll"
        case maxRoll = "max_roll"
    }
}

struct RollTableItemUpdate: Codable {
    var minRoll: Int?
    var maxRoll: Int?
    var description: String?

    enum CodingKeys: String, CodingKey {
        case description
        case minRoll = "min_roll"
        case maxRoll = "max_roll"
    }
}

struct RandomItemResponse: Codable {
    let tableName: String
    let item: String?

    enum CodingKeys: String, CodingKey {
        case item
        case tableName = "table_name"
    }
}

struct TableNameListResponse: Codable {
    let tableNames: [String]

    enum CodingKeys: String, CodingKey {
        case tableNames = "table_names"
    }
}

// MARK: - Character Models

struct CharacterCreate: Codable {
    var name: String
    var description: String?
    var appearanceDescription: String?
    var imageUrls: [String]?
    var videoClipUrls: [String]?
    var notesForLlm: String?
    var stats: CharacterStats?
    var exportFormatPreference: String?

    enum CodingKeys: String, CodingKey {
        case name, description, stats
        case appearanceDescription = "appearance_description"
        case imageUrls = "image_urls"
        case videoClipUrls = "video_clip_urls"
        case notesForLlm = "notes_for_llm"
        case exportFormatPreference = "export_format_preference"
    }

    func toCharacterCreateDTO() -> CampaignCreatorLib.CharacterCreateDTO {
        return CampaignCreatorLib.CharacterCreateDTO(
            name: self.name,
            description: self.description,
            appearanceDescription: self.appearanceDescription,
            imageURLs: self.imageUrls,
            notesForLLM: self.notesForLlm,
            stats: self.stats?.toCharacterStatsDTO(),
            exportFormatPreference: self.exportFormatPreference
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
    let accessToken: String
    let tokenType: String
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
