import SwiftUI
import Kingfisher
import SwiftData

struct CharacterDetailView: View {
    let character: CharacterModel

    @State private var showingEditSheet = false
    @State private var showingImageManager = false
    @State private var selectedLLMId = ""
    @State private var temperature = 0.7
    @StateObject private var llmService = LLMService()
    @State private var showingErrorAlert = false
    @State private var errorMessage = ""

    @Environment(\.modelContext) private var modelContext

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                CharacterHeaderView(character: character, editableName: .constant(character.name), isSaving: false, isGeneratingText: false, currentPrimaryColor: .blue)

                CharacterStatsView(character: character)

                if let description = character.character_description, !description.isEmpty {
                    SectionBox(title: "Description") {
                        Text(description)
                    }
                }

                if let appearance = character.appearance_description, !appearance.isEmpty {
                    SectionBox(title: "Appearance") {
                        Text(appearance)
                    }
                }

                if let notes = character.notes_for_llm, !notes.isEmpty {
                    SectionBox(title: "Notes for LLM") {
                        Text(notes)
                    }
                }

                CharacterLLMSettingsView(selectedLLMId: $selectedLLMId, temperature: $temperature, availableLLMs: llmService.availableLLMs, onLLMSettingsChange: {
                    character.selected_llm_id = selectedLLMId
                    character.temperature = temperature
                })

                CharacterMoodboardView(character: character, onSetBadgeAction: {
                    showingImageManager = true
                })

            }
            .padding()
        }
        .onDisappear(perform: {
            if character.hasChanges {
                character.needsSync = true
                try? modelContext.save()
            }
        })
        .navigationTitle(character.name)
        .navigationBarTitleDisplayMode(.inline)
        .refreshable {
            await refreshCharacter()
        }
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                NavigationLink(destination: MemoriesListView(character: character)) {
                    Image(systemName: "brain")
                }

                NavigationLink(destination: CharacterChatView(character: character)) {
                    Image(systemName: "message")
                }

                Button("Edit") {
                    showingEditSheet = true
                }
            }
        }
        .sheet(isPresented: $showingEditSheet) {
            CharacterEditView(character: character, isPresented: $showingEditSheet)
        }
        .sheet(isPresented: $showingImageManager) {
            CharacterImageManagerView(imageURLs: .init(get: { character.image_urls ?? [] }, set: { character.image_urls = $0 }), characterID: 0)
        }
        .onAppear {
            selectedLLMId = character.selected_llm_id ?? ""
            temperature = character.temperature ?? 0.7
            Task {
                do {
                    try await llmService.fetchAvailableLLMs()
                } catch {
                    errorMessage = error.localizedDescription
                    showingErrorAlert = true
                }
            }
        }
        .alert("Error", isPresented: $showingErrorAlert) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
    }

    private func refreshCharacter() async {
        do {
            let refreshedCharacter = try await llmService.apiService.fetchCharacter(id: character.id)
            character.name = refreshedCharacter.name
            character.character_description = refreshedCharacter.description
            character.appearance_description = refreshedCharacter.appearanceDescription
            character.image_urls = refreshedCharacter.imageURLs
            character.notes_for_llm = refreshedCharacter.notesForLLM
            character.strength = refreshedCharacter.stats?.strength
            character.dexterity = refreshedCharacter.stats?.dexterity
            character.constitution = refreshedCharacter.stats?.constitution
            character.intelligence = refreshedCharacter.stats?.intelligence
            character.wisdom = refreshedCharacter.stats?.wisdom
            character.charisma = refreshedCharacter.stats?.charisma
            character.export_format_preference = refreshedCharacter.exportFormatPreference
            character.selected_llm_id = refreshedCharacter.selectedLLMId
            character.temperature = refreshedCharacter.temperature
        } catch {
            errorMessage = "Failed to refresh character: \(error.localizedDescription)"
            showingErrorAlert = true
        }
    }
}
