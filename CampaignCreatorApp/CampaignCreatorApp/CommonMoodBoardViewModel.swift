import Foundation
import SwiftUI

@MainActor
class CommonMoodBoardViewModel: ObservableObject {
    @Binding var imageURLs: [String]
    let onSave: () -> Void
    let onGenerateAIImage: ((String) async throws -> String)?
    let imageUploadService: ImageUploadService

    @Published var showingAddImageOptions = false
    @Published var showingAddURLSheet = false
    @Published var showingGenerateMoodboardImageSheet = false
    @Published var newImageURLInput: String = ""
    @Published var aiImagePromptInput: String = ""
    @Published var isGeneratingAIImage = false
    @Published var alertItem: AlertMessageItem?

    init(imageURLs: Binding<[String]>, onSave: @escaping () -> Void, onGenerateAIImage: ((String) async throws -> String)?, imageUploadService: ImageUploadService) {
        _imageURLs = imageURLs
        self.onSave = onSave
        self.onGenerateAIImage = onGenerateAIImage
        self.imageUploadService = imageUploadService
    }

    func addImageFromURL() async {
        let urlString = newImageURLInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: urlString) else {
            alertItem = AlertMessageItem(message: "Invalid URL provided.")
            return
        }

        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                alertItem = AlertMessageItem(message: "Failed to download image.")
                return
            }

            let filename = url.lastPathComponent
            let mimeType = response.mimeType ?? "application/octet-stream"
            let uploadResult = await imageUploadService.uploadImage(imageData: data, filename: filename, mimeType: mimeType)

            switch uploadResult {
            case .success(let newAzureURL):
                if !imageURLs.contains(newAzureURL) {
                    imageURLs.append(newAzureURL)
                    onSave()
                }
                showingAddURLSheet = false
            case .failure(let error):
                if case let .serverError(_, message) = error, let messageData = message?.data(using: .utf8) {
                    do {
                        let errorDetail = try JSONDecoder().decode(ErrorDetail.self, from: messageData)
                        alertItem = AlertMessageItem(message: "Failed to upload image: \\(errorDetail.detail)")
                    } catch {
                        alertItem = AlertMessageItem(message: "Failed to upload image: \\(error.localizedDescription)")
                    }
                } else {
                    alertItem = AlertMessageItem(message: "Failed to upload image: \\(error.localizedDescription)")
                }
            }
        } catch {
            alertItem = AlertMessageItem(message: "Failed to download image: \\(error.localizedDescription)")
        }
    }

    func generateAndAddAIImage() async {
        guard let onGenerateAIImage = onGenerateAIImage else {
            return
        }

        let prompt = aiImagePromptInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !prompt.isEmpty else {
            alertItem = AlertMessageItem(message: "AI image prompt cannot be empty.")
            return
        }

        isGeneratingAIImage = true
        do {
            let newAzureURL = try await onGenerateAIImage(prompt)
            if !imageURLs.contains(newAzureURL) {
                imageURLs.append(newAzureURL)
                onSave()
            }
            showingGenerateMoodboardImageSheet = false
        } catch {
            alertItem = AlertMessageItem(message: "Failed to generate AI image: \\(error.localizedDescription)")
        }
        isGeneratingAIImage = false
    }

    func deleteImage(urlString: String) {
        imageURLs.removeAll { $0 == urlString }
        onSave()
    }

    func moveImage(from source: IndexSet, to destination: Int) {
        imageURLs.move(fromOffsets: source, toOffset: destination)
        onSave()
    }
}
