import Foundation
import SwiftData
import CampaignCreatorLib

@Model
final class CampaignModel: Identifiable {
    var id: Int = 0
    var title: String
    var concept: String?
    var initial_user_prompt: String?
    var sections: [CampaignSection]?
    var owner_id: Int
    var badge_image_url: String?
    var thematic_image_url: String?
    var thematic_image_prompt: String?
    var selected_llm_id: String?
    var temperature: Double?
    var theme_primary_color: String?
    var theme_secondary_color: String?
    var theme_background_color: String?
    var theme_text_color: String?
    var theme_font_family: String?
    var theme_background_image_url: String?
    var theme_background_image_opacity: Double?
    var mood_board_image_urls_string: String?
    var linked_character_ids_string: String?
    var needsSync: Bool = false
    var display_toc: [TOCEntry]?

    var mood_board_image_urls: [String]? {
        get {
            mood_board_image_urls_string?.components(separatedBy: ",")
        }
        set {
            mood_board_image_urls_string = newValue?.joined(separator: ",")
        }
    }

    var linked_character_ids: [Int]? {
        get {
            linked_character_ids_string?.components(separatedBy: ",").compactMap { Int($0) }
        }
        set {
            linked_character_ids_string = newValue?.map { String($0) }.joined(separator: ",")
        }
    }

    init(
        id: Int,
        title: String,
        concept: String? = nil,
        initial_user_prompt: String? = nil,
        sections: [CampaignSection]? = nil,
        owner_id: Int,
        badge_image_url: String? = nil,
        thematic_image_url: String? = nil,
        thematic_image_prompt: String? = nil,
        selected_llm_id: String? = nil,
        temperature: Double? = nil,
        theme_primary_color: String? = nil,
        theme_secondary_color: String? = nil,
        theme_background_color: String? = nil,
        theme_text_color: String? = nil,
        theme_font_family: String? = nil,
        theme_background_image_url: String? = nil,
        theme_background_image_opacity: Double? = nil,
        mood_board_image_urls: [String]? = nil,
        linked_character_ids: [Int]? = nil,
        display_toc: [TOCEntry]? = nil
    ) {
        self.id = id
        self.title = title
        self.concept = concept
        self.initial_user_prompt = initial_user_prompt
        self.sections = sections
        self.owner_id = owner_id
        self.badge_image_url = badge_image_url
        self.thematic_image_url = thematic_image_url
        self.thematic_image_prompt = thematic_image_prompt
        self.selected_llm_id = selected_llm_id
        self.temperature = temperature
        self.theme_primary_color = theme_primary_color
        self.theme_secondary_color = theme_secondary_color
        self.theme_background_color = theme_background_color
        self.theme_text_color = theme_text_color
        self.theme_font_family = theme_font_family
        self.theme_background_image_url = theme_background_image_url
        self.theme_background_image_opacity = theme_background_image_opacity
        self.mood_board_image_urls = mood_board_image_urls
        self.linked_character_ids = linked_character_ids
        self.display_toc = display_toc
    }

    static func from(campaign: CampaignCreatorLib.Campaign) -> CampaignModel {
        let model = CampaignModel(
            id: campaign.id,
            title: campaign.title,
            concept: campaign.concept,
            initial_user_prompt: campaign.initialUserPrompt,
            owner_id: 0, // TODO: Get owner_id from somewhere
            badge_image_url: campaign.badgeImageURL,
            thematic_image_url: campaign.thematicImageURL,
            thematic_image_prompt: campaign.thematicImagePrompt,
            selected_llm_id: campaign.selectedLLMId,
            temperature: campaign.temperature,
            theme_primary_color: campaign.themePrimaryColor,
            theme_secondary_color: campaign.themeSecondaryColor,
            theme_background_color: campaign.themeBackgroundColor,
            theme_text_color: campaign.themeTextColor,
            theme_font_family: campaign.themeFontFamily,
            theme_background_image_url: campaign.themeBackgroundImageURL,
            theme_background_image_opacity: campaign.themeBackgroundImageOpacity,
            display_toc: campaign.displayTOC?.map { TOCEntry(from: $0) }
        )
        model.mood_board_image_urls = campaign.moodBoardImageURLs
        model.linked_character_ids = campaign.linkedCharacterIDs
        model.sections = campaign.sections.map { CampaignSection(id: $0.id, campaign_id: $0.campaign_id ?? 0, title: $0.title, content: $0.content, order: $0.order, type: $0.type) }
        return model
    }

    var wordCount: Int {
        return sections?.reduce(0) { $0 + $1.content.components(separatedBy: .whitespacesAndNewlines).filter { !$0.isEmpty }.count } ?? 0
    }
}

