import Foundation
import SwiftUI

@MainActor
class CampaignListViewModel: ObservableObject {
    @Published var campaigns: [Campaign] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var apiService = APIService()

    func fetchCampaigns() async {
        isLoading = true
        errorMessage = nil
        do {
            let fetchedCampaigns: [Campaign] = try await apiService.performRequest(endpoint: "/campaigns/")
            self.campaigns = fetchedCampaigns
        } catch {
            self.errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func deleteCampaign(_ campaign: Campaign) async {
        isLoading = true
        errorMessage = nil
        do {
            try await apiService.performVoidRequest(endpoint: "/campaigns/\\(campaign.id)", method: "DELETE")
            await fetchCampaigns()
        } catch {
            self.errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
