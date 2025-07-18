import SwiftUI

@MainActor
class CampaignImageManagerViewModel: ObservableObject {
    @Binding var imageURLs: [String]
    let campaignID: Int

    @Published var imagePrompt: String = ""
    @Published var newImageURL: String = ""
    @Published var isGeneratingImage: Bool = false
    @Published var showErrorAlert: Bool = false
    @Published var errorMessage: String = ""
    @Published var generationError: String?
    @Published var selectedModel: ImageModelName = .dalle3

    // Debounce for image prompt
    private var debounceTimer: Timer?

    init(imageURLs: Binding<[String]>, campaignID: Int) {
        self._imageURLs = imageURLs
        self.campaignID = campaignID
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

        Task {
            // Replace with actual API call
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            let generatedImageURL = "https://picsum.photos/seed/\(UUID().uuidString)/400/400"

            if !self.imageURLs.contains(generatedImageURL) {
                self.imageURLs.append(generatedImageURL)
            }
            self.isGeneratingImage = false
        }
    }
}

enum ImageModelName: String, CaseIterable {
    case dalle3 = "dall-e-3"
    case dalle2 = "dall-e-2"
}
