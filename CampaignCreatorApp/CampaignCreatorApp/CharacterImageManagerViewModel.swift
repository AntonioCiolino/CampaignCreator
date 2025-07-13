import Foundation
import SwiftUI

@MainActor
class CharacterImageManagerViewModel: ObservableObject {
    @Binding var imageURLs: [String]
    let characterID: Int

    @Published var newImageURL: String = ""
    @Published var imagePrompt: String = ""
    @Published var selectedModel: ImageModelName = .openAIDalle
    @Published var isGeneratingImage: Bool = false
    @Published var generationError: String?
    @Published var showErrorAlert = false
    @Published var errorMessage = ""

    private var apiService = APIService()

    init(imageURLs: Binding<[String]>, characterID: Int) {
        _imageURLs = imageURLs
        self.characterID = characterID
    }

    func addURL() {
        let trimmedURL = newImageURL.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedURL.isEmpty {
            errorMessage = "URL cannot be empty."
            showErrorAlert = true
            return
        }
        if URL(string: trimmedURL) == nil {
             errorMessage = "Invalid URL format."
             showErrorAlert = true
             return
        }
        if imageURLs.contains(trimmedURL) {
            errorMessage = "This image URL has already been added."
            showErrorAlert = true
            return
        }
        imageURLs.append(trimmedURL)
        newImageURL = ""
    }

    func deleteURLs(at offsets: IndexSet) {
        imageURLs.remove(atOffsets: offsets)
    }

    func generateImage() {
        guard !imagePrompt.isEmpty else {
            generationError = "Image prompt cannot be empty."
            showErrorAlert = true
            return
        }

        isGeneratingImage = true
        generationError = nil

        let params = CharacterImageGenerationRequest(
            additional_prompt_details: imagePrompt,
            model_name: selectedModel.rawValue,
            size: "1024x1024",
            quality: selectedModel == .openAIDalle ? "standard" : nil,
            steps: nil,
            cfg_scale: nil,
            gemini_model_name: nil
        )

        Task {
            do {
                let body = try JSONEncoder().encode(params)
                let response: CharacterImageGenerationResponse = try await apiService.performRequest(endpoint: "/characters/\\(characterID)/generate-image", method: "POST", body: body)
                if let newURL = response.image_url, !newURL.isEmpty {
                    if !imageURLs.contains(newURL) {
                        imageURLs.append(newURL)
                    }
                    imagePrompt = ""
                } else {
                    generationError = "AI image generation succeeded but returned no URL."
                    showErrorAlert = true
                }
            } catch {
                generationError = "Failed to generate image: \\(error.localizedDescription)"
                showErrorAlert = true
            }
            isGeneratingImage = false
        }
    }
}

enum ImageModelName: String, CaseIterable, Codable {
    case openAIDalle = "dall-e"
    case stableDiffusion = "stable-diffusion"
}

struct CharacterImageGenerationResponse: Codable {
    let image_url: String?
    let prompt_used: String
}
