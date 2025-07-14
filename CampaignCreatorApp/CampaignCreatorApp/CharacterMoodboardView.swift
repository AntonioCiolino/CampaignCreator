import SwiftUI

struct CharacterMoodboardView: View {
    @Bindable var character: CharacterModel
    @EnvironmentObject var imageUploadService: ImageUploadService

    var body: some View {
        CommonMoodBoardView(
            imageURLs: .init(get: { character.image_urls ?? [] }, set: { character.image_urls = $0 }),
            onSave: {
                // No need to do anything here, as the changes are saved automatically
            },
            onGenerateAIImage: nil,
            imageUploadService: imageUploadService
        )
    }
}
