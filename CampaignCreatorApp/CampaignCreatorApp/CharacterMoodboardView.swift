import SwiftUI

struct CharacterMoodboardView: View {
    let imageURLs: [String]
    let characterName: String // Optional: for a more descriptive title

    // Define the grid layout: 3 columns, flexible size
    private let gridItemLayout = [GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2)]

    // @State private var selectedImageURLString: String? = nil // Replaced
    @State private var sheetTargetURL: URL? = nil // New state variable
    @State private var showingFullImageView = false

    var body: some View {
        NavigationView {
            ScrollView {
                if imageURLs.isEmpty {
                    VStack {
                        Spacer()
                        Text("No images available for this character.")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity) // Ensure it takes space to center
                } else {
                    LazyVGrid(columns: gridItemLayout, spacing: 2) {
                        ForEach(imageURLs, id: \.self) { urlString in
                            Button(action: {
                                print("[CharacterMoodboardView] Tapped image. Original urlString: \(urlString)")
                                if let url = URL(string: urlString) {
                                    self.sheetItemForImageView = IdentifiableURLContainer(url: url)
                                    print("[CharacterMoodboardView] Set sheetItemForImageView with URL: \(url.absoluteString)")
                                } else {
                                    self.sheetItemForImageView = nil // Ensure it's nil if URL is bad
                                    print("[CharacterMoodboardView] Failed to create URL from string, sheetItemForImageView set to nil.")
                                }
                            }) {
                                AsyncImage(url: URL(string: urlString)) { phase in
                                    switch phase {
                                    case .empty:
                                        ProgressView()
                                            .frame(maxWidth: .infinity, idealHeight: 120) // Give it some size
                                            .background(Color.gray.opacity(0.1))
                                    case .success(let image):
                                        image.resizable()
                                            .aspectRatio(contentMode: .fill) // Fill the frame
                                            .frame(minWidth: 0, maxWidth: .infinity) // Expand to column width
                                            .frame(height: 120) // Fixed height for uniformity
                                            .clipped() // Clip excess
                                            .contentShape(Rectangle()) // Ensure tappable area covers the image
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
                            .buttonStyle(.plain) // Use plain button style for image-only tap
                        }
                    }
                    .padding(2) // Add a little padding around the grid
                }
            }
            .navigationTitle("\(characterName) Moodboard")
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $showingFullImageView, onDismiss: { self.sheetTargetURL = nil }) {
                let _ = print("[CharacterMoodboardView .sheet] Content closure. sheetTargetURL: \(sheetTargetURL?.absoluteString ?? "nil")")
                if let concreteURL = sheetTargetURL {
                    FullCharacterImageViewWrapper(initialDisplayURL: concreteURL)
                } else {
                    Text("Error: URL for sheet was nil or invalid.")
                    let _ = print("[CharacterMoodboardView .sheet] Error: sheetTargetURL is nil.")
                }
            }
        }
        // If this view is meant to be pushed onto an existing NavigationView stack,
        // then the NavigationView here might be redundant or cause nested NavViews.
        // Assuming it's presented modally or as a top-level pushed view for now.
        // If pushed, the parent view's NavigationView would handle the title.
        // Let's remove the NavigationView here and assume it's pushed.
        // The navigationTitle will be handled by the pushing NavigationView.
    }
}

// Wrapper to manage the @State URL for the sheet, as sheet items need stable identity.
struct FullCharacterImageViewWrapper: View {
    let initialDisplayURL: URL? // Changed from urlString
    @State private var imageURLForSheet: URL?

    init(initialDisplayURL: URL?) { // Changed parameter name and type
        self.initialDisplayURL = initialDisplayURL
        print("[Wrapper init] Received initialDisplayURL: \(initialDisplayURL?.absoluteString ?? "nil")")
        // Directly use the passed URL for the state's initial value
        self._imageURLForSheet = State(initialValue: initialDisplayURL)
        print("[Wrapper init] Initialized imageURLForSheet with: \(self._imageURLForSheet.wrappedValue?.absoluteString ?? "nil")")
    }

    var body: some View {
        let _ = print("[Wrapper body] Current imageURLForSheet for FullCharacterImageView: \(imageURLForSheet?.absoluteString ?? "nil")")
        // This view now directly presents FullCharacterImageView,
        // which has its own NavigationView for its toolbar.
        FullCharacterImageView(imageURL: $imageURLForSheet)
    }
}


struct CharacterMoodboardView_Previews: PreviewProvider {
    static var previews: some View {
        // Sample URLs for preview
        let sampleURLs = [
            "https://picsum.photos/seed/picsum1/200/300",
            "https://picsum.photos/seed/picsum2/300/200",
            "https://picsum.photos/seed/picsum3/250/250",
            "http://example.com/invalid-url.jpg", // Invalid URL example
            "https://picsum.photos/seed/picsum4/200/220",
            "https://picsum.photos/seed/picsum5/220/200",
        ]
        let emptyURLs: [String] = []

        Group {
            NavigationView { // Add NavigationView for preview context
                 CharacterMoodboardView(imageURLs: sampleURLs, characterName: "Sample Hero")
            }
            .previewDisplayName("With Images")

            NavigationView {
                CharacterMoodboardView(imageURLs: emptyURLs, characterName: "No Images Hero")
            }
            .previewDisplayName("No Images")
        }
    }
}
