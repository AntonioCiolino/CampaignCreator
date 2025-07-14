import SwiftUI

struct CampaignMoodboardView: View {
    @StateObject private var viewModel: CampaignMoodboardViewModel
    @EnvironmentObject var imageUploadService: ImageUploadService

    init(campaign: Campaign) {
        _viewModel = StateObject(wrappedValue: CampaignMoodboardViewModel(campaign: campaign))
    }

    var body: some View {
        CommonMoodBoardView(
            imageURLs: $viewModel.moodBoardImageURLs,
            onSave: {
                viewModel.saveMoodboardChanges()
            },
            onGenerateAIImage: { prompt in
                return try await viewModel.generateAIImage(prompt: prompt)
            },
            imageUploadService: imageUploadService
        )
        .onChange(of: viewModel.moodBoardImageURLs) {
            viewModel.saveMoodboardChanges()
        }
    }
}
