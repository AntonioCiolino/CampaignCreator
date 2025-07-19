import SwiftUI

struct CharacterMoodboardView: View {
    @Bindable var character: CharacterModel
    @EnvironmentObject var imageUploadService: ImageUploadService
    var onSetBadgeAction: () -> Void

    var body: some View {
        VStack {
            CommonMoodBoardView(
                imageURLs: .init(get: { character.image_urls ?? [] }, set: { character.image_urls = $0 }),
                name: character.name,
                onSave: {
                    // No need to do anything here, as the changes are saved automatically
                },
                onGenerateAIImage: { prompt in
                    // This will be handled by the CommonMoodBoardView
                    return ""
                },
                imageUploadService: imageUploadService
            )
            Button(action: {
                onSetBadgeAction()
            }) {
                Text("Set Character Badge from Moodboard")
            }
            .buttonStyle(.bordered)
            .padding(.top, 10)
        }
    }
}
