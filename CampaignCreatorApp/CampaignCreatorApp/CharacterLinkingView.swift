import SwiftUI

struct CharacterLinkingView: View {
    @Bindable var campaign: CampaignModel
    @Binding var characters: [CharacterModel]
    @StateObject private var llmService = LLMService()
    @State private var showingErrorAlert = false
    @State private var errorMessage = ""

    var body: some View {
        VStack(alignment: .leading) {
            ForEach(characters) { character in
                Toggle(isOn: binding(for: character)) {
                    Text(character.name)
                }
                .toggleStyle(.switch)
            }
        }
        .onAppear(perform: fetchCharacters)
        .alert("Error", isPresented: $showingErrorAlert) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
    }

    private func fetchCharacters() {
        Task {
            do {
                let fetchedCharacters = try await llmService.apiService.fetchCharacters()
                self.characters = fetchedCharacters
            } catch {
                self.errorMessage = "Failed to fetch characters: \(error.localizedDescription)"
                self.showingErrorAlert = true
            }
        }
    }

    private func binding(for character: CharacterModel) -> Binding<Bool> {
        Binding<Bool>(
            get: {
                self.campaign.linked_character_ids?.contains(character.id) ?? false
            },
            set: { isLinked in
                if isLinked {
                    if self.campaign.linked_character_ids == nil {
                        self.campaign.linked_character_ids = []
                    }
                    self.campaign.linked_character_ids?.append(character.id)
                } else {
                    self.campaign.linked_character_ids?.removeAll { $0 == character.id }
                }
            }
        )
    }
}
