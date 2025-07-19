import SwiftUI

@MainActor
class ImageManagerViewModel: ObservableObject {
    @Binding var imageURLs: [String]

    @Published var imagePrompt: String = ""
    @Published var newImageURL: String = ""
    @Published var isGeneratingImage: Bool = false
    @Published var showErrorAlert: Bool = false
    @Published var errorMessage: String = ""
    @Published var generationError: String?
    @Published var selectedModel: ImageModelName = .dalle3
    @Published var generationStatus: String = ""

    private var debounceTimer: Timer?
    private let imageGenerationService = ImageGenerationService()

    init(imageURLs: Binding<[String]>) {
        self._imageURLs = imageURLs
    }

    func addURL() {
        guard let url = URL(string: newImageURL), UIApplication.shared.canOpenURL(url) else {
            errorMessage = "Invalid URL format."
            showErrorAlert = true
            return
        }
        if !imageURLs.contains(newImageURL) {
            imageURLs.append(newImageURL)
        }
        newImageURL = ""
    }

    func deleteURLs(at offsets: IndexSet) {
        imageURLs.remove(atOffsets: offsets)
    }

    func generateImage() {
        debounceTimer?.invalidate()
        isGeneratingImage = true
        generationError = nil
        generationStatus = "Generating image..."

        Task {
            do {
                let generatedImageURL = try await imageGenerationService.generateImage(prompt: imagePrompt, model: selectedModel.rawValue)
                if !self.imageURLs.contains(generatedImageURL) {
                    self.imageURLs.append(generatedImageURL)
                }
                self.generationStatus = "Image generated successfully!"
                self.isGeneratingImage = false
            } catch {
                self.generationError = error.localizedDescription
                self.generationStatus = "Image generation failed."
                self.showErrorAlert = true
                self.isGeneratingImage = false
            }
        }
    }
}
