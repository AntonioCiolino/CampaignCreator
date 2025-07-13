import Foundation
import SwiftUI

@MainActor
class CampaignDetailViewModel: ObservableObject {
    @Published var campaign: Campaign
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var apiService = APIService()

    init(campaign: Campaign) {
        self.campaign = campaign
    }

    func refreshCampaign() async {
        isLoading = true
        errorMessage = nil
        do {
            let refreshedCampaign: Campaign = try await apiService.performRequest(endpoint: "/campaigns/\\(campaign.id)")
            self.campaign = refreshedCampaign
        } catch {
            self.errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
