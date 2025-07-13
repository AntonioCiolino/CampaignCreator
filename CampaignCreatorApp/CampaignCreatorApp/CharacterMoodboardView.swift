import SwiftUI

struct CharacterMoodboardView: View {
    @StateObject private var viewModel: CharacterMoodboardViewModel
    @EnvironmentObject var imageUploadService: ImageUploadService
    var onCharacterUpdated: ((Character) -> Void)?

    init(character: Character, onCharacterUpdated: ((Character) -> Void)? = nil) {
        _viewModel = StateObject(wrappedValue: CharacterMoodboardViewModel(character: character))
        self.onCharacterUpdated = onCharacterUpdated
    }

    var body: some View {
        CommonMoodBoardView(
            imageURLs: $viewModel.imageURLs,
            onSave: {
                viewModel.saveCharacterMoodboard()
                onCharacterUpdated?(viewModel.character)
            },
            onGenerateAIImage: nil,
            imageUploadService: imageUploadService
        )
        .onChange(of: viewModel.imageURLs) { _ in
            viewModel.saveCharacterMoodboard()
            onCharacterUpdated?(viewModel.character)
        }
    }
}
