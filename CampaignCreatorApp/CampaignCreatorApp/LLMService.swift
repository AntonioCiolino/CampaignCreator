import Foundation
import SwiftUI
import SwiftData
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
            self.availableLLMs = localLLMs.map { AvailableLLM(id: $0.id, name: $0.name, modelType: $0.model_type, supportsTemperature: $0.supports_temperature, capabilities: $0.capabilities, description: $0.model_type) }
        } else {
            do {
                let response: LLMModelsResponse = try await apiService.performRequest(endpoint: "/llm/models")
                self.availableLLMs = response.models
                for llm in response.models {
                    let llmModel = LLMModel(id: llm.id, name: llm.name, model_type: llm.modelType ?? "", supports_temperature: llm.supportsTemperature, capabilities: llm.capabilities ?? [])
                    modelContext.insert(llmModel)
                }
                try modelContext.save()
            } catch {
                throw error
            }
        }
    }
}
