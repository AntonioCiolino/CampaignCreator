import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CampaignDetailViewModel: ObservableObject {
    @Published var availableLLMs: [AvailableLLM] = []
    private var apiService = CampaignCreatorLib.APIService()

    func fetchAvailableLLMs() {
        Task {
            do {
                let llms = try await apiService.fetchAvailableLLMs()
                let mappedLLMs = llms.map { AvailableLLM(id: $0.id, name: $0.name, modelType: $0.modelType, supportsTemperature: $0.supportsTemperature) }
                await MainActor.run {
                    self.availableLLMs = mappedLLMs
                }
            } catch {
                print("Error fetching available LLMs: \(error.localizedDescription)")
            }
        }
    }

    func refreshCampaign(campaign: CampaignModel) async {
        // In a real app, you would fetch the latest campaign data from the server.
        // For now, we'll just print a message.
        print("Refreshing campaign...")
    }
}
