import SwiftUI
import CampaignCreatorLib

struct CharacterEditView: View {
    @ObservedObject var campaignCreator: CampaignCreator
    @Binding var isPresented: Bool

    @State var characterToEdit: Character

    @State private var name: String
    @State private var descriptionText: String
    @State private var appearanceDescriptionText: String
    @State private var notesForLLMText: String
    @State private var exportFormatPreferenceText: String

    // For image URLs - simple list of text fields for now
    @State private var imageURLsText: [String] // Store URLs as strings for editing
    @State private var newImageURL: String = "" // For adding a new URL

    @State private var statsStrength: String
    @State private var statsDexterity: String
    @State private var statsConstitution: String
    @State private var statsIntelligence: String
    @State private var statsWisdom: String
    @State private var statsCharisma: String

    @State private var isSaving: Bool = false
    @State private var showErrorAlert: Bool = false
    @State private var errorMessage: String = ""

    @State private var isGeneratingAspect: Bool = false
    @State private var aspectGenerationError: String? = nil
    enum AspectField { case description, appearance }

    // New states for character image generation sheet
    @State private var showingCharacterImageSheet = false
    @State private var characterImageGeneratePrompt = ""
    @State private var characterImageGenerationError: String?
    @State private var isGeneratingCharacterImage = false


    @Environment(\.dismiss) var dismiss

    init(character: Character, campaignCreator: CampaignCreator, isPresented: Binding<Bool>) {
        self._characterToEdit = State(initialValue: character)
        self._campaignCreator = ObservedObject(wrappedValue: campaignCreator)
        self._isPresented = isPresented

        self._name = State(initialValue: character.name)
        self._descriptionText = State(initialValue: character.description ?? "")
        self._appearanceDescriptionText = State(initialValue: character.appearanceDescription ?? "")
        self._notesForLLMText = State(initialValue: character.notesForLLM ?? "")
        self._exportFormatPreferenceText = State(initialValue: character.exportFormatPreference ?? "")
        self._imageURLsText = State(initialValue: character.imageURLs ?? [])

        self._statsStrength = State(initialValue: character.stats?.strength.map(String.init) ?? "")
        self._statsDexterity = State(initialValue: character.stats?.dexterity.map(String.init) ?? "")
        self._statsConstitution = State(initialValue: character.stats?.constitution.map(String.init) ?? "")
        self._statsIntelligence = State(initialValue: character.stats?.intelligence.map(String.init) ?? "")
        self._statsWisdom = State(initialValue: character.stats?.wisdom.map(String.init) ?? "")
        self._statsCharisma = State(initialValue: character.stats?.charisma.map(String.init) ?? "")
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Basic Information")) {
                    TextField("Name*", text: $name)
                }

                Section(header: Text("Narrative Details")) {
                    generateableTextField(title: "Description", text: $descriptionText, fieldType: .description)
                    generateableTextField(title: "Appearance", text: $appearanceDescriptionText, fieldType: .appearance)
                }

