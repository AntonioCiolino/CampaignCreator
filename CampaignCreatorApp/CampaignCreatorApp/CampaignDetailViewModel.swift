import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CampaignDetailViewModel: ObservableObject {
    @Published var campaign: Campaign
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var apiService = CampaignCreatorLib.APIService()

    init(campaign: Campaign) {
        self.campaign = campaign
    }

    func refreshCampaign() async {
        isLoading = true
        errorMessage = nil
        do {
            let refreshedCampaign: Campaign = try await apiService.fetchCampaign(id: campaign.id) as! Campaign
            self.campaign = refreshedCampaign
        } catch {
            self.errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
