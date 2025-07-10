import SwiftUI

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

    private let gridItemLayout = [GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2), GridItem(.flexible(), spacing: 2)]
    @State private var sheetItemForImageView: IdentifiableURLContainer? = nil
    @Environment(\.editMode) private var editMode
    @Environment(\.dismiss) private var dismiss

    // Callback to inform the presenter that the character was updated
    var onCharacterUpdated: ((Character) -> Void)?

    @State private var isSaving: Bool = false
    @State private var showErrorAlert: Bool = false
    @State private var errorMessage: String = ""

    private var hasChanges: Bool {
        character.imageURLs ?? [] != localImageURLs
    }

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
                        })
                    }
                    .onMove(perform: moveImage) // Added .onMove
                }
                .padding(2)
            }
        }
        .navigationTitle("\(character.name) Moodboard") // Use character name
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                if editMode?.wrappedValue.isEditing ?? false {
                    Button("Cancel") {
                        // Revert changes and exit edit mode
                        localImageURLs = character.imageURLs ?? []
                        identifiableImageURLs = localImageURLs.map { IdentifiableString(value: $0) }
                        editMode?.wrappedValue = .inactive
                    }
                    .disabled(isSaving)
                } else {
                    Button("Close") { // Changed from "Done" to "Close" for clarity when not editing
                        dismiss()
                    }
                }
            }
            ToolbarItem(placement: .navigationBarTrailing) {
                if editMode?.wrappedValue.isEditing ?? false {
                    Button("Save") {
                        Task { await saveChanges() }
                    }
                    .disabled(!hasChanges || isSaving)
                } else {
                    EditButton().disabled(isSaving)
                }
            }
        }
        .sheet(item: $sheetItemForImageView) { itemWrapper in
            FullCharacterImageViewWrapper(initialDisplayURL: itemWrapper.url)
        }
        .alert("Error Saving Changes", isPresented: $showErrorAlert) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        // No specific onChange needed here now as moveImage directly updates localImageURLs
    }

    private func moveImage(from source: IndexSet, to destination: Int) {
        identifiableImageURLs.move(fromOffsets: source, toOffset: destination)
        localImageURLs = identifiableImageURLs.map { $0.value }
    }

    private func saveChanges() async {
        guard hasChanges else {
            editMode?.wrappedValue = .inactive // Exit edit mode if no changes
            return
        }

        isSaving = true
        var updatedCharacter = character
        updatedCharacter.imageURLs = localImageURLs.isEmpty ? nil : localImageURLs
        updatedCharacter.markAsModified()

        do {
            let savedCharacter = try await campaignCreator.updateCharacter(updatedCharacter)
            // Update the @State character to reflect the saved changes (including new modifiedAt)
            self.character = savedCharacter
            // Update localImageURLs to match the saved state, in case nil was set for empty array
            self.localImageURLs = savedCharacter.imageURLs ?? []
            self.identifiableImageURLs = self.localImageURLs.map { IdentifiableString(value: $0) }

            onCharacterUpdated?(savedCharacter) // Call the callback
            isSaving = false
            editMode?.wrappedValue = .inactive // Exit edit mode
            // Optionally dismiss if save is successful and that's the desired UX
            // dismiss()
        } catch let error as APIError {
            errorMessage = "API Error: \(error.localizedDescription)"
            showErrorAlert = true
            isSaving = false
        } catch {
            errorMessage = "An unexpected error occurred: \(error.localizedDescription)"
            showErrorAlert = true
            isSaving = false
        }
    }
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
