import SwiftUI
import CampaignCreatorLib

struct CampaignMoodboardView: View {
    @State var campaign: Campaign
    @ObservedObject var campaignCreator: CampaignCreator

    @State private var moodboardImageURLs: [String]

    init(campaign: Campaign, campaignCreator: CampaignCreator) {
        self._campaign = State(initialValue: campaign)
        self.campaignCreator = campaignCreator
        self._moodboardImageURLs = State(initialValue: campaign.moodBoardImageURLs ?? [])
    }

    var body: some View {
        CommonMoodboardView(
            title: "\(campaign.title) Moodboard",
            imageURLs: $moodboardImageURLs,
            onSave: { newImageURLs in
                Task {
                    await saveMoodboardChanges(newImageURLs: newImageURLs)
                }
            },
            onGenerateAIImage: { prompt in
                Task {
                    try await campaignCreator.generateImage(
                        prompt: prompt,
                        modelName: ImageModelName.defaultOpenAI.rawValue,
                        associatedCampaignId: String(campaign.id)
                    ).imageUrl
                }
            }
        )
    }

    private func saveMoodboardChanges(newImageURLs: [String]) async {
        var updatedCampaign = campaign
        updatedCampaign.moodBoardImageURLs = newImageURLs
        updatedCampaign.markAsModified()

        do {
            _ = try await campaignCreator.updateCampaign(updatedCampaign)
            // Optionally, show a success message
        } catch {
            // Optionally, show an error message
        }
    }
}
