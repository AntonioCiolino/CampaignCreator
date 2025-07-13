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
        var updatedCampaign = campaign
        updatedCampaign.mood_board_image_urls = moodBoardImageURLs
        Task {
            do {
                let campaignUpdate = CampaignUpdate(
                    title: updatedCampaign.title,
                    initial_user_prompt: updatedCampaign.initial_user_prompt,
                    concept: updatedCampaign.concept,
                    badge_image_url: updatedCampaign.badge_image_url,
                    thematic_image_url: updatedCampaign.thematic_image_url,
                    thematic_image_prompt: updatedCampaign.thematic_image_prompt,
                    selected_llm_id: updatedCampaign.selected_llm_id,
                    temperature: updatedCampaign.temperature,
                    theme_primary_color: updatedCampaign.theme_primary_color,
                    theme_secondary_color: updatedCampaign.theme_secondary_color,
                    theme_background_color: updatedCampaign.theme_background_color,
                    theme_text_color: updatedCampaign.theme_text_color,
                    theme_font_family: updatedCampaign.theme_font_family,
                    theme_background_image_url: updatedCampaign.theme_background_image_url,
                    theme_background_image_opacity: updatedCampaign.theme_background_image_opacity,
                    mood_board_image_urls: updatedCampaign.mood_board_image_urls
                )
                let body = try JSONEncoder().encode(campaignUpdate)
                let _: Campaign = try await apiService.performRequest(endpoint: "/campaigns/\\(campaign.id)", method: "PUT", body: body)
            } catch {
                print("Failed to save campaign moodboard: \\(error)")
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
