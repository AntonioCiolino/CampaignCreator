import Foundation
import CampaignCreatorLib

@MainActor
class LLMService: ObservableObject {
    @Published var availableLLMs: [AvailableLLM] = []

    let apiService: CampaignCreatorLib.APIService

    init(apiService: CampaignCreatorLib.APIService = CampaignCreatorLib.APIService()) {
        self.apiService = apiService
    }

    @Environment(\.modelContext) private var modelContext

    func fetchAvailableLLMs() async throws {
        let descriptor = FetchDescriptor<LLMModel>()
        let localLLMs = try? modelContext.fetch(descriptor)

        if let localLLMs = localLLMs, !localLLMs.isEmpty {
            self.availableLLMs = localLLMs.map { AvailableLLM(id: $0.id, name: $0.name, description: $0.model_type, supports_temperature: $0.supports_temperature, capabilities: $0.capabilities) }
        } else {
            do {
                let response: LLMModelsResponse = try await apiService.performRequest(endpoint: "/llm/models")
                self.availableLLMs = response.models
                for llm in response.models {
                    let llmModel = LLMModel(id: llm.id, name: llm.name, model_type: llm.model_type, supports_temperature: llm.supports_temperature, capabilities: llm.capabilities)
                    modelContext.insert(llmModel)
                }
                try modelContext.save()
            } catch {
                throw error
            }
        }
    }
}
