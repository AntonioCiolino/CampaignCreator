import SwiftUI

struct CampaignMoodboardView: View {
    @Bindable var campaign: CampaignModel
    @EnvironmentObject var imageUploadService: ImageUploadService
    var onSetBadge: ((String) -> Void)?

    var body: some View {
        SectionBox(title: "Mood Board") {
            CommonMoodBoardView(
                imageURLs: .init(get: { campaign.mood_board_image_urls ?? [] }, set: { campaign.mood_board_image_urls = $0 }),
                onSave: {
                    // No need to do anything here, as the changes are saved automatically
                },
                onGenerateAIImage: { prompt in
                    // This will be handled by the CommonMoodBoardView
                    return ""
                },
                imageUploadService: imageUploadService,
                onSetBadge: onSetBadge,
                isForBadgeSelection: true,
                thematicImageURL: campaign.thematic_image_url
            )
        }
    }
}
