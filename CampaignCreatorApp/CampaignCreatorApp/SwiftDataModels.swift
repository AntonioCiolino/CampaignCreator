import Foundation
import SwiftData
import CampaignCreatorLib

@Model
final class CampaignModel: Identifiable {
    var id: UUID = UUID()
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

    init(
        title: String,
        concept: String? = nil,
        initial_user_prompt: String? = nil,
        sections: [CampaignSection]? = nil,
        owner_id: Int,
        badge_image_url: String? = nil,
        thematic_image_url: String? = nil,
        thematic_image_prompt: String? = nil,
        selected_llm_id: String? = nil,
        temperature: Float? = nil,
        theme_primary_color: String? = nil,
        theme_secondary_color: String? = nil,
        theme_background_color: String? = nil,
        theme_text_color: String? = nil,
        theme_font_family: String? = nil,
        theme_background_image_url: String? = nil,
        theme_background_image_opacity: Float? = nil,
        mood_board_image_urls: [String]? = nil
    ) {
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
    }

    var wordCount: Int {
        return sections?.reduce(0) { $0 + $1.content.components(separatedBy: .whitespacesAndNewlines).filter { !$0.isEmpty }.count } ?? 0
    }
}

@Model
final class CharacterModel: Identifiable {
    var id: UUID = UUID()
    var name: String
    var character_description: String?
    var appearance_description: String?
    var image_urls: [String]?
    var video_clip_urls: [String]?
    var notes_for_llm: String?
    @Attribute(.transformable(by: "CharacterStatsTransformer"))
    var stats: CharacterStats
    var export_format_preference: String?
    var owner_id: Int
    var campaign_ids: [Int]?

    init(
        name: String,
        character_description: String? = nil,
        appearance_description: String? = nil,
        image_urls: [String]? = nil,
        video_clip_urls: [String]? = nil,
        notes_for_llm: String? = nil,
        stats: CharacterStats = CharacterStats(),
        export_format_preference: String? = nil,
        owner_id: Int,
        campaign_ids: [Int]? = nil
    ) {
        self.name = name
        self.character_description = character_description
        self.appearance_description = appearance_description
        self.image_urls = image_urls
        self.video_clip_urls = video_clip_urls
        self.notes_for_llm = notes_for_llm
        self.stats = stats
        self.export_format_preference = export_format_preference
        self.owner_id = owner_id
        self.campaign_ids = campaign_ids
    }
}

struct CampaignSection: Codable, Identifiable {
    let id: Int
    let campaign_id: Int
    var title: String?
    var content: String
    var order: Int
    var type: String?
}

struct CharacterStats: Codable {
    var strength: Int? = 10
    var dexterity: Int? = 10
    var constitution: Int? = 10
    var intelligence: Int? = 10
    var wisdom: Int? = 10
    var charisma: Int? = 10

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
}

class CharacterStatsTransformer: ValueTransformer {
    override class func transformedValueClass() -> AnyClass {
        return NSData.self
    }

    override class func allowsReverseTransformation() -> Bool {
        return true
    }

    override func transformedValue(_ value: Any?) -> Any? {
        guard let stats = value as? CharacterStats else { return nil }

        do {
            let data = try JSONEncoder().encode(stats)
            return data
        } catch {
            print("Failed to encode CharacterStats: \(error)")
            return nil
        }
    }

    override func reverseTransformedValue(_ value: Any?) -> Any? {
        guard let data = value as? Data else { return nil }

        do {
            let stats = try JSONDecoder().decode(CharacterStats.self, from: data)
            return stats
        } catch {
            print("Failed to decode CharacterStats: \(error)")
            return nil
        }
    }
}
