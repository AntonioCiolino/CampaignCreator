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

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                CharacterHeaderView(character: character, editableName: .constant(character.name), isSaving: false, isGeneratingText: false, currentPrimaryColor: .blue)

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

                SectionBox(title: "Statistics") {
                    StatRow(label: "Strength", value: character.strength)
                    StatRow(label: "Dexterity", value: character.dexterity)
                    StatRow(label: "Constitution", value: character.constitution)
                    StatRow(label: "Intelligence", value: character.intelligence)
                    StatRow(label: "Wisdom", value: character.wisdom)
                    StatRow(label: "Charisma", value: character.charisma)
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
        .navigationTitle(character.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
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
}