                Section(header: Text("Character Image")) {
                    // Display current image URLs (if any)
                    if !imageURLsText.isEmpty {
                        ForEach(imageURLsText.indices, id: \.self) { index in
                            HStack {
                                TextField("Image URL", text: $imageURLsText[index])
                                Button(action: { imageURLsText.remove(at: index) }) {
                                    Image(systemName: "trash").foregroundColor(.red)
                                }
                            }
                        }
                    }
                    // Add new image URL
                    HStack {
                        TextField("Add new image URL", text: $newImageURL)
                        Button(action: {
                            if !newImageURL.isEmpty, let _ = URL(string: newImageURL) { // Basic URL validation
                                imageURLsText.append(newImageURL)
                                newImageURL = ""
                            }
                        }) {
                            Image(systemName: "plus.circle.fill")
                        }
                        .disabled(newImageURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }

                    Button(action: {
                        // Reset prompt and error before showing sheet
                        characterImageGeneratePrompt = "\(name) - \(appearanceDescriptionText)" // Pre-fill prompt
                        characterImageGenerationError = nil
                        showingCharacterImageSheet = true
                    }) {
                        Label("Generate Character Image (AI)", systemImage: "photo.on.rectangle.angled")
                    }
                    .disabled(isGeneratingAspect || isGeneratingCharacterImage)
                }

                Section(header: Text("Statistics (Optional)")) {
                    StatEditableRow(label: "Strength", valueString: $statsStrength)
                    StatEditableRow(label: "Dexterity", valueString: $statsDexterity)
                    StatEditableRow(label: "Constitution", valueString: $statsConstitution)
                    StatEditableRow(label: "Intelligence", valueString: $statsIntelligence)
                    StatEditableRow(label: "Wisdom", valueString: $statsWisdom)
                    StatEditableRow(label: "Charisma", valueString: $statsCharisma)
                }

                Section(header: Text("Additional Information")) {
                    VStack(alignment: .leading) {
                        Text("Notes for LLM (Optional)").font(.caption).foregroundColor(.gray)
                        TextEditor(text: $notesForLLMText).frame(height: 80)
                            .overlay(formElementOverlay())
                    }
                    TextField("Export Format Preference (Optional)", text: $exportFormatPreferenceText)
                }

                if let error = aspectGenerationError {
                    Text("Generation Error: \(error)").foregroundColor(.red).font(.caption)
                }
            }
            .navigationTitle("Edit Character")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismissView() }.disabled(isSaving || isGeneratingAspect)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    if isSaving || isGeneratingAspect {
                        ProgressView()
                    } else {
                        Button("Save") {
                            Task { await saveCharacterChanges() }
                        }
                        .disabled(name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSaving || isGeneratingAspect)
                    }
                }
            }
            .alert("Error Updating Character", isPresented: $showErrorAlert) {
                Button("OK") { }
            } message: { Text(errorMessage) }
            .disabled(isSaving || isGeneratingAspect)
        }
    }

    @ViewBuilder
    private func generateableTextField(title: String, text: Binding<String>, fieldType: AspectField) -> some View {
        VStack(alignment: .leading) {
            HStack {
                Text(title).font(.caption).foregroundColor(.gray)
                Spacer()
                Button(action: { Task { await generateAspect(forField: fieldType)} }) {
                    Label("Generate", systemImage: "sparkles")
                }
                .buttonStyle(.borderless)
                .disabled(isGeneratingAspect || name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            TextEditor(text: text).frame(height: 100)
                .overlay(formElementOverlay())
        }
    }

    private func formElementOverlay() -> some View {
        RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.5), lineWidth: 1)
    }

    private func requestImageGeneration() {
        // Placeholder for actual image generation logic
        print("Image generation requested for character: \(name)")
        // In a real implementation, this would:
        // 1. Construct a prompt (e.g., using name, appearance, description)
        // 2. Call a method in CampaignCreator (e.g., generateCharacterImage(prompt:))
        // 3. That method would call an APIService endpoint.
        // 4. Handle the response (e.g., an image URL or data) and update imageURLsText or display the image.
        // For now, we can show a temporary alert or log.
        errorMessage = "AI Image Generation feature is not yet implemented."
        showErrorAlert = true // Use the existing alert for simplicity
    }

    private func generateAspect(forField field: AspectField) async {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            aspectGenerationError = "Character name must be provided to generate aspects."
            return
        }
        isGeneratingAspect = true
        aspectGenerationError = nil
        let characterNameForPrompt = name.trimmingCharacters(in: .whitespacesAndNewlines)
        var prompt = ""
        switch field {
        case .description:
            prompt = "Generate a compelling character description for a character named '\(characterNameForPrompt)'."
            if !descriptionText.isEmpty { prompt += " Consider this existing description: \(descriptionText)"}
            if !appearanceDescriptionText.isEmpty { prompt += " Appearance notes: \(appearanceDescriptionText)"}
        case .appearance:
            prompt = "Generate a vivid appearance description for a character named '\(characterNameForPrompt)'."
            if !appearanceDescriptionText.isEmpty { prompt += " Consider this existing appearance: \(appearanceDescriptionText)"}
            if !descriptionText.isEmpty { prompt += " General description: \(descriptionText)"}
        }
        if !notesForLLMText.isEmpty { prompt += " Additional notes for generation: \(notesForLLMText)"}

        do {
            let generatedText = try await campaignCreator.generateText(prompt: prompt)
            switch field {
            case .description: descriptionText = generatedText
            case .appearance: appearanceDescriptionText = generatedText
            }
        } catch let error as LLMError {
            aspectGenerationError = error.localizedDescription
        } catch {
            aspectGenerationError = "An unexpected error occurred during generation: \(error.localizedDescription)"
        }
        isGeneratingAspect = false
    }

    private func saveCharacterChanges() async {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            errorMessage = "Character name cannot be empty."; showErrorAlert = true; return
        }
        isSaving = true; errorMessage = ""; aspectGenerationError = nil
        var updatedCharacter = characterToEdit
        updatedCharacter.name = name.trimmingCharacters(in: .whitespacesAndNewlines)
        updatedCharacter.description = descriptionText.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        updatedCharacter.appearanceDescription = appearanceDescriptionText.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        updatedCharacter.notesForLLM = notesForLLMText.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        updatedCharacter.exportFormatPreference = exportFormatPreferenceText.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        updatedCharacter.imageURLs = imageURLsText.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        if updatedCharacter.imageURLs?.isEmpty ?? true { updatedCharacter.imageURLs = nil }

        var newStats = CharacterStats()
        newStats.strength = Int(statsStrength)
        newStats.dexterity = Int(statsDexterity)
        newStats.constitution = Int(statsConstitution)
        newStats.intelligence = Int(statsIntelligence)
        newStats.wisdom = Int(statsWisdom)
        newStats.charisma = Int(statsCharisma)
        if newStats.strength != nil || newStats.dexterity != nil || newStats.constitution != nil || newStats.intelligence != nil || newStats.wisdom != nil || newStats.charisma != nil {
            updatedCharacter.stats = newStats
        } else { updatedCharacter.stats = nil }
        updatedCharacter.markAsModified()

        do {
            try await campaignCreator.updateCharacter(updatedCharacter)
            dismissView()
        } catch let error as APIError {
            errorMessage = error.localizedDescription; showErrorAlert = true
        } catch {
            errorMessage = "An unexpected error occurred: \(error.localizedDescription)"; showErrorAlert = true
        }
        isSaving = false
    }

    private func dismissView() { isPresented = false }
}

struct StatEditableRow: View {
    let label: String
    @Binding var valueString: String
    var body: some View {
        HStack {
            Text(label)
            Spacer()
            TextField("0", text: $valueString)
                .keyboardType(.numberPad).frame(width: 50)
                .multilineTextAlignment(.trailing).textFieldStyle(RoundedBorderTextFieldStyle())
        }
    }
}

struct CharacterEditView_Previews: PreviewProvider {
    static var previews: some View {
        @State var isPresented: Bool = true
        let creator = CampaignCreator()
        let sampleCharacter = Character(
            id: 1, name: "Aella Swiftarrow (Edit)", description: "A nimble scout...", // Changed id from UUID() to 1
            appearanceDescription: "Slender build...", imageURLs: ["http://example.com/img1.png"],
            stats: CharacterStats(strength: 10, dexterity: 15)
        )
        return CharacterEditView(character: sampleCharacter, campaignCreator: creator, isPresented: $isPresented)
    }
}
