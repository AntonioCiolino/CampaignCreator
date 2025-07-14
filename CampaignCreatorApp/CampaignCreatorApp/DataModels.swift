//
//  DataModels.swift
//  CampaignCreatorApp
//
//  Created by Jules on 6/20/24.
//
//  NOTE: The @Model macro requires that all stored properties be declared as 'var' instead of 'let'.
//  This is because the macro synthesizes the storage for the properties and needs to be able to modify them.
//  Do not change the 'var' declarations to 'let' in the Campaign and Character models.
//

import Foundation
import SwiftData
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

@Model
final class Campaign: Identifiable {
    var id: Int
    var title: String
    var concept: String?
    var initial_user_prompt: String?
    var sections: [CampaignSection]?
    var owner_id: Int
    var badge_image_url: String?
    var thematic_image_url: String?
    var thematic_image_prompt: String?
    var selected_llm_id: String?
    var temperature: Float?
    var theme_primary_color: String?
    var theme_secondary_color: String?
    var theme_background_color: String?
    var theme_text_color: String?
    var theme_font_family: String?
    var theme_background_image_url: String?
    var theme_background_image_opacity: Float?
    var mood_board_image_urls: [String]?

    init(from libCampaign: CampaignCreatorLib.Campaign) {
        self.id = libCampaign.id
        self.title = libCampaign.title
        self.concept = libCampaign.concept
        self.initial_user_prompt = libCampaign.initialUserPrompt
        self.sections = libCampaign.sections.map { CampaignSection(from: $0) }
        self.owner_id = 0 // This will need to be set from user context
        self.badge_image_url = libCampaign.badgeImageURL
        self.thematic_image_url = libCampaign.thematicImageURL
        self.thematic_image_prompt = libCampaign.thematicImagePrompt
        self.selected_llm_id = libCampaign.selectedLLMId
        self.temperature = Float(libCampaign.temperature ?? 0.7)
        self.theme_primary_color = libCampaign.themePrimaryColor
        self.theme_secondary_color = libCampaign.themeSecondaryColor
        self.theme_background_color = libCampaign.themeBackgroundColor
        self.theme_text_color = libCampaign.themeTextColor
        self.theme_font_family = libCampaign.themeFontFamily
        self.theme_background_image_url = libCampaign.themeBackgroundImageURL
        self.theme_background_image_opacity = Float(libCampaign.themeBackgroundImageOpacity ?? 1.0)
        self.mood_board_image_urls = libCampaign.moodBoardImageURLs
    }
}

extension Campaign {
    var wordCount: Int {
        return sections?.reduce(0) { $0 + $1.content.components(separatedBy: .whitespacesAndNewlines).filter { !$0.isEmpty }.count } ?? 0
    }

    func toCampaignUpdateDTO() -> CampaignCreatorLib.CampaignUpdateDTO {
        return CampaignCreatorLib.CampaignUpdateDTO(
            title: self.title,
            initialUserPrompt: self.initial_user_prompt,
            concept: self.concept,
            displayTOC: nil, // Not available in app model
            badgeImageURL: self.badge_image_url,
            thematicImageURL: self.thematic_image_url,
            thematicImagePrompt: self.thematic_image_prompt,
            selectedLLMId: self.selected_llm_id,
            temperature: Double(self.temperature ?? 0.7),
            moodBoardImageURLs: self.mood_board_image_urls,
            themePrimaryColor: self.theme_primary_color,
            themeSecondaryColor: self.theme_secondary_color,
            themeBackgroundColor: self.theme_background_color,
            themeTextColor: self.theme_text_color,
            themeFontFamily: self.theme_font_family,
            themeBackgroundImageURL: self.theme_background_image_url,
            themeBackgroundImageOpacity: Double(self.theme_background_image_opacity ?? 1.0),
            linkedCharacterIDs: nil, // Not available in app model
            customSections: nil, // Not available in app model
            sections: self.sections?.map { $0.toCampaignSectionDTO() }
        )
    }
}

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

struct CampaignSection: Codable, Identifiable {
    let id: Int
    let campaign_id: Int
    var title: String?
    var content: String
    var order: Int
    var type: String?

    func toCampaignSectionDTO() -> CampaignCreatorLib.CampaignSection {
        return CampaignCreatorLib.CampaignSection(
            id: self.id,
            title: self.title,
            content: self.content,
            order: self.order,
            type: self.type
        )
    }
}

