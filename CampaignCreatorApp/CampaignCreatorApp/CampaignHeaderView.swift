import SwiftUI
// import PhotosUI // No longer needed as PhotosPicker is removed
import CampaignCreatorLib // Assuming Campaign model is here
import Kingfisher

struct CampaignHeaderView: View {
    // Properties passed from parent
    let campaign: Campaign
    @Binding var editableTitle: String
    let isSaving: Bool
    let isGeneratingText: Bool
    let currentPrimaryColor: Color

    // Callback for the placeholder button
    let onSetBadgeAction: () -> Void
    // Note: The .onChange for editableTitle and debouncing logic
    // will remain in CampaignDetailView as it owns the editableTitle @State
    // and the titleDebounceTimer.

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading) {
                    Text("\(campaign.wordCount) words (from sections)")
                        .font(.caption).foregroundColor(.secondary)
                    // Removed "Modified At" Text View
                }
                Spacer()
            }

            TextField("Campaign Title", text: $editableTitle)
                .font(.largeTitle)
                .textFieldStyle(PlainTextFieldStyle())
                .padding(.bottom, 4)
                .disabled(isSaving || isGeneratingText)

            // Campaign Badge Display
            if let badgeUrlString = campaign.badgeImageURL, let badgeUrl = URL(string: badgeUrlString) {
                // KFImage loads and caches the campaign badge.
                // Displayed as a circular icon.
                KFImage(badgeUrl)
                    .placeholder { // Shown during loading.
                        ProgressView().frame(width: 50, height: 50).padding(.top, 5)
                    }
                    .onFailure { error in // Log errors if image loading fails.
                        print("KFImage failed to load campaign badge \(badgeUrlString): \(error.localizedDescription)")
                    }
                    .resizable()
                    .aspectRatio(contentMode: .fit) // Ensures the entire image fits within the frame.
                    .frame(maxWidth: 50, maxHeight: 50) // Sized for a small icon badge.
                    .clipShape(Circle()) // Makes the badge circular.
                    .overlay(Circle().stroke(currentPrimaryColor, lineWidth: 2)) // Adds a themed border.
                    .padding(.top, 5)
                    .id(campaign.badgeImageURL) // Ensures view redraws if the URL string changes.
            } else {
                // Default placeholder if no badgeImageURL is set.
                Image(systemName: "shield.lefthalf.filled.slash")
                    .font(.largeTitle)
                    .foregroundColor(.secondary)
                    .frame(width: 50, height: 50)
                    .padding(.top, 5)
            }
            Button(action: {
                onSetBadgeAction() // This action is passed from CampaignDetailView
            }) {
                Text("Set Campaign Badge")
            }
            .buttonStyle(.bordered)
            .font(.caption)
            .padding(.top, 2)

        }
        .padding().background(Color(.systemGroupedBackground)).cornerRadius(12)
    }
}
