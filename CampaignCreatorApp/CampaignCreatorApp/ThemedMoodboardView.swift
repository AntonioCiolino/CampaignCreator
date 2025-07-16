import SwiftUI
import Kingfisher
import CampaignCreatorLib

struct ThemedMoodboardView: View {
    @Binding var imageURLs: [String]
    let onSave: () -> Void
    let onGenerateAIImage: ((String) async throws -> String)?
    let imageUploadService: ImageUploadService
    let onSetBadge: ((String) -> Void)?
    let isForBadgeSelection: Bool
    let thematicImageURL: String?

    var body: some View {
        CommonMoodBoardView(
            imageURLs: $imageURLs,
            onSave: onSave,
            onGenerateAIImage: onGenerateAIImage,
            imageUploadService: imageUploadService,
            onSetBadge: onSetBadge,
            isForBadgeSelection: isForBadgeSelection,
            thematicImageURL: thematicImageURL
        )
    }
}
