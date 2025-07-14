import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CampaignDetailViewModel: ObservableObject {
    @Published var availableLLMs: [AvailableLLM] = []
    private var apiService = CampaignCreatorLib.APIService()

    nonisolated func fetchAvailableLLMs() async throws -> [AvailableLLM] {
        let llms = try await apiService.fetchAvailableLLMs()
        return llms.map { AvailableLLM(id: $0.id, name: $0.name) }
    }

    func refreshCampaign(campaign: CampaignModel) async {
        // In a real app, you would fetch the latest campaign data from the server.
        // For now, we'll just print a message.
        print("Refreshing campaign...")
    }
}
