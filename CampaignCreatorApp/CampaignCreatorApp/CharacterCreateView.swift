import SwiftUI
import CampaignCreatorLib

struct CharacterCreateView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    @Binding var isPresented: Bool

    @State private var characterName: String = ""
    @State private var characterDescription: String = ""
    @State private var characterAppearance: String = ""
    @State private var characterNotesForLLM: String = ""
    @State private var characterExportFormatPreference: String = "Complex" // Default to "Complex"
    @State private var characterImageURLsText: [String] = []
    @State private var newImageURL: String = ""
    // TODO: Add @State vars for stats if they are to be settable on creation

    @State private var isSaving: Bool = false
    @State private var showErrorAlert: Bool = false
    @State private var errorMessage: String = ""

    // State for AI text generation
    @State private var isGeneratingDescription: Bool = false
    @State private var isGeneratingAppearance: Bool = false
    @State private var generationError: String? = nil
    enum AspectField { case description, appearance }

    @Environment(\.dismiss) var dismiss // Use new dismiss environment variable

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Character Details")) {
                    TextField("Name*", text: $characterName)
                        .disabled(isGeneratingDescription || isGeneratingAppearance)
                    generateableTextField(title: "Description", text: $characterDescription, fieldType: .description, isGenerating: $isGeneratingDescription)
                    generateableTextField(title: "Appearance", text: $characterAppearance, fieldType: .appearance, isGenerating: $isGeneratingAppearance)
                }

                Section(header: Text("Image URLs")) {
                    ForEach(characterImageURLsText.indices, id: \.self) { index in
                        HStack {
                            TextField("Image URL", text: $characterImageURLsText[index])
                            Button(action: { characterImageURLsText.remove(at: index) }) {
                                Image(systemName: "trash").foregroundColor(.red)
                            }
                        }
                    }
                    HStack {
                        TextField("Add new image URL", text: $newImageURL)
                        Button(action: {
                            if !newImageURL.isEmpty, let _ = URL(string: newImageURL) { // Basic URL validation
                                characterImageURLsText.append(newImageURL)
                                newImageURL = ""
                            }
                        }) {
                            Image(systemName: "plus.circle.fill")
                        }
                        .disabled(newImageURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }

                Section(header: Text("Additional Information")) {
                    VStack(alignment: .leading) {
                        Text("Notes for LLM (Optional)").font(.caption).foregroundColor(.gray)
                        TextEditor(text: $characterNotesForLLM)
                            .frame(height: 80)
                            .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                            .disabled(isGeneratingDescription || isGeneratingAppearance)
                    }
                    TextField("Export Format Preference", text: $characterExportFormatPreference)
                        .disabled(isGeneratingDescription || isGeneratingAppearance)
                }
                // TODO: Add sections for stats if CharacterStats is simple enough for creation form

                if let error = generationError {
                    Section {
                        Text("Generation Error: \(error)").foregroundColor(.red).font(.caption)
                    }
                }
            }
            .navigationTitle("New Character")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismissView()
                    }
                    .disabled(isSaving || isGeneratingDescription || isGeneratingAppearance)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    if isSaving || isGeneratingDescription || isGeneratingAppearance {
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

    @ViewBuilder
    private func generateableTextField(title: String, text: Binding<String>, fieldType: AspectField, isGenerating: Binding<Bool>) -> some View {
        VStack(alignment: .leading) {
            HStack {
                Text(title).font(.caption).foregroundColor(.gray)
                Spacer()
                Button(action: { Task { await generateAspect(forField: fieldType, isGenerating: isGenerating) } }) {
                    Label("Generate", systemImage: "sparkles")
                }
                .buttonStyle(.borderless)
                .disabled(isGeneratingDescription || isGeneratingAppearance || characterName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            TextEditor(text: text)
                .frame(height: 100)
                .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1))
                .disabled(isGeneratingDescription || isGeneratingAppearance)
        }
    }

    private func generateAspect(forField field: AspectField, isGenerating: Binding<Bool>) async {
        guard !characterName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            generationError = "Character name must be provided to generate aspects."
            return
        }
        isGenerating.wrappedValue = true
        generationError = nil

        let characterNameForPrompt = characterName.trimmingCharacters(in: .whitespacesAndNewlines)
        var prompt = ""
        switch field {
        case .description:
            prompt = "Generate a compelling character description for a character named '\(characterNameForPrompt)'."
            if !characterDescription.isEmpty { prompt += " Consider this existing partial description: \(characterDescription)"}
            if !characterAppearance.isEmpty { prompt += " Appearance notes: \(characterAppearance)"}
        case .appearance:
            prompt = "Generate a vivid appearance description for a character named '\(characterNameForPrompt)'."
            if !characterAppearance.isEmpty { prompt += " Consider this existing partial appearance: \(characterAppearance)"}
            if !characterDescription.isEmpty { prompt += " General description: \(characterDescription)"}
        }

        do {
            let generatedText = try await campaignCreator.generateText(prompt: prompt)
            switch field {
            case .description: characterDescription = generatedText
            case .appearance: characterAppearance = generatedText
            }
        } catch let error as LLMError {
            generationError = error.localizedDescription
            showErrorAlert = true // Using existing alert for simplicity
            errorMessage = error.localizedDescription
        } catch {
            generationError = "An unexpected error occurred during generation: \(error.localizedDescription)"
            showErrorAlert = true
            errorMessage = "An unexpected error occurred during generation: \(error.localizedDescription)"
        }
        isGenerating.wrappedValue = false
    }

    private func saveCharacter() async {
        let name = characterName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }

        isSaving = true
        errorMessage = ""

        do {
            // Pass all relevant fields to createCharacter
            // The DTO used by createCharacter in APIService will handle which fields are sent
            let finalExportFormatPreference = characterExportFormatPreference.trimmingCharacters(in: .whitespacesAndNewlines)
            _ = try await campaignCreator.createCharacter(
                name: name,
                description: characterDescription.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty(),
                appearance: characterAppearance.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty(),
                notesForLLM: characterNotesForLLM.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty(),
                imageURLs: characterImageURLsText.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }.nilIfEmpty(),
                exportFormatPreference: finalExportFormatPreference.isEmpty ? "Complex" : finalExportFormatPreference
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

// String.nilIfEmpty() is now provided by StringUtils.swift

// Helper to convert empty arrays to nil for optional fields
extension Array where Element == String {
    func nilIfEmpty() -> [String]? {
        self.isEmpty ? nil : self
    }
}

struct CharacterCreateView_Previews: PreviewProvider {
    static var previews: some View {
        @State var isPresented: Bool = true
        let campaignCreator = CampaignCreator()

        CharacterCreateView(campaignCreator: campaignCreator, isPresented: $isPresented)
    }
}
