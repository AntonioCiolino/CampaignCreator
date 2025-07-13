import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterMoodboardViewModel: ObservableObject {
    @Published var character: Character
    @Published var imageURLs: [String]

    private var apiService = CampaignCreatorLib.APIService()

    init(character: Character) {
        self.character = character
        self.imageURLs = character.image_urls ?? []
    }

    func saveCharacterMoodboard() {
        var updatedCharacter = character
        updatedCharacter.image_urls = imageURLs
        Task {
            do {
                let characterUpdate = CharacterUpdate(
                    name: updatedCharacter.name,
                    description: updatedCharacter.description,
                    appearance_description: updatedCharacter.appearance_description,
                    image_urls: updatedCharacter.image_urls,
                    video_clip_urls: updatedCharacter.video_clip_urls,
                    notes_for_llm: updatedCharacter.notes_for_llm,
                    stats: updatedCharacter.stats,
                    export_format_preference: updatedCharacter.export_format_preference
                )
                let body = try JSONEncoder().encode(characterUpdate)
                let _: Character = try await apiService.performRequest(endpoint: "/characters/\\(character.id)", method: "PUT", body: body)
            } catch {
                print("Failed to save character moodboard: \\(error)")
            }
        }
    }
}