extension CampaignSection {
    init(from libSection: CampaignCreatorLib.CampaignSection) {
        self.id = libSection.id
        self.title = libSection.title
        self.content = libSection.content
        self.order = libSection.order
        self.type = libSection.type
        self.campaign_id = 0 // This will need to be set from context
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

@Model
final class Character: Identifiable {
    var id: Int
    var name: String
    var character_description: String?
    var appearance_description: String?
    var image_urls: [String]?
    var video_clip_urls: [String]?
    var notes_for_llm: String?
    var stats: CharacterStats?
    var export_format_preference: String?
    var owner_id: Int
    var campaign_ids: [Int]?

    init(from libCharacter: CampaignCreatorLib.Character) {
        self.id = libCharacter.id
        self.name = libCharacter.name
        self.character_description = libCharacter.description
        self.appearance_description = libCharacter.appearanceDescription
        self.image_urls = libCharacter.imageURLs
        self.video_clip_urls = libCharacter.video_clip_urls
        self.notes_for_llm = libCharacter.notesForLLM
        self.stats = CharacterStats(from: libCharacter.stats)
        self.export_format_preference = libCharacter.exportFormatPreference
        self.owner_id = libCharacter.ownerID ?? 0
        self.campaign_ids = libCharacter.campaignIDs
    }

    convenience init(
        id: Int,
        name: String,
        character_description: String? = nil,
        appearance_description: String? = nil,
        image_urls: [String]? = nil,
        video_clip_urls: [String]? = nil,
        notes_for_llm: String? = nil,
        stats: CharacterStats? = nil,
        export_format_preference: String? = nil,
        owner_id: Int,
        campaign_ids: [Int]? = nil
    ) {
        self.init(from: CampaignCreatorLib.Character(id: id, name: name, description: character_description, appearanceDescription: appearance_description, imageURLs: image_urls, video_clip_urls: video_clip_urls, notesForLLM: notes_for_llm, stats: stats?.toLib(), exportFormatPreference: export_format_preference, ownerID: owner_id, campaignIDs: campaign_ids))
    }

    convenience init(
        id: Int,
        name: String,
        owner_id: Int
    ) {
        self.init(from: CampaignCreatorLib.Character(id: id, name: name, description: nil, appearanceDescription: nil, imageURLs: nil, video_clip_urls: nil, notesForLLM: nil, stats: nil, exportFormatPreference: nil, ownerID: owner_id, campaignIDs: nil))
    }

    convenience init(
        id: Int,
        name: String,
        character_description: String?,
        appearance_description: String?,
        image_urls: [String]?,
        video_clip_urls: [String]?,
        notes_for_llm: String?,
        stats: CharacterStats?,
        export_format_preference: String?,
        owner_id: Int,
        campaign_ids: [Int]?
    ) {
        self.init(id: id, name: name, character_description: character_description, appearance_description: appearance_description, image_urls: image_urls, video_clip_urls: video_clip_urls, notes_for_llm: notes_for_llm, stats: stats, export_format_preference: export_format_preference, owner_id: owner_id, campaign_ids: campaign_ids)
    }
}

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

struct CharacterStats: Codable {
    var strength: Int?
    var dexterity: Int?
    var constitution: Int?
    var intelligence: Int?
    var wisdom: Int?
    var charisma: Int?

    func toCharacterStatsDTO() -> CampaignCreatorLib.CharacterStats {
        return CampaignCreatorLib.CharacterStats(
            strength: self.strength,
            dexterity: self.dexterity,
            constitution: self.constitution,
            intelligence: self.intelligence,
            wisdom: self.wisdom,
            charisma: self.charisma
        )
    }

    func toLib() -> CampaignCreatorLib.CharacterStats {
        return CampaignCreatorLib.CharacterStats(
            strength: self.strength,
            dexterity: self.dexterity,
            constitution: self.constitution,
            intelligence: self.intelligence,
            wisdom: self.wisdom,
            charisma: self.charisma
        )
    }
}

extension CharacterStats {
    init(from libStats: CampaignCreatorLib.CharacterStats?) {
        self.strength = libStats?.strength
        self.dexterity = libStats?.dexterity
        self.constitution = libStats?.constitution
        self.intelligence = libStats?.intelligence
        self.wisdom = libStats?.wisdom
        self.charisma = libStats?.charisma
    }
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
