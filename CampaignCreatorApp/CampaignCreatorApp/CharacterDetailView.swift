import SwiftUI
import CampaignCreatorLib
import Kingfisher

struct CharacterDetailView: View {
    // Use @State for the character if its properties will be updated by an Edit sheet
    // and this view needs to reflect those changes immediately without a full list refresh.
    @State var character: Character
    @ObservedObject var campaignCreator: CampaignCreator
    @EnvironmentObject var imageUploadService: ImageUploadService

    @State private var showingEditView = false
    @State private var showingFullCharacterImageSheet = false
    @State private var selectedImageURLForSheet: URL? = nil

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading) {
                        Text(character.name)
                            .font(.largeTitle)
                        // Potentially other brief info here if desired
                    }
                    Spacer()

                    // Character Image Thumbnail/Icon
                    // TODO: Implement Robust Image Caching (see also CharacterMoodboardView.swift)
                    // This AsyncImage could benefit from a shared, robust caching solution to prevent
                    // re-downloading the same image if viewed multiple times or across different app sessions.
                    if let firstImageURLString = character.imageURLs?.first, let imageURL = URL(string: firstImageURLString) {
                        Button(action: {
                            selectedImageURLForSheet = imageURL
                            showingFullCharacterImageSheet = true
                        }) {
                            // KFImage loads and caches the character's avatar (first imageURL).
                            // Displayed as a circular icon.
                            KFImage(imageURL)
                                .placeholder { // Shown during loading.
                                    ProgressView().frame(width: 50, height: 50)
                                }
                                .onFailure { error in // Log errors if image loading fails.
                                    print("KFImage failed to load character image \(imageURL.absoluteString): \(error.localizedDescription)")
                                }
                                .resizable()
                                .aspectRatio(contentMode: .fill) // Fills the circular frame.
                                .frame(width: 50, height: 50) // Sized for a small icon/avatar.
                                .clipShape(Circle()) // Makes the avatar circular.
                                .overlay(Circle().stroke(Color.secondary, lineWidth: 1))
                        }
                        .buttonStyle(.plain) // Use plain to make the image itself the button
                    } else {
                        // Default placeholder if no imageURLs are available.
                        Image(systemName: "person.crop.circle")
                            .resizable().scaledToFit().frame(width: 50, height: 50).foregroundColor(.gray)
                    }
                }
                .padding(.bottom, 5)

                // Image URLs (Links) section REMOVED as per user request

                if let description = character.description, !description.isEmpty {
                    SectionBox(title: "Description") { Text(description) }
                }

                if let appearance = character.appearanceDescription, !appearance.isEmpty {
                    SectionBox(title: "Appearance") { Text(appearance) }
                }

                if let stats = character.stats {
                    SectionBox(title: "Statistics") { StatsView(stats: stats) }
                }

                if let notes = character.notesForLLM, !notes.isEmpty {
                    SectionBox(title: "Notes for LLM") { Text(notes) }
                }

                if let exportFormat = character.exportFormatPreference, !exportFormat.isEmpty {
                     SectionBox(title: "Export Preference") { Text(exportFormat) }
                }

                // Display Custom Sections - REMOVED from Character

                // SectionBox for Metadata REMOVED
                Spacer()
            }
            .padding()
        }
        .navigationTitle(character.name)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            print("[CHAR_NOTES_DEBUG CharacterDetailView] View appeared for char ID \(character.id). Initial notesForLLM: '\(character.notesForLLM ?? "nil")', appearance: '\(character.appearanceDescription ?? "nil")'")
        }
        .refreshable {
            print("[CHAR_DETAIL_REFRESH] Refresh triggered for character ID \(character.id).")
            do {
                let refreshedCharacter = try await campaignCreator.refreshCharacter(id: character.id)
                // Update the local @State var character to reflect the refreshed data
                self.character = refreshedCharacter
                print("[CHAR_DETAIL_REFRESH] Successfully refreshed character ID \(character.id). New notes: '\(refreshedCharacter.notesForLLM ?? "nil")', new appearance: '\(refreshedCharacter.appearanceDescription ?? "nil")'")
            } catch {
                print("❌ [CHAR_DETAIL_REFRESH] Error refreshing character ID \(character.id): \(error.localizedDescription)")
                // Optionally, show an alert to the user here
            }
        }
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) { // Changed to ToolbarItemGroup
                // Navigate to Chat View
                NavigationLink(destination: CharacterChatView(campaignCreator: campaignCreator, character: character)) {
                    Image(systemName: "message.fill")
                }

                // Moodboard Button
                if let _ = character.imageURLs, !(character.imageURLs?.isEmpty ?? true) { // Ensure urls exist and are not empty
                    // The actual URLs are now passed via the character object to the moodboard
                    NavigationLink(destination: CharacterMoodboardView(campaignCreator: campaignCreator, character: character, onCharacterUpdated: { updatedCharacter in
                        // This callback is crucial for reflecting changes made in the moodboard (e.g., reordered images)
                        // back in this detail view.
                        self.character = updatedCharacter
                        print("[CharacterDetailView] Moodboard updated character ID \(updatedCharacter.id).")
                    }).environmentObject(imageUploadService)) {
                        Image(systemName: "photo.stack") // Icon for moodboard/gallery
                    }
                }

                Button("Edit") { showingEditView = true }
            }
        }
        .sheet(isPresented: $showingEditView, onDismiss: {
            // Optional: Any logic that still needs to run on dismiss,
            // but the primary character update is now handled by the callback.
            // For example, if there was a general list refresh pending, it could go here.
            // For now, we can leave it empty or remove it if the callback handles all needed updates.
            print("[CHAR_NOTES_DEBUG CharacterDetailView] Edit sheet dismissed for char ID \(character.id). Primary update via callback.")
        }) {
            CharacterEditView(character: character, campaignCreator: campaignCreator, isPresented: $showingEditView, onCharacterUpdated: { updatedCharacter in
                print("[CHAR_NOTES_DEBUG CharacterDetailView] onCharacterUpdated callback received for char ID \(updatedCharacter.id). New notesForLLM: \(updatedCharacter.notesForLLM ?? "nil"), imageURLs: \(updatedCharacter.imageURLs ?? [])")
                self.character = updatedCharacter // Update the local state directly
            })
        }
        .sheet(isPresented: $showingFullCharacterImageSheet) {
            FullCharacterImageView(imageURL: $selectedImageURLForSheet)
        }
    }
}


