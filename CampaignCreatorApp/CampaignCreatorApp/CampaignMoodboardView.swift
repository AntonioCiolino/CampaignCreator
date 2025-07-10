import SwiftUI
import CampaignCreatorLib

struct CampaignMoodboardView: View {
    let campaign: Campaign // Pass the whole campaign to access different image URL properties

    private var allImageURLs: [String] {
        var urls: [String] = []
        if let badge = campaign.badgeImageURL, !badge.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            urls.append(badge)
        }
        if let thematic = campaign.thematicImageURL, !thematic.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            urls.append(thematic)
        }
        if let moodboardImages = campaign.moodBoardImageURLs {
            urls.append(contentsOf: moodboardImages.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty })
        }
        // Remove duplicates, preserving order of first appearance
        var uniqueURLs = [String]()
        var seen = Set<String>()
        for url in urls {
            if !seen.contains(url) {
                uniqueURLs.append(url)
                seen.insert(url)
            }
        }
        return uniqueURLs
    }

    private let gridItemLayout = [GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2)]

    @State private var selectedImageURLString: String? = nil
    // showingFullImageView will be managed by the NavigationLink or sheet presentation

    var body: some View {
        // This view will be pushed onto a navigation stack, so no NavigationView here.
        ScrollView {
            if allImageURLs.isEmpty {
                VStack {
                    Spacer()
                    Text("No images available for this campaign.")
                        .font(.headline)
                        .foregroundColor(.secondary)
                    Spacer()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                LazyVGrid(columns: gridItemLayout, spacing: 2) {
                    ForEach(allImageURLs, id: \.self) { urlString in
                        let _ = print("[CampaignMoodboardView ForEach] Processing urlString for link: \(urlString)")
                        let destinationURL = URL(string: urlString) // Convert to URL?
                        // NavigationLink to FullCharacterImageView (which is generic enough for any image URL)
                        NavigationLink(destination: FullCharacterImageViewWrapper(initialDisplayURL: destinationURL) // Pass URL?
                                        .navigationTitle("Image Detail") // More specific title
                                        .navigationBarTitleDisplayMode(.inline)
                        ) {
                            AsyncImage(url: URL(string: urlString)) { phase in // Keep URL(string:) for AsyncImage source
                                switch phase {
                                case .empty:
                                    ProgressView()
                                        .frame(maxWidth: .infinity, idealHeight: 120)
                                        .background(Color.gray.opacity(0.1))
                                case .success(let image):
                                    image.resizable()
                                        .aspectRatio(contentMode: .fill)
                                        .frame(minWidth: 0, maxWidth: .infinity)
                                        .frame(height: 120)
                                        .clipped()
                                case .failure:
                                    Image(systemName: "photo.fill")
                                        .resizable()
                                        .scaledToFit()
                                        .frame(width: 50, height: 50)
                                        .foregroundColor(.gray)
                                        .frame(maxWidth: .infinity, idealHeight: 120)
                                        .background(Color.gray.opacity(0.1))
                                @unknown default:
                                    EmptyView()
                                }
                            }
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(2)
            }
        }
        .navigationTitle("\(campaign.title) Moodboard")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct CampaignMoodboardView_Previews: PreviewProvider {
    static var previews: some View {
        let sampleCampaignWithImages = Campaign(
            id: 1,
            title: "Test Campaign",
            sections: [], // sections comes before badgeImageURL
            badgeImageURL: "https://picsum.photos/seed/badge/200/200",
            thematicImageURL: "https://picsum.photos/seed/thematic/600/400",
            moodBoardImageURLs: [
                "https://picsum.photos/seed/mb1/300/300",
                "https://picsum.photos/seed/mb2/300/300",
                "http://example.com/invalid.jpg"
            ]
            // other parameters will use their defaults
        )

        let sampleCampaignNoImages = Campaign(
            id: 2,
            title: "Empty Campaign",
            sections: []
        )

        Group {
            NavigationView {
                CampaignMoodboardView(campaign: sampleCampaignWithImages)
            }
            .previewDisplayName("With Images")

            NavigationView {
                CampaignMoodboardView(campaign: sampleCampaignNoImages)
            }
            .previewDisplayName("No Images")
        }
    }
}
