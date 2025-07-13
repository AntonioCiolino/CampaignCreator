import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterEditViewModel: ObservableObject {
    @Published var characterToEdit: Character

    @Published var name: String
    @Published var descriptionText: String
    @Published var appearanceDescriptionText: String
    @Published var notesForLLMText: String

    enum ExportFormat: String, CaseIterable, Identifiable {
        case notSet = "Not Set"
        case complex = "Complex"
        case simple = "Simple"

        var id: String { self.rawValue }

        var displayName: String {
            switch self {
            case .notSet: return "Not Set (Use Default)"
            case .complex: return "Complex Stat Block"
            case .simple: return "Simple Stat Block"
            }
        }
    }
    @Published var selectedExportFormat: ExportFormat

    @Published var imageURLsText: [String]
    @Published var showingImageManager = false

    @Published var statsStrength: String
    @Published var statsDexterity: String
    @Published var statsConstitution: String
    @Published var statsIntelligence: String
    @Published var statsWisdom: String
    @Published var statsCharisma: String

    @Published var isDescriptionExpanded: Bool = true
    @Published var isAppearanceExpanded: Bool = true

    @Published var isSaving: Bool = false
    @Published var isGenerating: Bool = false
    @Published var errorMessage: String?

    private var apiService = CampaignCreatorLib.APIService()

    init(character: Character) {
        self.characterToEdit = character
        self.name = character.name
        self.descriptionText = character.description ?? ""
        self.appearanceDescriptionText = character.appearance_description ?? ""
        self.notesForLLMText = character.notes_for_llm ?? ""
        if let currentPreference = character.export_format_preference, !currentPreference.isEmpty {
            self.selectedExportFormat = ExportFormat(rawValue: currentPreference) ?? .notSet
        } else {
            self.selectedExportFormat = .notSet
        }
        self.imageURLsText = character.image_urls ?? []

        self.statsStrength = character.stats?.strength.map(String.init) ?? ""
        self.statsDexterity = character.stats?.dexterity.map(String.init) ?? ""
        self.statsConstitution = character.stats?.constitution.map(String.init) ?? ""
        self.statsIntelligence = character.stats?.intelligence.map(String.init) ?? ""
        self.statsWisdom = character.stats?.wisdom.map(String.init) ?? ""
        self.statsCharisma = character.stats?.charisma.map(String.init) ?? ""
    }

    enum AspectField { case description, appearance }

    func generateAspect(forField field: AspectField) async {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            errorMessage = "Character name must be provided to generate aspects."
            return
        }
        isGenerating = true
        errorMessage = nil
        let characterNameForPrompt = name.trimmingCharacters(in: .whitespacesAndNewlines)
        var prompt = ""
        switch field {
        case .description:
            prompt = "Generate a compelling character description for a character named '\\(characterNameForPrompt)'."
            if !descriptionText.isEmpty { prompt += " Consider this existing description: \\(descriptionText)"}
            if !appearanceDescriptionText.isEmpty { prompt += " Appearance notes: \\(appearanceDescriptionText)"}
        case .appearance:
            prompt = "Generate a vivid appearance description for a character named '\\(characterNameForPrompt)'."
            if !appearanceDescriptionText.isEmpty { prompt += " Consider this existing appearance: \\(appearanceDescriptionText)"}
            if !descriptionText.isEmpty { prompt += " General description: \\(descriptionText)"}
        }
        if !notesForLLMText.isEmpty { prompt += " Additional notes for generation: \\(notesForLLMText)"}

        do {
            let request = LLMGenerationRequest(prompt: prompt, model_id_with_prefix: nil, temperature: nil, max_tokens: nil, chat_history: nil, campaign_id: nil, section_title_suggestion: nil, section_type: nil, section_creation_prompt: nil)
            let body = try JSONEncoder().encode(request)
            let response: LLMTextGenerationResponse = try await apiService.performRequest(endpoint: "/llm/generate-text", method: "POST", body: body)
            switch field {
            case .description: descriptionText = response.text
            case .appearance: appearanceDescriptionText = response.text
            }
        } catch {
            errorMessage = "An unexpected error occurred during generation: \\(error.localizedDescription)"
        }
        isGenerating = false
    }

    func saveCharacterChanges() async -> Character? {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            errorMessage = "Character name cannot be empty."; return nil
        }
        isSaving = true; errorMessage = nil
        var updatedCharacter = characterToEdit
        updatedCharacter.name = name.trimmingCharacters(in: .whitespacesAndNewlines)
        updatedCharacter.description = descriptionText.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        updatedCharacter.appearance_description = appearanceDescriptionText.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()
        updatedCharacter.notes_for_llm = notesForLLMText.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty()

        if selectedExportFormat == .notSet {
            updatedCharacter.export_format_preference = nil
        } else {
            updatedCharacter.export_format_preference = selectedExportFormat.rawValue
        }

        let finalImageURLs = imageURLsText.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        if finalImageURLs.isEmpty {
            updatedCharacter.image_urls = nil
        } else {
            updatedCharacter.image_urls = finalImageURLs
        }

        var newStats = updatedCharacter.stats ?? CharacterStats(strength: nil, dexterity: nil, constitution: nil, intelligence: nil, wisdom: nil, charisma: nil)
        newStats.strength = Int(statsStrength)
        newStats.dexterity = Int(statsDexterity)
        newStats.constitution = Int(statsConstitution)
        newStats.intelligence = Int(statsIntelligence)
        newStats.wisdom = Int(statsWisdom)
        newStats.charisma = Int(statsCharisma)
        if newStats.strength != nil || newStats.dexterity != nil || newStats.constitution != nil || newStats.intelligence != nil || newStats.wisdom != nil || newStats.charisma != nil {
            updatedCharacter.stats = newStats
        } else {
            updatedCharacter.stats = nil
        }

        do {
            let characterUpdateDTO = characterToEdit.toCharacterUpdateDTO()
            let updatedLibCharacter: CampaignCreatorLib.Character = try await apiService.updateCharacter(characterToEdit.id, data: characterUpdateDTO)
            if let updatedAppCharacter = Character(from: updatedLibCharacter) {
                self.characterToEdit = updatedAppCharacter
            }
            isSaving = false
            return self.characterToEdit
        } catch {
            errorMessage = "An unexpected error occurred: \\(error.localizedDescription)"
            isSaving = false
            return nil
        }
    }
}
