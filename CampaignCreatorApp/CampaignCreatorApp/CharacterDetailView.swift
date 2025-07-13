import SwiftUI
import Kingfisher
import CampaignCreatorLib

struct CharacterDetailView: View {
    @StateObject private var viewModel: CharacterDetailViewModel
    @EnvironmentObject var imageUploadService: ImageUploadService

    @State private var showingEditView = false
    @State private var showingFullCharacterImageSheet = false
    @State private var selectedImageURLForSheet: URL? = nil

    init(character: Character) {
        _viewModel = StateObject(wrappedValue: CharacterDetailViewModel(character: character))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading) {
                        Text(viewModel.character.name)
                            .font(.largeTitle)
                    }
                    Spacer()
                    if let firstImageURLString = viewModel.character.image_urls?.first, let imageURL = URL(string: firstImageURLString) {
                        Button(action: {
                            selectedImageURLForSheet = imageURL
                            showingFullCharacterImageSheet = true
                        }) {
                            KFImage(imageURL)
                                .placeholder {
                                    ProgressView().frame(width: 50, height: 50)
                                }
                                .onFailure { error in
                                    print("KFImage failed to load character image \\(imageURL.absoluteString): \\(error.localizedDescription)")
                                }
                                .resizable()
                                .aspectRatio(contentMode: .fill)
                                .frame(width: 50, height: 50)
                                .clipShape(Circle())
                                .overlay(Circle().stroke(Color.secondary, lineWidth: 1))
                        }
                        .buttonStyle(.plain)
                    } else {
                        Image(systemName: "person.crop.circle")
                            .resizable().scaledToFit().frame(width: 50, height: 50).foregroundColor(.gray)
                    }
                }
                .padding(.bottom, 5)

                if let description = viewModel.character.description, !description.isEmpty {
                    SectionBox(title: "Description") { Text(description) }
                }

                if let appearance = viewModel.character.appearance_description, !appearance.isEmpty {
                    SectionBox(title: "Appearance") { Text(appearance) }
                }

                if let stats = viewModel.character.stats {
                    SectionBox(title: "Statistics") { StatsView(stats: stats) }
                }

                if let notes = viewModel.character.notes_for_llm, !notes.isEmpty {
                    SectionBox(title: "Notes for LLM") { Text(notes) }
                }

                if let exportFormat = viewModel.character.export_format_preference, !exportFormat.isEmpty {
                     SectionBox(title: "Export Preference") { Text(exportFormat) }
                }

                Spacer()
            }
            .padding()
        }
        .navigationTitle(viewModel.character.name)
        .navigationBarTitleDisplayMode(.inline)
        .refreshable {
            await viewModel.refreshCharacter()
        }
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                NavigationLink(destination: CharacterChatView(character: viewModel.character)) {
                    Image(systemName: "message.fill")
                }

                if let _ = viewModel.character.image_urls, !(viewModel.character.image_urls?.isEmpty ?? true) {
                    NavigationLink(destination: CharacterMoodboardView(character: viewModel.character, onCharacterUpdated: { updatedCharacter in
                        viewModel.character = updatedCharacter
                    }).environmentObject(imageUploadService)) {
                        Image(systemName: "photo.stack")
                    }
                }

                Button("Edit") { showingEditView = true }
            }
        }
        .sheet(isPresented: $showingEditView, onDismiss: {
            Task {
                await viewModel.refreshCharacter()
            }
        }) {
            CharacterEditView(character: viewModel.character, isPresented: $showingEditView, onCharacterUpdated: { updatedCharacter in
                viewModel.character = updatedCharacter
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
            Text(value != nil ? "\\(value!)" : "N/A").foregroundColor(value != nil ? .primary : .secondary)
        }
    }
}

struct CharacterDetailView_Previews: PreviewProvider {
    static var previews: some View {
        // Create a mock library character stats first
        let libStats = CampaignCreatorLib.CharacterStats(
            strength: 11,
            dexterity: 19,
            constitution: 12,
            intelligence: 10,
            wisdom: 14,
            charisma: 13
        )

        // Create a mock library character
        let libCharacter = CampaignCreatorLib.Character(
            id: 1,
            ownerID: 1,
            name: "Aella Swiftarrow (Detail)",
            description: "A nimble scout with keen eyes and a steady hand, always ready for adventure.",
            appearanceDescription: "Slender build, often seen in practical leather armor and a deep green cloak that helps her blend into forests. Has a braid of raven hair and striking blue eyes.",
            notesForLLM: "Loves nature, wary of large cities, skilled archer.",
            stats: libStats,
            exportFormatPreference: "Markdown",
            imageURLs: [""],
            campaignIDs: []
        )

        // Use the failable initializer to create the app-level character
        let sampleCharacter = Character(from: libCharacter)!

        return NavigationView {
            CharacterDetailView(character: sampleCharacter)
                .environmentObject(ImageUploadService()) // Add a mock service if needed
        }
    }
}
