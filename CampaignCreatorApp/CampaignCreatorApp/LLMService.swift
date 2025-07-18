import Foundation
import CampaignCreatorLib

@MainActor
class LLMService: ObservableObject {
    @Published var availableLLMs: [AvailableLLM] = []
    @Published var errorMessage: String?

    private let apiService: CampaignCreatorLib.APIService

    init(apiService: CampaignCreatorLib.APIService = CampaignCreatorLib.APIService()) {
        self.apiService = apiService
    }

    func fetchAvailableLLMs() async {
        guard let token = UserDefaultsTokenManager().getToken() else {
            errorMessage = "Authentication token not found."
            return
        }

        let endpoint = "/llms/available"

        do {
            let response: LLMModelsResponse = try await apiService.get(endpoint: endpoint, token: token)
            self.availableLLMs = response.models
        } catch {
            self.errorMessage = "Failed to fetch available LLMs: \(error.localizedDescription)"
        }
    }
}
