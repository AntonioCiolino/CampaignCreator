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
    // Removed: @State private var exportFormatPreferenceText: String

    // For Export Format Picker
    enum ExportFormat: String, CaseIterable, Identifiable {
        case notSet = "Not Set" // Represents clearing the preference
        case complex = "Complex" // "Complex Stat Block (Elara Style)"
        case simple = "Simple"   // "Simple Stat Block (Harlan Style)"

        var id: String { self.rawValue }

        var displayName: String {
            switch self {
            case .notSet: return "Not Set (Use Default)"
            case .complex: return "Complex Stat Block"
            case .simple: return "Simple Stat Block"
            }
        }
    }
    @State private var selectedExportFormat: ExportFormat

    // For image URLs - managed via CharacterImageManagerView
    @State private var imageURLsText: [String] // Store URLs as strings for editing
    // @State private var newImageURL: String = "" // REMOVED - Handled by manager view

    @State private var showingImageManager = false // State to present the image manager sheet

    @State private var statsStrength: String
    @State private var statsDexterity: String
    @State private var statsConstitution: String
    @State private var statsIntelligence: String
    @State private var statsWisdom: String
    @State private var statsCharisma: String

    // State for custom sections // REMOVED
    // @State private var localCustomSections: [CustomSection]

    // State for collapsible sections
    @State private var isDescriptionExpanded: Bool = true // Default to expanded
    @State private var isAppearanceExpanded: Bool = true // Default to expanded

    @State private var isSaving: Bool = false
    @State private var showErrorAlert: Bool = false
    @State private var errorMessage: String = ""

    // Callback for when a character is successfully updated
    var onCharacterUpdated: ((Character) -> Void)?

    @State private var isGeneratingAspect: Bool = false
    @State private var aspectGenerationError: String? = nil
    enum AspectField { case description, appearance }

    // New states for character image generation sheet
    // @State private var showingCharacterImageSheet = false // REMOVED - Old AI Gen UI
    // @State private var characterImageGeneratePrompt = "" // REMOVED - Old AI Gen UI
    // @State private var characterImageGenerationError: String? // REMOVED - Old AI Gen UI
    // @State private var isGeneratingCharacterImage = false // REMOVED - Old AI Gen UI


    @Environment(\.dismiss) var dismiss

    init(character: Character, campaignCreator: CampaignCreator, isPresented: Binding<Bool>, onCharacterUpdated: ((Character) -> Void)? = nil) {
        self._characterToEdit = State(initialValue: character)
        self._campaignCreator = ObservedObject(wrappedValue: campaignCreator)
        self._isPresented = isPresented
        self.onCharacterUpdated = onCharacterUpdated // Store the callback

        self._name = State(initialValue: character.name)
        self._descriptionText = State(initialValue: character.description ?? "")
        self._appearanceDescriptionText = State(initialValue: character.appearanceDescription ?? "")
        self._notesForLLMText = State(initialValue: character.notesForLLM ?? "")
        // Initialize selectedExportFormat
        if let currentPreference = character.exportFormatPreference, !currentPreference.isEmpty {
            self._selectedExportFormat = State(initialValue: ExportFormat(rawValue: currentPreference) ?? .notSet)
        } else {
            self._selectedExportFormat = State(initialValue: .notSet)
        }
        self._imageURLsText = State(initialValue: character.imageURLs ?? [])

        self._statsStrength = State(initialValue: character.stats?.strength.map(String.init) ?? "")
        self._statsDexterity = State(initialValue: character.stats?.dexterity.map(String.init) ?? "")
        self._statsConstitution = State(initialValue: character.stats?.constitution.map(String.init) ?? "")
        self._statsIntelligence = State(initialValue: character.stats?.intelligence.map(String.init) ?? "")
        self._statsWisdom = State(initialValue: character.stats?.wisdom.map(String.init) ?? "")
        self._statsCharisma = State(initialValue: character.stats?.charisma.map(String.init) ?? "")
        // self._localCustomSections = State(initialValue: character.customSections ?? []) // REMOVED
        print("[CHAR_NOTES_DEBUG CharacterEditView] Initializing for char ID \(character.id). Initial notesForLLMText: \(self._notesForLLMText.wrappedValue)")
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Basic Information")) {
                    TextField("Name*", text: $name)
                }

                Section(header: Text("Statistics (Optional)")) {
                    StatEditableRow(label: "Strength", valueString: $statsStrength)
                    StatEditableRow(label: "Dexterity", valueString: $statsDexterity)
                    StatEditableRow(label: "Constitution", valueString: $statsConstitution)
                    StatEditableRow(label: "Intelligence", valueString: $statsIntelligence)
                    StatEditableRow(label: "Wisdom", valueString: $statsWisdom)
                    StatEditableRow(label: "Charisma", valueString: $statsCharisma)
                }

                Section(header: Text("Narrative Details")) {
                    DisclosureGroup("Description", isExpanded: $isDescriptionExpanded) {
                        VStack(alignment: .leading) {
                            TextEditor(text: $descriptionText)
                                .frame(height: 100)
                                .overlay(formElementOverlay())
                            Button(action: { Task { await generateAspect(forField: .description) } }) {
                                Label("Generate Description", systemImage: "sparkles")
                            }
                            .buttonStyle(.borderless)
                            .disabled(isGeneratingAspect || name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !campaignCreator.isLLMServiceAvailable)
                            if !campaignCreator.isLLMServiceAvailable {
                                Text("OpenAI API key not configured for generation.")
                                    .font(.caption)
                                    .foregroundColor(.orange)
                            }
                        }
                    }

                    DisclosureGroup("Appearance", isExpanded: $isAppearanceExpanded) {
                        VStack(alignment: .leading) {
                            TextEditor(text: $appearanceDescriptionText)
                                .frame(height: 100)
                                .overlay(formElementOverlay())
                            Button(action: { Task { await generateAspect(forField: .appearance) } }) {
                                Label("Generate Appearance", systemImage: "sparkles")
                            }
                            .buttonStyle(.borderless)
                            .disabled(isGeneratingAspect || name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !campaignCreator.isLLMServiceAvailable)
                            if !campaignCreator.isLLMServiceAvailable {
                                Text("OpenAI API key not configured for generation.")
                                    .font(.caption)
                                    .foregroundColor(.orange)
                            }
                        }
                    }
                }

                Section(header: Text("Character Images")) {
                    if imageURLsText.isEmpty {
                        Text("No images. Manage images to add or generate new ones.")
                            .foregroundColor(.secondary)
                            .padding(.vertical)
                    } else {
                        TabView {
                            ForEach(imageURLsText, id: \.self) { urlString in
                                if let url = URL(string: urlString) {
                                    AsyncImage(url: url) { phase in
                                        switch phase {
                                        case .empty:
                                            ProgressView()
                                        case .success(let image):
                                            image.resizable()
                                                .aspectRatio(contentMode: .fit)
                                        case .failure:
                                            Image(systemName: "photo.fill")
                                                .foregroundColor(.gray)
                                                .overlay(Text("Error").font(.caption).foregroundColor(.red))
                                        @unknown default:
                                            EmptyView()
                                        }
                                    }
                                    .frame(height: 200) // Define a reasonable height for the carousel items
                                    .clipped()
                                } else {
                                    Image(systemName: "photo.fill")
                                        .foregroundColor(.gray)
                                        .overlay(Text("Invalid URL").font(.caption).foregroundColor(.red))
                                        .frame(height: 200)
                                }
                            }
                        }
                        .tabViewStyle(PageTabViewStyle())
                        .frame(height: 220) // Adjust height to accommodate PageTabViewStyle indicators
                        // .listRowInsets(EdgeInsets()) // Use if section spacing is an issue
                    }

                    Button(action: {
                        showingImageManager = true
                    }) {
                        Label("Manage Images", systemImage: "photo.on.rectangle.angled")
                    }
                }

                Section(header: Text("Additional Information")) {
                    VStack(alignment: .leading) {
                        Text("Notes for LLM (Optional)").font(.caption).foregroundColor(.gray)
                        TextEditor(text: $notesForLLMText).frame(height: 80)
                            .overlay(formElementOverlay())
                    }
                    Picker("Export Format Preference", selection: $selectedExportFormat) {
                        ForEach(ExportFormat.allCases) { format in
                            Text(format.displayName).tag(format)
                        }
                    }
                }

                // Section for "Custom Sections" REMOVED

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
            .disabled(isSaving || isGeneratingAspect) // Removed isGeneratingCharacterImage
            // .sheet for old AI image generation - REMOVED
            .sheet(isPresented: $showingImageManager) {
                CharacterImageManagerView(imageURLs: $imageURLsText, characterID: characterToEdit.id) // Pass characterID
                    .environmentObject(campaignCreator.apiService)
                    .environmentObject(campaignCreator) // Pass CampaignCreator for auto-save
            }
            .onChange(of: imageURLsText) { newValue in
                print("[CharacterEditView] imageURLsText changed. New value: \(newValue)")
            }
        }
    }

    // MARK: - Character Image Generation Sheet and performCharacterImageGeneration() - REMOVED

    // generateableTextField has been removed as its functionality is now inline with DisclosureGroups.

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

        let finalNotesForLLM = notesForLLMText.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        print("[CHAR_NOTES_DEBUG CharacterEditView] saveCharacterChanges for char ID \(characterToEdit.id). Final notesForLLM being set on updatedCharacter: \(finalNotesForLLM ?? "nil")")
        updatedCharacter.notesForLLM = finalNotesForLLM

        // Save selected export format
        if selectedExportFormat == .notSet {
            updatedCharacter.exportFormatPreference = nil
        } else {
            updatedCharacter.exportFormatPreference = selectedExportFormat.rawValue
        }

        print("[CharacterEditView saveCharacterChanges] Current imageURLsText before processing: \(imageURLsText)")
        let finalImageURLs = imageURLsText.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        if finalImageURLs.isEmpty {
            updatedCharacter.imageURLs = nil
        } else {
            updatedCharacter.imageURLs = finalImageURLs
        }
        print("[CharacterEditView saveCharacterChanges] updatedCharacter.imageURLs set to: \(updatedCharacter.imageURLs ?? [])")

        // if updatedCharacter.imageURLs?.isEmpty ?? true { updatedCharacter.imageURLs = nil } // Old logic replaced
        // updatedCharacter.customSections = localCustomSections.filter { !$0.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !$0.content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty } // REMOVED

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
            let savedCharacter = try await campaignCreator.updateCharacter(updatedCharacter)
            // Call the callback with the character returned from the API
            onCharacterUpdated?(savedCharacter)
            dismissView()
        } catch let error as APIError {
            errorMessage = error.localizedDescription; showErrorAlert = true
        } catch {
            errorMessage = "An unexpected error occurred: \(error.localizedDescription)"; showErrorAlert = true
        }
        isSaving = false
    }

    // private func addCustomSection() { // REMOVED
    //     localCustomSections.append(CustomSection(title: "New Section", content: ""))
    // }

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
            // customSections REMOVED
        )
        return CharacterEditView(character: sampleCharacter, campaignCreator: creator, isPresented: $isPresented)
    }
}
