import SwiftUI
import Kingfisher
import SwiftData

struct CharacterDetailView: View {
    let character: CharacterModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                CharacterHeaderView(character: character, editableName: .constant(character.name), isSaving: false, isGeneratingText: false, currentPrimaryColor: .blue, onSetBadgeAction: {})

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

                // Add more sections as needed

            }
            .padding()
        }
        .navigationTitle(character.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .navigationBarTrailing) {
                Button("Edit") {
                    // ...
                }
            }
        }
    }
}
