import SwiftUI
import CampaignCreatorLib // Assuming Campaign model is here

struct CampaignHeaderView: View {
    // Properties passed from parent
    let campaign: Campaign
    @Binding var editableTitle: String
    let isSaving: Bool
    let isGeneratingText: Bool
    let currentPrimaryColor: Color

    // Callback for the placeholder button
    let onSetBadgeAction: () -> Void
    @State private var showingImagePicker = false
    @Binding var selectedBadgeImage: PhotosPickerItem?
    // Note: The .onChange for editableTitle and debouncing logic
    // will remain in CampaignDetailView as it owns the editableTitle @State
    // and the titleDebounceTimer.

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading) {
                    Text("\(campaign.wordCount) words (from sections)")
                        .font(.caption).foregroundColor(.secondary)
                    Text(campaign.modifiedAt != nil ? "Modified: \(campaign.modifiedAt!, style: .date)" : "Modified: N/A")
                        .font(.caption).foregroundColor(.secondary)
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
                AsyncImage(url: badgeUrl) { phase in
                    switch phase {
                    case .success(let image):
                        image.resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(maxWidth: 100, maxHeight: 100)
                            .clipShape(Circle())
                            .overlay(Circle().stroke(currentPrimaryColor, lineWidth: 2))
                            .padding(.top, 5)
                    case .failure:
                        Image(systemName: "photo.circle")
                            .resizable().scaledToFit().frame(width: 50, height: 50)
                            .padding(.top, 5)
                    case .empty:
                        ProgressView().frame(width: 50, height: 50).padding(.top, 5)
                    @unknown default:
                        EmptyView()
                    }
                }
            } else {
                Image(systemName: "shield.lefthalf.filled.slash")
                    .font(.largeTitle)
                    .foregroundColor(.secondary)
                    .frame(width: 50, height: 50)
                    .padding(.top, 5)
            }
            PhotosPicker(
                selection: $selectedBadgeImage,
                matching: .images,
                photoLibrary: .shared()
            ) {
                Text("Set Campaign Badge")
            }
            .buttonStyle(.bordered)
            .font(.caption)
            .padding(.top, 2)
            // The onSetBadgeAction callback might be triggered via .onChange of selectedBadgeImage in the parent view (CampaignDetailView)

        }
        .padding().background(Color(.systemGroupedBackground)).cornerRadius(12)
    }
}
