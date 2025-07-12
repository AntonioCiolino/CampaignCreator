import SwiftUI
import CampaignCreatorLib

struct CharacterMoodboardView: View {
    @State var character: Character
    @ObservedObject var campaignCreator: CampaignCreator
    @EnvironmentObject var imageUploadService: ImageUploadService
    var onCharacterUpdated: ((Character) -> Void)?

    @State private var imageURLs: [String]

    init(campaignCreator: CampaignCreator, character: Character, onCharacterUpdated: ((Character) -> Void)? = nil) {
        self.campaignCreator = campaignCreator
        self._character = State(initialValue: character)
        self.onCharacterUpdated = onCharacterUpdated
        self._imageURLs = State(initialValue: character.imageURLs ?? [])
    }

    var body: some View {
        CommonMoodBoardView(
            imageURLs: $imageURLs,
            onSave: {
                saveCharacterMoodboard()
            },
            onGenerateAIImage: nil,
            imageUploadService: imageUploadService
        )
        .onChange(of: imageURLs) { _ in
            saveCharacterMoodboard()
        }
    }

    private func saveCharacterMoodboard() {
        var updatedCharacter = character
        updatedCharacter.imageURLs = imageURLs
        Task {
            do {
                let savedCharacter = try await campaignCreator.updateCharacter(updatedCharacter)
                onCharacterUpdated?(savedCharacter)
            } catch {
                // Handle error
                print("Failed to save character moodboard: \(error)")
            }
        }
    }
}
