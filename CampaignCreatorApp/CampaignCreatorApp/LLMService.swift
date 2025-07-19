import Foundation
import CampaignCreatorLib

@MainActor
class LLMService: ObservableObject {
    @Published var availableLLMs: [AvailableLLM] = []

    let apiService: CampaignCreatorLib.APIService

    init(apiService: CampaignCreatorLib.APIService = CampaignCreatorLib.APIService()) {
        self.apiService = apiService
    }

    func fetchAvailableLLMs() async throws {
        do {
            let response: LLMModelsResponse = try await apiService.performRequest(endpoint: "/llm/models")
            self.availableLLMs = response.models
        } catch {
            throw error
        }
    }
}
