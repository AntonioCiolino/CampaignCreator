import SwiftUI
import CampaignCreatorLib

struct CharacterDetailView: View {
    // Use @State for the character if its properties will be updated by an Edit sheet
    // and this view needs to reflect those changes immediately without a full list refresh.
    @State var character: Character
    @ObservedObject var campaignCreator: CampaignCreator

    @State private var showingEditView = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(character.name)
                    .font(.largeTitle)
                    .padding(.bottom, 5)

                if let imageURLs = character.imageURLs, !imageURLs.isEmpty {
                    SectionBox(title: "Image URLs") {
                        ForEach(imageURLs, id: \.self) { urlString in
                            Text(urlString)
                                .font(.caption)
                                .foregroundColor(.blue)
                                .onTapGesture {
                                    if let url = URL(string: urlString) {
                                        UIApplication.shared.open(url)
                                    }
                                }
                        }
                    }
                }

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

                SectionBox(title: "Metadata") {
                    HStack { Text("Created:"); Spacer(); Text(character.createdAt != nil ? "\(character.createdAt!, style: .date)" : "N/A") }
                    .font(.caption).foregroundColor(.secondary)
                    
                    HStack { Text("Modified:"); Spacer(); Text(character.modifiedAt != nil ? "\(character.modifiedAt!, style: .date)" : "N/A") }
                    .font(.caption).foregroundColor(.secondary)
                }
                Spacer()
            }
            .padding()
        }
        .navigationTitle(character.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Edit") { showingEditView = true }
            }
        }
        .sheet(isPresented: $showingEditView, onDismiss: {
            // Refresh character data if needed after edit view is dismissed
            // This is important if CharacterEditView modifies the character
            // and CampaignCreator.characters array is updated.
            // We need to find the updated character from the list.
            if let updatedCharacter = campaignCreator.characters.first(where: { $0.id == character.id }) {
                self.character = updatedCharacter
            }
        }) {
            CharacterEditView(character: character, campaignCreator: campaignCreator, isPresented: $showingEditView)
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

struct SectionBox<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title).font(.headline)
            content.padding().frame(maxWidth: .infinity, alignment: .leading)
                .background(Color(.systemGray6)).cornerRadius(8)
        }
        .padding(.vertical, 8)
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
