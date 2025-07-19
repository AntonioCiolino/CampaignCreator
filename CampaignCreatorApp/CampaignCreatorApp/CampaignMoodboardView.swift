import SwiftUI

struct CampaignMoodboardView: View {
    @Bindable var campaign: CampaignModel
    @EnvironmentObject var imageUploadService: ImageUploadService
    var onSetBadgeAction: () -> Void

    var body: some View {
        VStack {
            CommonMoodBoardView(
                imageURLs: .init(get: { campaign.mood_board_image_urls ?? [] }, set: { campaign.mood_board_image_urls = $0 }),
                name: campaign.title,
                onSave: {
                    // No need to do anything here, as the changes are saved automatically
                },
                onGenerateAIImage: nil,
                imageUploadService: imageUploadService,
                onSetBadge: { urlString in
                    campaign.badge_image_url = urlString
                }
            )
        }
    }
}
