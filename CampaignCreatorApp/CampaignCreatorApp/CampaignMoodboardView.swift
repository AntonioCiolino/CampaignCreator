import SwiftUI
import SwiftData

struct CampaignMoodboardView: View {
    @Bindable var campaign: CampaignModel
    @Environment(\.modelContext) private var modelContext
    @EnvironmentObject var imageUploadService: ImageUploadService
    var onSetBadgeAction: () -> Void

    var body: some View {
        VStack {
            CommonMoodBoardView(
                imageURLs: Binding(
                    get: { campaign.mood_board_image_urls ?? [] },
                    set: { campaign.mood_board_image_urls = $0 }
                ),
                onSave: {
                    try? modelContext.save()
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
