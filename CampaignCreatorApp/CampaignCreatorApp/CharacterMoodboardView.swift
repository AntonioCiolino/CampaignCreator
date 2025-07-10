import SwiftUI

// Helper struct for .sheet(item: ...)
struct IdentifiableURLContainer: Identifiable {
    let id = UUID()
    let url: URL
}

struct CharacterMoodboardView: View {
    let imageURLs: [String]
    let characterName: String

    private let gridItemLayout = [GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2)]
    @State private var sheetItemForImageView: IdentifiableURLContainer? = nil

    // Private helper view for each cell in the moodboard grid
    private struct MoodboardCellView: View {
        let urlString: String
        let action: () -> Void // Action to perform on tap

        var body: some View {
            Button(action: action) {
                AsyncImage(url: URL(string: urlString)) { phase in
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
                            .contentShape(Rectangle())
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

    var body: some View {
        ScrollView {
            if imageURLs.isEmpty {
                VStack {
                    Spacer()
                    Text("No images available for this character.")
                        .font(.headline)
                        .foregroundColor(.secondary)
                    Spacer()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                LazyVGrid(columns: gridItemLayout, spacing: 2) {
                    ForEach(imageURLs, id: \.self) { urlString in
                        MoodboardCellView(urlString: urlString, action: {
                            // print("[CharacterMoodboardView] Tapped image. Original urlString: \(urlString)")
                            if let url = URL(string: urlString) {
                                self.sheetItemForImageView = IdentifiableURLContainer(url: url)
                                // print("[CharacterMoodboardView] Set sheetItemForImageView with URL: \(url.absoluteString)")
                            } else {
                                self.sheetItemForImageView = nil
                                // print("[CharacterMoodboardView] Failed to create URL from string, sheetItemForImageView set to nil.")
                            }
                        })
                    }
                }
                .padding(2)
            }
        }
        .navigationTitle("\(characterName) Moodboard")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(item: $sheetItemForImageView, onDismiss: {
            // print("[CharacterMoodboardView .sheet(item:)] Sheet dismissed. sheetItemForImageView automatically set to nil.")
        }) { itemWrapper in // itemWrapper is IdentifiableURLContainer
            // let _ = print("[CharacterMoodboardView .sheet(item:)] Content closure. URL: \(itemWrapper.url.absoluteString)")
            FullCharacterImageViewWrapper(initialDisplayURL: itemWrapper.url)
        }
    }
}

struct FullCharacterImageViewWrapper: View {
    let initialDisplayURL: URL?
    @State private var imageURLForSheet: URL?

    init(initialDisplayURL: URL?) {
        self.initialDisplayURL = initialDisplayURL
        // print("[Wrapper init] Received initialDisplayURL: \(initialDisplayURL?.absoluteString ?? "nil")")
        self._imageURLForSheet = State(initialValue: initialDisplayURL)
        // print("[Wrapper init] Initialized imageURLForSheet with: \(self._imageURLForSheet.wrappedValue?.absoluteString ?? "nil")")
    }

    var body: some View {
        // let _ = print("[Wrapper body] Current imageURLForSheet for FullCharacterImageView: \(imageURLForSheet?.absoluteString ?? "nil")")
        FullCharacterImageView(imageURL: $imageURLForSheet) // FullCharacterImageView is defined in CharacterDetailView.swift
    }
}

struct CharacterMoodboardView_Previews: PreviewProvider {
    static var previews: some View {
        let sampleURLs = [
            "https://picsum.photos/seed/chara_mb1/200/300",
            "https://picsum.photos/seed/chara_mb2/300/200",
            "https://picsum.photos/seed/chara_mb3/250/250",
        ]
        let emptyURLs: [String] = []

        Group {
            NavigationView {
                 CharacterMoodboardView(imageURLs: sampleURLs, characterName: "Hero With Images")
            }
            .previewDisplayName("With Images")

            NavigationView {
                CharacterMoodboardView(imageURLs: emptyURLs, characterName: "Hero No Images")
            }
            .previewDisplayName("No Images")
        }
    }
}
