import SwiftUI
import CampaignCreatorLib

struct CharacterCreateView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    @Binding var isPresented: Bool

    @State private var characterName: String = ""
    @State private var characterDescription: String = ""
    @State private var characterAppearance: String = "" // Added for more detail
    // TODO: Add @State vars for stats, imageURLs etc. if they are to be settable on creation

    @State private var isSaving: Bool = false
    @State private var showErrorAlert: Bool = false
    @State private var errorMessage: String = ""

    @Environment(\.dismiss) var dismiss // Use new dismiss environment variable

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Character Details")) {
                    TextField("Name*", text: $characterName)
                    VStack(alignment: .leading) {
                        Text("Description")
                            .font(.caption).foregroundColor(.gray)
                        TextEditor(text: $characterDescription)
                            .frame(height: 100)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                    VStack(alignment: .leading) {
                        Text("Appearance")
                            .font(.caption).foregroundColor(.gray)
                        TextEditor(text: $characterAppearance)
                            .frame(height: 100)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                    }
                }
                // TODO: Add sections for stats if CharacterStats is simple enough for creation form
            }
            .navigationTitle("New Character")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismissView()
                    }
                    .disabled(isSaving)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    if isSaving {
                        ProgressView()
                    } else {
                        Button("Save") {
                            Task {
                                await saveCharacter()
                            }
                        }
                        .disabled(characterName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSaving)
                    }
                }
            }
            .alert("Error Creating Character", isPresented: $showErrorAlert) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        }
    }

    private func saveCharacter() async {
        let name = characterName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }

        isSaving = true
        errorMessage = ""

        do {
            // Pass all relevant fields to createCharacter
            // The DTO used by createCharacter in APIService will handle which fields are sent
            _ = try await campaignCreator.createCharacter(
                name: name,
                description: characterDescription.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty(),
                appearance: characterAppearance.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
                // TODO: Pass stats if form includes them
            )
            // CampaignCreator.fetchCharacters() is called internally, updating the list.
            dismissView()
        } catch let error as APIError {
            errorMessage = error.localizedDescription
            showErrorAlert = true
            print("❌ Error creating character: \(errorMessage)")
        } catch {
            errorMessage = "An unexpected error occurred: \(error.localizedDescription)"
            showErrorAlert = true
            print("❌ Unexpected error creating character: \(errorMessage)")
        }
        isSaving = false
    }

    private func dismissView() {
        // isPresented binding is preferred for sheets
        isPresented = false
        // dismiss() // Use if not presented as a sheet or if binding doesn't work
    }
}

// Helper to convert empty strings to nil for optional fields
extension String {
    func nilIfEmpty() -> String? {
        self.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : self
    }
}

struct CharacterCreateView_Previews: PreviewProvider {
    static var previews: some View {
        @State var isPresented: Bool = true
        let campaignCreator = CampaignCreator()

        CharacterCreateView(campaignCreator: campaignCreator, isPresented: $isPresented)
    }
}
