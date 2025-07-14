import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CampaignMoodboardViewModel: ObservableObject {
    @Published var campaign: CampaignModel
    @Published var moodBoardImageURLs: [String]

    private var apiService = CampaignCreatorLib.APIService()

    init(campaign: CampaignModel) {
        self.campaign = campaign
        self.moodBoardImageURLs = campaign.mood_board_image_urls ?? []
    }

}
