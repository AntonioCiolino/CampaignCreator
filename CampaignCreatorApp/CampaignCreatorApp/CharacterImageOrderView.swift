import SwiftUI
import CampaignCreatorLib

private struct IdentifiableURLString: Identifiable {
    let id = UUID()
    var urlString: String
}

struct CharacterImageOrderView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    @State var character: Character // Passed in to get initial order and ID

    @State private var identifiableOrderedImageURLs: [IdentifiableURLString]
    private var originalImageURLs: [String] // To compare for hasChanges

    var onDismiss: (Bool) -> Void // Callback: true if saved, false if cancelled

    @Environment(\.dismiss) private var dismissEnvironment
    @Environment(\.editMode) private var editMode // Added to manage list edit state
    @State private var isSaving: Bool = false
    @State private var showErrorAlert: Bool = false
    @State private var errorMessage: String = ""

    private var isEditing: Bool { // Helper
        editMode?.wrappedValue.isEditing ?? false
    }

    private var hasChanges: Bool {
        let currentOrder = identifiableOrderedImageURLs.map { $0.urlString }
        return currentOrder != originalImageURLs
    }

    init(campaignCreator: CampaignCreator, character: Character, onDismiss: @escaping (Bool) -> Void) {
        self.campaignCreator = campaignCreator
        self._character = State(initialValue: character) // Store the character
        let initialURLs = character.imageURLs ?? []
        self.originalImageURLs = initialURLs
        self._identifiableOrderedImageURLs = State(initialValue: initialURLs.map { IdentifiableURLString(urlString: $0) })
        self.onDismiss = onDismiss
    }

    var body: some View {
        NavigationView {
            VStack {
                if identifiableOrderedImageURLs.isEmpty {
                    Text("No images to reorder.")
                        .foregroundColor(.secondary)
                        .padding()
                    Spacer()
                } else {
                    List {
                        ForEach(identifiableOrderedImageURLs) { identifiableURL in
                            HStack {
                                AsyncImage(url: URL(string: identifiableURL.urlString)) { phase in
                                    switch phase {
                                    case .empty:
                                        ProgressView().frame(width: 40, height: 40)
                                    case .success(let image):
                                        image.resizable().aspectRatio(contentMode: .fill)
                                            .frame(width: 40, height: 40).clipped()
                                    case .failure:
                                        Image(systemName: "photo.fill")
                                            .frame(width: 40, height: 40).foregroundColor(.gray)
                                    @unknown default:
                                        EmptyView().frame(width: 40, height: 40)
                                    }
                                }
                                .background(Color.gray.opacity(0.1)) // Background for the frame

                                Text(identifiableURL.urlString)
                                    .font(.caption)
                                    .lineLimit(1)
                                    .truncationMode(.middle)
                            }
                        }
                        .onMove(perform: moveImage)
                    }
                }
            }
            .navigationTitle("Reorder Images")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    if isEditing {
                        Button("Cancel") {
                            // Revert changes and exit edit mode
                            identifiableOrderedImageURLs = originalImageURLs.map { IdentifiableURLString(urlString: $0) }
                            editMode?.wrappedValue = .inactive
                            // Don't dismiss the sheet, let user tap "Close" or "Done" (from EditButton)
                        }
                        .disabled(isSaving)
                    } else {
                        Button("Close") { // Changed from "Cancel" when not editing
                            onDismiss(false) // Indicate no save occurred
                            dismissEnvironment()
                        }
                        .disabled(isSaving)
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    if isEditing {
                        if isSaving {
                            ProgressView()
                        } else {
                            Button("Done") { // Changed from "Save" - action now tied to exiting edit mode
                                if hasChanges {
                                    Task { await saveOrder() }
                                } else {
                                    editMode?.wrappedValue = .inactive
                                    // Optional: could also dismiss here if no changes and Done is tapped
                                    // onDismiss(false)
                                    // dismissEnvironment()
                                }
                            }
                            // Save button (now "Done") is implicitly enabled/disabled by hasChanges logic within its action
                            // Or, keep it always enabled and check hasChanges inside.
                            // For clarity, disable if saving.
                            .disabled(isSaving)
                        }
                    } else {
                        // Show EditButton only if there are images to reorder
                        if !identifiableOrderedImageURLs.isEmpty {
                            EditButton().disabled(isSaving)
                        }
                    }
                }
            }
            .alert("Error Saving Order", isPresented: $showErrorAlert) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        }
    }

    private func moveImage(from source: IndexSet, to destination: Int) {
        identifiableOrderedImageURLs.move(fromOffsets: source, toOffset: destination)
    }

    private func saveOrder() async {
        guard hasChanges else {
            onDismiss(false) // No changes, but signal dismissal perhaps as 'not saved'
            dismissEnvironment()
            return
        }

        isSaving = true
        var tempCharacter = character // Use the @State character passed in
        let finalOrderedURLs = identifiableOrderedImageURLs.map { $0.urlString }
        tempCharacter.imageURLs = finalOrderedURLs.isEmpty ? nil : finalOrderedURLs
        tempCharacter.markAsModified()

        do {
            _ = try await campaignCreator.updateCharacter(tempCharacter) // The updated character is returned
            editMode?.wrappedValue = .inactive // Exit edit mode
            onDismiss(true) // Signal that save was successful
            dismissEnvironment()
        } catch let error as APIError {
            errorMessage = "API Error: \(error.localizedDescription)"
            showErrorAlert = true
        } catch {
            errorMessage = "An unexpected error occurred: \(error.localizedDescription)"
            showErrorAlert = true
        }
        isSaving = false
    }
}

struct CharacterImageOrderView_Previews: PreviewProvider {
    static var previews: some View {
        let campaignCreator = CampaignCreator()
        let sampleURLs1 = [
            "https://picsum.photos/seed/order_img1/200/300",
            "https://picsum.photos/seed/order_img2/300/200",
            "https://picsum.photos/seed/order_img3/250/250",
        ]
        let charWithImages = Character(id: 1, name: "Reorder Hero", imageURLs: sampleURLs1)
        let charNoImages = Character(id: 2, name: "No Images Hero", imageURLs: [])

        // Preview for view with images
        CharacterImageOrderView(
            campaignCreator: campaignCreator,
            character: charWithImages,
            onDismiss: { saved in
                print("Preview dismiss: Images saved - \(saved)")
            }
        )
        .previewDisplayName("With Images")

        // Preview for view with no images
        CharacterImageOrderView(
            campaignCreator: campaignCreator,
            character: charNoImages,
            onDismiss: { saved in
                print("Preview dismiss: Images saved - \(saved)")
            }
        )
        .previewDisplayName("No Images")
    }
}
