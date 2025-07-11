import SwiftUI

// TODO: Implement Robust Image Caching
// Consider implementing a more robust image caching mechanism (e.g., using NSCache for in-memory caching
// and potentially a disk cache) to improve performance and reduce repeated downloads.
// This could involve creating a custom ImageLoader class or service that AsyncImage
// (or a replacement custom view) can use. This would benefit both the moodboard and character thumbnail.

// Helper struct for .sheet(item: ...)
struct IdentifiableURLContainer: Identifiable {
    let id = UUID() // Stable ID for the sheet item
    let url: URL
}

// To make String identifiable for ForEach with .onMove, if they are not unique
struct IdentifiableString: Identifiable {
    let id = UUID()
    let value: String
}

import CampaignCreatorLib // Required for Character and CampaignCreator

struct CharacterMoodboardView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    @State var character: Character // Pass the full character

    @State private var localImageURLs: [String] // Local copy for reordering
    @State private var identifiableImageURLs: [IdentifiableString] // For UI with .onMove
    // @State private var isManualEditing: Bool = false // REVERTED

    private let gridItemLayout = [GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2)]
    @State private var sheetItemForImageView: IdentifiableURLContainer? = nil
    @Environment(\.editMode) private var editMode // RESTORED
    @Environment(\.dismiss) private var dismiss

    // Callback to inform the presenter that the character was updated
    var onCharacterUpdated: ((Character) -> Void)?

    @State private var isSaving: Bool = false
    @State private var showErrorAlert: Bool = false
    @State private var errorMessage: String = ""
    @State private var showingReorderView: Bool = false // State to present CharacterImageOrderView

    // hasChanges, saveChanges, moveImage, EditButton, and .onMove are no longer needed here
    // as reordering is delegated to CharacterImageOrderView.

    init(campaignCreator: CampaignCreator, character: Character, onCharacterUpdated: ((Character) -> Void)? = nil) {
        self.campaignCreator = campaignCreator
        self._character = State(initialValue: character)
        let initialURLs = character.imageURLs ?? []
        self._localImageURLs = State(initialValue: initialURLs)
        self._identifiableImageURLs = State(initialValue: initialURLs.map { IdentifiableString(value: $0) })
        self.onCharacterUpdated = onCharacterUpdated
    }

    // Private helper view for each cell in the moodboard grid
    private struct MoodboardCellView: View {
        let urlString: String
        let action: () -> Void // Action to perform on tap
        @Environment(\.editMode) private var editMode // RESTORED for cell's own logic if needed

        private var isEditing: Bool { // Uses environment editMode
            editMode?.wrappedValue.isEditing ?? false
        }

        @ViewBuilder
        private var cellContent: some View {
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

        var body: some View {
            if isEditing {
                cellContent
                    .frame(maxWidth: .infinity, idealHeight: 120) // Ensure a consistent frame for drag
                    .contentShape(Rectangle()) // Make the whole area draggable
            } else {
                Button(action: action) {
                    cellContent
                }
                .buttonStyle(.plain)
            }
        }
    }

    // private var isEditing: Bool { // Helper computed property for readability - REMOVED, will use explicit @State
    //     editMode?.wrappedValue.isEditing ?? false
    // }

    var body: some View {
        ScrollView { // Reverted to default ScrollView initialization
            if identifiableImageURLs.isEmpty {
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
                    // Use identifiableImageURLs for ForEach to support .onMove
                    ForEach(identifiableImageURLs) { identifiableURL in
                        MoodboardCellView(urlString: identifiableURL.value, action: {
                            if let url = URL(string: identifiableURL.value) {
                                self.sheetItemForImageView = IdentifiableURLContainer(url: url)
                            } else {
                                self.sheetItemForImageView = nil
                            }
                        }) // Cell no longer needs isEditing, it uses @Environment(\.editMode)
                    }
                    // .onMove is REMOVED - reordering handled by CharacterImageOrderView
                }
                .padding(2)
            }
        }
        .navigationTitle("\(character.name) Moodboard")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button("Close") {
                    dismiss()
                }
            }
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    showingReorderView = true
                } label: {
                    Label("Reorder Images", systemImage: "arrow.up.arrow.down.circle")
                }
                .disabled(identifiableImageURLs.isEmpty) // Disable if no images
            }
        }
        .sheet(isPresented: $showingReorderView) {
            CharacterImageOrderView(
                campaignCreator: campaignCreator,
                character: character, // Pass the current character state
                onDismiss: { changesMade in
                    showingReorderView = false // Dismiss the sheet
                    if changesMade {
                        // Re-fetch or update character to reflect new order
                        // The CharacterImageOrderView handles saving, so we need to refresh the character state here
                        // to get the updated imageURLs order.
                        Task {
                            do {
                                // Refresh the character from the source of truth
                                let refreshedCharacter = try await campaignCreator.refreshCharacter(id: character.id)
                                self.character = refreshedCharacter // Update local @State

                                // Update local URL arrays to reflect changes for the grid display
                                let updatedURLs = refreshedCharacter.imageURLs ?? []
                                self.localImageURLs = updatedURLs
                                self.identifiableImageURLs = updatedURLs.map { IdentifiableString(value: $0) }

                                // Propagate the updated character to the parent view (e.g., CharacterDetailView)
                                onCharacterUpdated?(refreshedCharacter)
                                print("[CharacterMoodboardView] Image order updated and character refreshed.")
                            } catch {
                                print("❌ Error refreshing character after image reorder: \(error.localizedDescription)")
                                // Optionally show an alert to the user
                                self.errorMessage = "Failed to refresh character after reordering images: \(error.localizedDescription)"
                                self.showErrorAlert = true
                            }
                        }
                    }
                }
            )
        }
        .sheet(item: $sheetItemForImageView) { itemWrapper in // For viewing single image
            FullCharacterImageViewWrapper(initialDisplayURL: itemWrapper.url)
        }
        .alert("Moodboard Error", isPresented: $showErrorAlert) { // Generic error alert
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
    }
    // moveImage and saveChanges methods are REMOVED as they are no longer used here.
    // EditButton and related @Environment(\.editMode) direct usage for reordering is removed.
}

