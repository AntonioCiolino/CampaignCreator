import SwiftUI
import SwiftData
import CampaignCreatorLib

struct CharacterLinkingView: View {
    @Bindable var campaign: CampaignModel
    @Query private var characterModels: [CharacterModel]
    @State private var characters: [CharacterModel] = []
    @StateObject private var llmService = LLMService()
    @State private var showingErrorAlert = false
    @State private var errorMessage = ""
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        VStack(alignment: .leading) {
            ForEach(characters) { character in
                Toggle(isOn: binding(for: character)) {
                    Text(character.name)
                }
                .toggleStyle(.switch)
            }
        }
        .onAppear(perform: fetchAndMatchCharacters)
        .alert("Error", isPresented: $showingErrorAlert) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
    }

    private func fetchAndMatchCharacters() {
        Task {
            do {
                let fetchedCharacters = try await llmService.apiService.fetchCharacters()
                let fetchedCharacterIDs = fetchedCharacters.map { $0.id }

                // Filter local characterModels to only those that exist on the server
                self.characters = self.characterModels.filter { characterModel in
                    fetchedCharacterIDs.contains(characterModel.id)
                }
            } catch {
                self.errorMessage = "Failed to fetch characters: \(error.localizedDescription)"
                self.showingErrorAlert = true
            }
        }
    }

    private func binding(for character: CharacterModel) -> Binding<Bool> {
        Binding<Bool>(
            get: {
                self.campaign.linked_character_ids.contains(character.id)
            },
            set: { isLinked, _ in
                if isLinked {
                    if !self.campaign.linked_character_ids.contains(character.id) {
                        self.campaign.linked_character_ids.append(character.id)
                    }
                } else {
                    self.campaign.linked_character_ids.removeAll { $0 == character.id }
                }
            }
        )
    }
}
