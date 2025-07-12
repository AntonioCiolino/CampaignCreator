import SwiftUI
import CampaignCreatorLib

struct CharacterMoodboardView: View {
    @State var character: Character
    @ObservedObject var campaignCreator: CampaignCreator

    @State private var moodboardImageURLs: [String]

    var onCharacterUpdated: ((Character) -> Void)?

    init(campaignCreator: CampaignCreator, character: Character, onCharacterUpdated: ((Character) -> Void)? = nil) {
        self.campaignCreator = campaignCreator
        self._character = State(initialValue: character)
        self.onCharacterUpdated = onCharacterUpdated
        self._moodboardImageURLs = State(initialValue: character.imageURLs ?? [])
    }

    var body: some View {
        CommonMoodboardView(
            title: "\(character.name) Moodboard",
            imageURLs: $moodboardImageURLs,
            onSave: { newImageURLs in
                Task {
                    await saveMoodboardChanges(newImageURLs: newImageURLs)
                }
            }
        )
    }

    private func saveMoodboardChanges(newImageURLs: [String]) async {
        var updatedCharacter = character
        updatedCharacter.imageURLs = newImageURLs
        updatedCharacter.markAsModified()

        do {
            let savedCharacter = try await campaignCreator.updateCharacter(updatedCharacter)
            onCharacterUpdated?(savedCharacter)
            // Optionally, show a success message
        } catch {
            // Optionally, show an error message
        }
    }
}
