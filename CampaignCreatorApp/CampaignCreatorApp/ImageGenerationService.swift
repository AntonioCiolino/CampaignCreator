import Foundation
import CampaignCreatorLib

@MainActor
class ImageGenerationService: ObservableObject {
    private let apiService: CampaignCreatorLib.APIService

    init(apiService: CampaignCreatorLib.APIService) {
        self.apiService = apiService
    }

    func generateImage(prompt: String, model: CampaignCreatorLib.ImageModelName = .dalle3) async throws -> String {
        let payload = CampaignCreatorLib.ImageGenerationParams(prompt: prompt, model: model.rawValue)
        do {
            let response: CampaignCreatorLib.ImageGenerationResponse = try await apiService.generateImage(payload: payload)
            guard let imageUrl = response.imageUrl else {
                throw APIError.noData
            }
            return imageUrl
        } catch {
            throw error
        }
    }
}