struct StatsView: View {
    let stats: CharacterStats
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            StatRow(label: "Strength", value: stats.strength)
            StatRow(label: "Dexterity", value: stats.dexterity)
            StatRow(label: "Constitution", value: stats.constitution)
            StatRow(label: "Intelligence", value: stats.intelligence)
            StatRow(label: "Wisdom", value: stats.wisdom)
            StatRow(label: "Charisma", value: stats.charisma)
        }
    }
}

struct StatRow: View {
    let label: String
    let value: Int?
    var body: some View {
        HStack {
            Text(label).fontWeight(.medium)
            Spacer()
            Text(value != nil ? "\(value!)" : "N/A").foregroundColor(value != nil ? .primary : .secondary)
        }
    }
}

struct CharacterDetailView_Previews: PreviewProvider {
    static var previews: some View {
        let creator = CampaignCreator()

        let sampleCharacter = Character(
            id: 1,
            name: "Aella Swiftarrow (Detail)",
            description: "A nimble scout with keen eyes and a steady hand, always ready for adventure.",
            appearanceDescription: "Slender build, often seen in practical leather armor and a deep green cloak that helps her blend into forests. Has a braid of raven hair and striking blue eyes.",
            imageURLs: nil, // Or ["http://example.com/aella.png"]
            notesForLLM: "Loves nature, wary of large cities, skilled archer.",
            stats: CharacterStats(strength: 11, dexterity: 19, constitution: 12, intelligence: 10, wisdom: 14, charisma: 13),
            exportFormatPreference: "Markdown",
            // customSections REMOVED
            createdAt: Date(timeIntervalSinceNow: -86400 * 5), // 5 days ago
            modifiedAt: Date(timeIntervalSinceNow: -86400 * 1) // 1 day ago
        )

        // Optional: If you want to test how the view behaves if the character is in the CampaignCreator's list
        // (e.g., for onDismiss logic that tries to find the character in the list to refresh it):
        // creator.characters = [sampleCharacter]
        // Note: This would require CampaignCreator.characters to be easily mutable for previews,
        // or using a mock CampaignCreator designed for previews.

        return NavigationView {
            CharacterDetailView(character: sampleCharacter, campaignCreator: creator)
        }
    }
}