@Model
final class CharacterModel: Identifiable {
    var id: Int = 0
    var name: String
    var character_description: String?
    var appearance_description: String?
    var image_urls: [String]?
    var video_clip_urls: [String]?
    var notes_for_llm: String?
    var strength: Int? = 10
    var dexterity: Int? = 10
    var constitution: Int? = 10
    var intelligence: Int? = 10
    var wisdom: Int? = 10
    var charisma: Int? = 10
    var export_format_preference: String?
    var owner_id: Int
    var campaign_ids: [Int]?
    var selected_llm_id: String?
    var temperature: Double?
    @Relationship(inverse: \ChatMessageModel.character) var messages: [ChatMessageModel]? = []
    @Relationship(inverse: \MemoryModel.character) var memories: [MemoryModel]? = []
    var needsSync: Bool = false


    init(
        id: Int,
        name: String,
        character_description: String? = nil,
        appearance_description: String? = nil,
        image_urls: [String]? = nil,
        video_clip_urls: [String]? = nil,
        notes_for_llm: String? = nil,
        strength: Int? = 10,
        dexterity: Int? = 10,
        constitution: Int? = 10,
        intelligence: Int? = 10,
        wisdom: Int? = 10,
        charisma: Int? = 10,
        export_format_preference: String? = nil,
        owner_id: Int,
        campaign_ids: [Int]? = nil,
        selected_llm_id: String? = nil,
        temperature: Double? = nil
    ) {
        self.id = id
        self.name = name
        self.character_description = character_description
        self.appearance_description = appearance_description
        self.image_urls = image_urls
        self.video_clip_urls = video_clip_urls
        self.notes_for_llm = notes_for_llm
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma
        self.export_format_preference = export_format_preference
        self.owner_id = owner_id
        self.campaign_ids = campaign_ids
        self.selected_llm_id = selected_llm_id
        self.temperature = temperature
    }

    static func from(character: CampaignCreatorLib.Character) -> CharacterModel {
        return CharacterModel(
            id: character.id,
            name: character.name,
            character_description: character.description,
            appearance_description: character.appearanceDescription,
            image_urls: character.imageURLs,
            notes_for_llm: character.notesForLLM,
            strength: character.stats?.strength,
            dexterity: character.stats?.dexterity,
            constitution: character.stats?.constitution,
            intelligence: character.stats?.intelligence,
            wisdom: character.stats?.wisdom,
            charisma: character.stats?.charisma,
            export_format_preference: character.exportFormatPreference,
            owner_id: 0, // TODO: Get owner_id from somewhere
            selected_llm_id: character.selectedLLMId,
            temperature: character.temperature
        )
    }
}

@Model
class MemoryModel: Identifiable {
    @Attribute(.unique) var id: String = UUID().uuidString
    var summary: String
    var timestamp: Date
    var character: CharacterModel?
    var user: UserModel?

    init(summary: String, timestamp: Date) {
        self.summary = summary
        self.timestamp = timestamp
    }
}

struct CampaignSection: Codable, Identifiable, Hashable {
    let id: Int
    let campaign_id: Int
    var title: String?
    var content: String
    var order: Int
    var type: String?

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: CampaignSection, rhs: CampaignSection) -> Bool {
        lhs.id == rhs.id
    }
}

@Model
final class ChatMessageModel: Identifiable {
    @Attribute(.unique) var id: String = UUID().uuidString
    var text: String
    var sender: String // "user" or "llm"
    var timestamp: Date
    var character: CharacterModel?
    var user: UserModel?

    init(
        text: String,
        sender: String,
        timestamp: Date
    ) {
        self.text = text
        self.sender = sender
        self.timestamp = timestamp
    }
}

@Model
final class UserModel: Identifiable {
    @Attribute(.unique) var id: Int
    var username: String
    var email: String?
    var fullName: String?
    var avatarUrl: String?

    init(id: Int, username: String, email: String?, fullName: String?, avatarUrl: String?) {
        self.id = id
        self.username = username
        self.email = email
        self.fullName = fullName
        self.avatarUrl = avatarUrl
    }

    static func from(user: User) -> UserModel {
        return UserModel(
            id: user.id,
            username: user.username,
            email: user.email,
            fullName: user.fullName,
            avatarUrl: user.avatarUrl
        )
    }
}

struct TOCEntry: Codable, Identifiable {
    var id = UUID()
    let title: String?
    let type: String?

    enum CodingKeys: String, CodingKey {
        case title
        case type
    }

    init(from apiTocEntry: CampaignCreatorLib.TOCEntry) {
        self.title = apiTocEntry.title
        self.type = apiTocEntry.type
    }
}

struct SeedSectionsEvent: Codable {
    let event_type: String
    let message: String?
    let progress_percent: Double?
    let current_section_title: String?
    let total_sections_processed: Int?
    let section_data: CampaignSection?
}
