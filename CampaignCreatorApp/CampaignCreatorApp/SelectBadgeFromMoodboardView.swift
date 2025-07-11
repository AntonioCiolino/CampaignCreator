import SwiftUI
import Kingfisher

struct SelectBadgeFromMoodboardView: View {
    let moodBoardImageURLs: [String]
    let thematicImageURL: String? // Optionally include the main thematic image as a choice
    var onImageSelected: (String) -> Void // Callback with the selected URL
    @Environment(\.dismiss) var dismiss

    private var allSelectableImageURLs: [String] {
        var urls = moodBoardImageURLs
        if let thematic = thematicImageURL, !thematic.isEmpty, !urls.contains(thematic) {
            urls.insert(thematic, at: 0) // Add thematic image at the beginning if it exists and isn't already in mood board
        }
        return urls
    }

    // Grid layout
    let columns: [GridItem] = Array(repeating: .init(.flexible()), count: 3) // Adjust column count as needed

    var body: some View {
        NavigationView {
            ScrollView {
                if allSelectableImageURLs.isEmpty {
                    Text("No images available in the mood board or as a thematic image.")
                        .foregroundColor(.secondary)
                        .padding()
                } else {
                    LazyVGrid(columns: columns, spacing: 10) {
                        ForEach(allSelectableImageURLs, id: \.self) { urlString in
                            Button(action: {
                                onImageSelected(urlString)
                                dismiss()
                            }) {
                                // KFImage for asynchronous image loading and caching.
                                KFImage(URL(string: urlString))
                                    .placeholder { // Displayed while loading or if it fails.
                                        ProgressView()
                                            .frame(minWidth: 0, maxWidth: .infinity, minHeight: 100, maxHeight: 100)
                                            .background(Color.gray.opacity(0.05)) // Subtle background for placeholder
                                    }
                                    .onFailure { error in // Handle image loading failures.
                                        print("KFImage failed to load image for badge selection \(urlString): \(error.localizedDescription)")
                                        // Consider showing a more prominent error in the cell if needed.
                                    }
                                    .resizable()
                                    .aspectRatio(contentMode: .fill)
                                    .frame(minWidth: 0, maxWidth: .infinity, minHeight: 100, maxHeight: 100) // Fixed height
                                    .clipped()
                                    .cornerRadius(8)
                            }
                            .buttonStyle(.plain) // Use plain button style to make the image tappable without extra button chrome
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("Select Badge Image")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    }
}

struct SelectBadgeFromMoodboardView_Previews: PreviewProvider {
    static var previews: some View {
        SelectBadgeFromMoodboardView(
            moodBoardImageURLs: [
                "https://picsum.photos/seed/mb1/200/300",
                "https://picsum.photos/seed/mb2/300/200",
                "https://picsum.photos/seed/mb3/250/250",
                "https://picsum.photos/seed/mb4/200/200",
            ],
            thematicImageURL: "https://picsum.photos/seed/thematic/400/300",
            onImageSelected: { selectedURL in
                print("Selected URL: \(selectedURL)")
            }
        )
    }
}
