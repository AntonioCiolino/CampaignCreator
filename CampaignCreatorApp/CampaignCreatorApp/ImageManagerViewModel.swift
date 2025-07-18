import SwiftUI
import CampaignCreatorLib

@MainActor
class ImageManagerViewModel: ObservableObject {
    @Binding var imageURLs: [String]

    @Published var imagePrompt: String = ""
    @Published var newImageURL: String = ""
    @Published var isGeneratingImage: Bool = false
    @Published var showErrorAlert: Bool = false
    @Published var errorMessage: String = ""
    @Published var generationError: String?
    @Published var selectedModel: CampaignCreatorLib.ImageModelName = .openAIDalle
    @Published var generationStatus: String = ""

    private var debounceTimer: Timer?
    private let imageGenerationService: ImageGenerationService
    private let apiService = CampaignCreatorLib.APIService()

    init(imageURLs: Binding<[String]>) {
        self._imageURLs = imageURLs
        self.imageGenerationService = ImageGenerationService(apiService: self.apiService)
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
                let generatedImageURL = try await imageGenerationService.generateImage(prompt: imagePrompt, model: selectedModel)
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
