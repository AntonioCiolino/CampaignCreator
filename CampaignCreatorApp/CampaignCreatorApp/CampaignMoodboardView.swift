import SwiftUI

import CampaignCreatorLib

struct CampaignMoodboardView: View {
    @Bindable var campaign: CampaignModel
    @EnvironmentObject var imageUploadService: ImageUploadService
    var onSetBadge: ((String) -> Void)?
    @StateObject private var apiService = CampaignCreatorLib.APIService()

    var body: some View {
        SectionBox(title: "Mood Board") {
            ThemedMoodboardView(
                imageURLs: .init(get: { campaign.mood_board_image_urls ?? [] }, set: { campaign.mood_board_image_urls = $0 }),
                onSave: {
                    // No need to do anything here, as the changes are saved automatically
                },
                onGenerateAIImage: { prompt in
                    let params = CampaignCreatorLib.ImageGenerationParams(
                        prompt: prompt,
                        model: .openAIDalle,
                        size: "1024x1024",
                        quality: "standard",
                        campaignId: nil
                    )
                    let response: CampaignCreatorLib.ImageGenerationResponse = try await apiService.generateImage(payload: params)
                    return response.imageUrl ?? ""
                },
                imageUploadService: imageUploadService,
                onSetBadge: onSetBadge,
                isForBadgeSelection: true,
                thematicImageURL: campaign.thematic_image_url
            )
        }
    }
}
