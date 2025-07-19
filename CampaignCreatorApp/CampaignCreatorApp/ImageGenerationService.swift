import Foundation
import CampaignCreatorLib

@MainActor
class ImageGenerationService: ObservableObject {
    private let apiService: CampaignCreatorLib.APIService

    init(apiService: CampaignCreatorLib.APIService = CampaignCreatorLib.APIService()) {
        self.apiService = apiService
    }

    func generateImage(prompt: String, model: String = "dall-e-3") async throws -> String {
        let payload = ImageGenerationParams(prompt: prompt, model: model)
        do {
            let response: ImageGenerationResponse = try await apiService.generateImage(payload: payload)
            return response.imageUrl
        } catch {
            throw error
        }
    }
}
