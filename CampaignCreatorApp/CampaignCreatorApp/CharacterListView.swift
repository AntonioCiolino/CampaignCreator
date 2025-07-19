import SwiftUI
import Kingfisher
import SwiftData
import CampaignCreatorLib

struct CharacterListView: View {
    @Environment(\.modelContext) private var modelContext
    @EnvironmentObject var contentViewModel: ContentViewModel
    @Query(sort: \CharacterModel.name) private var characters: [CharacterModel]
    @State private var showingCreateSheet = false
    @State private var showingErrorAlert = false
    @State private var errorMessage = ""

    private let apiService = CampaignCreatorLib.APIService()

    var body: some View {
        NavigationView {
            Group {
                if characters.isEmpty {
                    Text("No characters yet. Tap '+' to create one.")
                        .foregroundColor(.secondary)
                        .font(.title2)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(characters) { character in
                            NavigationLink(destination: CharacterDetailView(character: character)) {
                                HStack {
                                    if let firstImageURL = character.image_urls?.first, let url = URL(string: firstImageURL) {
                                        KFImage(url)
                                            .resizable()
                                            .aspectRatio(contentMode: .fill)
                                            .frame(width: 40, height: 40)
                                            .clipped()
                                            .cornerRadius(4)
                                    } else {
                                        Image(systemName: "person.fill")
                                            .resizable()
                                            .aspectRatio(contentMode: .fit)
                                            .frame(width: 40, height: 40)
                                            .foregroundColor(.gray)
                                    }
                                    VStack(alignment: .leading) {
                                        Text(character.name)
                                            .font(.headline)
                                        Text(character.character_description ?? "No description")
                                            .font(.subheadline)
                                            .foregroundColor(.gray)
                                            .lineLimit(2) // Limit description lines in list
                                    }
                                }
                            }
                        }
                        .onDelete(perform: deleteCharacters)
                    }
                    .refreshable {
                        await refreshCharacters()
                    }
                }
            }
            .navigationTitle("Characters")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        self.showingCreateSheet = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreateSheet) {
                if let user = contentViewModel.currentUser {
                    CharacterCreateView(isPresented: $showingCreateSheet, ownerId: user.id)
                }
            }
            .alert("Error", isPresented: $showingErrorAlert) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        }
    }

    private func deleteCharacters(offsets: IndexSet) {
        withAnimation {
            for index in offsets {
                let characterToDelete = characters[index]
                print("Attempting to delete character: \(characterToDelete.name)")
                modelContext.delete(characterToDelete)
            }

            do {
                try modelContext.save()
                print("Successfully saved model context from deleteCharacters.")
            } catch {
                print("Error saving model context from deleteCharacters: \(error.localizedDescription)")
            }
        }
    }

    @EnvironmentObject var networkMonitor: NetworkMonitor

    private func refreshCharacters() async {
        if networkMonitor.isConnected {
            await syncDirtyCharacters()
        }

        do {
            let fetchedCharacters = try await apiService.fetchCharacters()

            // Clear out existing characters to avoid duplicates
            for character in characters {
                modelContext.delete(character)
            }

            // Insert or update characters
            for character in fetchedCharacters {
                if let existingCharacter = characters.first(where: { $0.id == character.id }) {
                    existingCharacter.name = character.name
                    existingCharacter.character_description = character.description
                    existingCharacter.appearance_description = character.appearanceDescription
                    existingCharacter.image_urls = character.imageURLs
                    existingCharacter.notes_for_llm = character.notesForLLM
                    existingCharacter.strength = character.stats?.strength
                    existingCharacter.dexterity = character.stats?.dexterity
                    existingCharacter.constitution = character.stats?.constitution
                    existingCharacter.intelligence = character.stats?.intelligence
                    existingCharacter.wisdom = character.stats?.wisdom
                    existingCharacter.charisma = character.stats?.charisma
                    existingCharacter.export_format_preference = character.exportFormatPreference
                    existingCharacter.selected_llm_id = character.selectedLLMId
                    existingCharacter.temperature = character.temperature
                } else {
                    let characterModel = CharacterModel.from(character: character)
                    modelContext.insert(characterModel)
                }
            }

            try modelContext.save()
        } catch {
            errorMessage = "Failed to refresh characters: \(error.localizedDescription)"
            showingErrorAlert = true
        }
    }

    private func syncDirtyCharacters() async {
        let dirtyCharacters = characters.filter { $0.needsSync }
        for character in dirtyCharacters {
            do {
                let characterUpdate = CharacterUpdate(
                    name: character.name,
                    description: character.character_description,
                    appearance_description: character.appearance_description,
                    image_urls: character.image_urls,
                    notes_for_llm: character.notes_for_llm,
                    export_format_preference: character.export_format_preference
                )
                let body = try JSONEncoder().encode(characterUpdate)
                let _: CharacterModel = try await apiService.performRequest(endpoint: "/characters/\(character.id)", method: "PUT", body: body)
                character.needsSync = false
                try modelContext.save()
            } catch {
                print("Failed to sync character \(character.id): \(error.localizedDescription)")
            }
        }
    }
}

