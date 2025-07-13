import Foundation
import SwiftUI
import CampaignCreatorLib

@MainActor
class CharacterCreateViewModel: ObservableObject {
    @Published var characterName: String = ""
    @Published var characterDescription: String = ""
    @Published var characterAppearance: String = ""
    @Published var characterNotesForLLM: String = ""
    @Published var characterExportFormatPreference: String = "Complex"
    @Published var characterImageURLsText: [String] = []
    @Published var newImageURL: String = ""

    @Published var isSaving: Bool = false
    @Published var isGenerating: Bool = false
    @Published var errorMessage: String?

    private var apiService = CampaignCreatorLib.APIService()

    enum AspectField { case description, appearance }

    func generateAspect(forField field: AspectField) async {
        guard !characterName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            errorMessage = "Character name must be provided to generate aspects."
            return
        }
        isGenerating = true
        errorMessage = nil

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
            let request = LLMGenerationRequest(prompt: prompt, model_id_with_prefix: nil, temperature: nil, max_tokens: nil, chat_history: nil, campaign_id: nil, section_title_suggestion: nil, section_type: nil, section_creation_prompt: nil)
            let body = try JSONEncoder().encode(request)
            let response: LLMTextGenerationResponse = try await apiService.performRequest(endpoint: "/llm/generate-text", method: "POST", body: body)
            switch field {
            case .description: characterDescription = response.text
            case .appearance: characterAppearance = response.text
            }
        } catch {
            errorMessage = "An unexpected error occurred during generation: \(error.localizedDescription)"
        }
        isGenerating = false
    }

    func saveCharacter() async {
        let name = characterName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }

        isSaving = true
        errorMessage = ""

        do {
            let finalExportFormatPreference = characterExportFormatPreference.trimmingCharacters(in: .whitespacesAndNewlines)
            var character = CharacterCreate(
                name: name,
                description: characterDescription.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty(),
                appearance_description: characterAppearance.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty(),
                image_urls: characterImageURLsText.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }.nilIfEmpty(),
                video_clip_urls: nil,
                notes_for_llm: characterNotesForLLM.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty(),
                stats: nil,
                export_format_preference: finalExportFormatPreference.isEmpty ? "Complex" : finalExportFormatPreference
            )

            let characterCreateDTO = character.toCharacterCreateDTO()
            let _: CampaignCreatorLib.Character = try await apiService.createCharacter(characterCreateDTO)
        } catch {
            errorMessage = "An unexpected error occurred: \(error.localizedDescription)"
        }
        isSaving = false
    }
}
