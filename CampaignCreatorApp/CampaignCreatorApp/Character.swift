import Foundation
import SwiftData

@Model
final class Character {
    var id: UUID
    var name: String
    var character_description: String?
    var appearance_description: String?
    var image_urls: [String]?
    var notes_for_llm: String?
    var export_format_preference: String?
    var owner_id: Int
    @Attribute(.transformable(by: "CharacterStatsTransformer"))
    var stats: CharacterStats

    init(
        id: UUID = UUID(),
        name: String,
        character_description: String? = nil,
        appearance_description: String? = nil,
        image_urls: [String]? = nil,
        notes_for_llm: String? = nil,
        export_format_preference: String? = nil,
        owner_id: Int,
        stats: CharacterStats = CharacterStats()
    ) {
        self.id = id
        self.name = name
        self.character_description = character_description
        self.appearance_description = appearance_description
        self.image_urls = image_urls
        self.notes_for_llm = notes_for_llm
        self.export_format_preference = export_format_preference
        self.owner_id = owner_id
        self.stats = stats
    }
}
