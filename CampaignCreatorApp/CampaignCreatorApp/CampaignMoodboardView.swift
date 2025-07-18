import SwiftUI

struct CampaignMoodboardView: View {
    @Bindable var campaign: CampaignModel
    @EnvironmentObject var imageUploadService: ImageUploadService
    var onSetBadgeAction: () -> Void

    var body: some View {
        VStack {
            CommonMoodBoardView(
                imageURLs: .init(get: { campaign.mood_board_image_urls ?? [] }, set: { campaign.mood_board_image_urls = $0 }),
                onSave: {
                    // No need to do anything here, as the changes are saved automatically
                },
                onGenerateAIImage: { prompt in
                    // This will be handled by the CommonMoodBoardView
                    return ""
                },
                imageUploadService: imageUploadService
            )
            Button(action: {
                onSetBadgeAction()
            }) {
                Text("Set Campaign Badge from Moodboard")
            }
            .buttonStyle(.bordered)
            .padding(.top, 10)
        }
    }
}
