import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CampaignListViewModel: ObservableObject {
    @Published var campaigns: [Campaign] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var apiService = CampaignCreatorLib.APIService()

    func fetchCampaigns() async {
        isLoading = true
        errorMessage = nil
        do {
            let fetchedCampaigns: [Campaign] = try await apiService.fetchCampaigns() as! [Campaign]
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
            try await apiService.deleteCampaign(id: campaign.id)
            await fetchCampaigns()
        } catch {
            self.errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
