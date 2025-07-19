import SwiftUI
import SwiftData

struct CharacterMoodboardView: View {
    @Bindable var character: CharacterModel
    @Environment(\.modelContext) private var modelContext
    @EnvironmentObject var imageUploadService: ImageUploadService
    var onSetBadgeAction: () -> Void

    var body: some View {
        VStack {
            CommonMoodBoardView(
                imageURLs: Binding(
                    get: { character.image_urls ?? [] },
                    set: { character.image_urls = $0 }
                ),
                onSave: {
                    try? modelContext.save()
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