struct FullCharacterImageViewWrapper: View {
    let initialDisplayURL: URL?
    @State private var imageURLForSheet: URL?

    init(initialDisplayURL: URL?) {
        self.initialDisplayURL = initialDisplayURL
        self._imageURLForSheet = State(initialValue: initialDisplayURL)
    }

    var body: some View {
        FullCharacterImageView(imageURL: $imageURLForSheet) // FullCharacterImageView is defined in CharacterDetailView.swift
    }
}

struct CharacterMoodboardView_Previews: PreviewProvider {
    static var previews: some View {
        // Sample data for preview
        let sampleImageURLs = [
            "https://picsum.photos/seed/chara_mb_preview1/200/300",
            "https://picsum.photos/seed/chara_mb_preview2/300/200",
            "https://picsum.photos/seed/chara_mb_preview3/250/250",
        ]

        let sampleCharacterWithImages = Character(
            id: 101, // Using a distinct ID for preview character
            name: "Preview Hero With Images",
            imageURLs: sampleImageURLs,
            createdAt: Date(),
            modifiedAt: Date()
        )

        let sampleCharacterNoImages = Character(
            id: 102,
            name: "Preview Hero No Images",
            imageURLs: [], // Empty array
            createdAt: Date(),
            modifiedAt: Date()
        )

        let sampleCharacterNilImages = Character(
            id: 103,
            name: "Preview Hero Nil Images",
            imageURLs: nil, // Explicitly nil
            createdAt: Date(),
            modifiedAt: Date()
        )

        // Dummy CampaignCreator for preview
        let previewCampaignCreator = CampaignCreator()

        Group {
            NavigationView {
                CharacterMoodboardView(
                    campaignCreator: previewCampaignCreator,
                    character: sampleCharacterWithImages,
                    onCharacterUpdated: { updatedChar in
                        print("Preview: Character updated - \(updatedChar.name)")
                    }
                )
            }
            .previewDisplayName("With Images (Active Edit)")
            .environment(\.editMode, .constant(.active)) // Start in active edit mode for easy testing

            NavigationView {
                CharacterMoodboardView(
                    campaignCreator: previewCampaignCreator,
                    character: sampleCharacterWithImages,
                    onCharacterUpdated: { updatedChar in
                        print("Preview: Character updated - \(updatedChar.name)")
                    }
                )
            }
            .previewDisplayName("With Images (Inactive Edit)")
            // .environment(\.editMode, .constant(.inactive)) // Default, not strictly needed to set

            NavigationView {
                CharacterMoodboardView(
                    campaignCreator: previewCampaignCreator,
                    character: sampleCharacterNoImages,
                    onCharacterUpdated: { updatedChar in
                        print("Preview: Character updated - \(updatedChar.name)")
                    }
                )
            }
            .previewDisplayName("No Images (Empty Array)")

            NavigationView {
                CharacterMoodboardView(
                    campaignCreator: previewCampaignCreator,
                    character: sampleCharacterNilImages,
                    onCharacterUpdated: { updatedChar in
                        print("Preview: Character updated - \(updatedChar.name)")
                    }
                )
            }
            .previewDisplayName("No Images (Nil Array)")
        }
    }
}
