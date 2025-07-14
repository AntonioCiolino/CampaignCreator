import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CampaignMoodboardViewModel: ObservableObject {
    @Published var campaign: Campaign
    @Published var moodBoardImageURLs: [String]

    private var apiService = CampaignCreatorLib.APIService()

    init(campaign: Campaign) {
        self.campaign = campaign
        self.moodBoardImageURLs = campaign.mood_board_image_urls ?? []
    }

    func saveMoodboardChanges() {
        let updatedCampaign = campaign
        updatedCampaign.mood_board_image_urls = moodBoardImageURLs
        Task {
            do {
                let campaignUpdateDTO = updatedCampaign.toCampaignUpdateDTO()
                let _: CampaignCreatorLib.Campaign = try await apiService.updateCampaign(updatedCampaign.id, data: campaignUpdateDTO)
            } catch {
                print("Failed to save campaign moodboard: \(error)")
            }
        }
    }

    func generateAIImage(prompt: String) async throws -> String {
        let params = CampaignCreatorLib.ImageGenerationParams(
            prompt: prompt,
            model: .openAIDalle,
            size: "1024x1024",
            quality: "standard",
            campaignId: campaign.id
        )
        let response: CampaignCreatorLib.ImageGenerationResponse = try await apiService.generateImage(payload: params)
        return response.imageUrl ?? ""
    }
}
