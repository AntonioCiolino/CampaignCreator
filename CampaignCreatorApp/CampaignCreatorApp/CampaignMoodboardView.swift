import SwiftUI
import CampaignCreatorLib

struct CampaignMoodboardView: View {
    @State var campaign: Campaign
    @ObservedObject var campaignCreator: CampaignCreator
    @EnvironmentObject var imageUploadService: ImageUploadService

    @State private var moodBoardImageURLs: [String]

    init(campaign: Campaign, campaignCreator: CampaignCreator) {
        self._campaign = State(initialValue: campaign)
        self.campaignCreator = campaignCreator
        self._moodBoardImageURLs = State(initialValue: campaign.moodBoardImageURLs ?? [])
    }

    var body: some View {
        CommonMoodBoardView(
            imageURLs: $moodBoardImageURLs,
            onSave: {
                saveMoodboardChanges()
            },
            onGenerateAIImage: { prompt in
                let response = try await campaignCreator.generateImage(
                    prompt: prompt,
                    modelName: ImageModelName.defaultOpenAI.rawValue,
                    associatedCampaignId: String(campaign.id)
                )
                return response.imageUrl ?? ""
            },
            imageUploadService: imageUploadService
        )
        .onChange(of: moodBoardImageURLs) { _ in
            saveMoodboardChanges()
        }
    }

    private func saveMoodboardChanges() {
        var updatedCampaign = campaign
        updatedCampaign.moodBoardImageURLs = moodBoardImageURLs
        Task {
            do {
                try await campaignCreator.updateCampaign(updatedCampaign)
            } catch {
                // Handle error
                print("Failed to save campaign moodboard: \(error)")
            }
        }
    }
}
