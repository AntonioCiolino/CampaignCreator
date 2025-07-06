import SwiftUI
import CampaignCreatorLib

struct CharacterListView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    @State private var characters: [Character] = []
    @State private var showingCreateSheet = false

    var body: some View {
        NavigationView {
            List {
                ForEach(characters) { character in
                    VStack(alignment: .leading) {
                        Text(character.name)
                            .font(.headline)
                        Text(character.description ?? "No description")
                            .font(.subheadline)
                            .foregroundColor(.gray)
                    }
                }
                .onDelete(perform: deleteCharacters)
            }
            .navigationTitle("Characters")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        self.showingCreateSheet = true // Present CharacterCreateView as a sheet
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreateSheet, onDismiss: loadCharacters) { // Reload characters when sheet is dismissed
                CharacterCreateView(campaignCreator: campaignCreator, isPresented: $showingCreateSheet)
            }
            .onAppear {
                loadCharacters()
            }

            if characters.isEmpty && !showingCreateSheet { // Avoid showing placeholder when sheet is up
                Text("No characters yet. Tap '+' to create one.")
                    .foregroundColor(.secondary)
                    .font(.title2)
                    .frame(maxWidth: .infinity, maxHeight: .infinity) // Center it
                    .background(Color(.systemBackground)) // Ensure it's visible if list is empty
            }
        }
    }

    private func loadCharacters() {
        self.characters = campaignCreator.listCharacters()
        // For testing, if listCharacters is empty, add mock data:
        // This mock data logic can be removed once actual data persistence/flow is robust
        if self.characters.isEmpty && ProcessInfo.processInfo.environment["XCODE_RUNNING_FOR_PREVIEWS"] != "1" { // Don't add mock data in previews if list is empty
             print("No characters found in CampaignCreator, adding mock characters for UI testing (non-preview).")
             let mockChar1 = campaignCreator.createCharacter(name: "Elara Meadowlight")
             var mockChar1Updated = mockChar1 // Create mutable copy to update
             mockChar1Updated.description = "A brave elf ranger with a hawk companion."
             campaignCreator.updateCharacter(mockChar1Updated)

             let mockChar2 = campaignCreator.createCharacter(name: "Grom Bloodfist")
             var mockChar2Updated = mockChar2 // Create mutable copy
             mockChar2Updated.description = "A stoic orc warrior seeking redemption."
             campaignCreator.updateCharacter(mockChar2Updated)

             self.characters = campaignCreator.listCharacters() // Reload after adding mocks
        }
    }

    private func deleteCharacters(offsets: IndexSet) {
        let charactersToDelete = offsets.map { characters[$0] }
        for character in charactersToDelete {
            campaignCreator.deleteCharacter(character)
        }
        // The list will update automatically if `campaignCreator.characters` is @Published
        // and `characters` state var here is correctly updated from it.
        // Calling loadCharacters() ensures consistency if direct @Published updates aren't flowing as expected.
        loadCharacters()
    }
}

#Preview {
    // For preview, you might want to pass a CampaignCreator that already has some mock characters
    let previewCampaignCreator = CampaignCreator()
    let char1 = previewCampaignCreator.createCharacter(name: "Preview Elara")
    var updatedChar1 = char1
    updatedChar1.description = "Preview Elf Ranger"
    previewCampaignCreator.updateCharacter(updatedChar1)

    let char2 = previewCampaignCreator.createCharacter(name: "Preview Grom")
    var updatedChar2 = char2
    updatedChar2.description = "Preview Orc Warrior"
    previewCampaignCreator.updateCharacter(updatedChar2)

    return CharacterListView(campaignCreator: previewCampaignCreator)
}
