import SwiftUI
import CampaignCreatorLib

struct CharacterCreateView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    @Binding var isPresented: Bool // To dismiss the sheet

    @State private var characterName: String = ""
    @State private var characterDescription: String = ""
    // TODO: Add fields for other character properties like stats, imageURLs etc. later

    @Environment(\.presentationMode) var presentationMode // Alternative way to dismiss

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Character Details")) {
                    TextField("Name", text: $characterName)
                    // Using TextEditor for potentially multi-line description
                    VStack(alignment: .leading) {
                        Text("Description (Optional)")
                            .font(.caption)
                            .foregroundColor(.gray)
                        TextEditor(text: $characterDescription)
                            .frame(height: 150) // Adjust height as needed
                            .overlay(
                                RoundedRectangle(cornerRadius: 5)
                                    .stroke(Color.gray.opacity(0.5), lineWidth: 1)
                            )
                    }
                }

                // TODO: Add sections for stats, appearance, notes for LLM etc. in future iterations
            }
            .navigationTitle("New Character")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismissView()
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        saveCharacter()
                        dismissView()
                    }
                    .disabled(characterName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
    }

    private func saveCharacter() {
        let name = characterName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }

        let newCharacter = campaignCreator.createCharacter(name: name)
        // Update description if provided
        if !characterDescription.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            var updatedCharacter = newCharacter
            updatedCharacter.description = characterDescription.trimmingCharacters(in: .whitespacesAndNewlines)
            campaignCreator.updateCharacter(updatedCharacter) // Assuming CampaignCreator has an update method
        }
        // After saving, CharacterListView will update itself on next appear or via @ObservedObject chain
    }

    private func dismissView() {
        if isPresented {
            isPresented = false
        } else {
            // Fallback if isPresented binding isn't used (e.g., direct navigation)
            presentationMode.wrappedValue.dismiss()
        }
    }
}

struct CharacterCreateView_Previews: PreviewProvider {
    static var previews: some View {
        // Create a dummy binding for the preview
        @State var isPresented: Bool = true
        let campaignCreator = CampaignCreator()

        CharacterCreateView(campaignCreator: campaignCreator, isPresented: $isPresented)
    }
}
