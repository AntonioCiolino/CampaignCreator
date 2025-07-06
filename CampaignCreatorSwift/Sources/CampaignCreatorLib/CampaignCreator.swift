import Foundation
#if canImport(Combine)
import Combine
#endif

@MainActor
public class CampaignCreator: ObservableObjectProtocol {
    public let markdownGenerator: MarkdownGenerator
    private var llmService: LLMService?
    private let apiService: APIService
    
    @Published public var campaigns: [Campaign] = []
    @Published public var characters: [Character] = []

    @Published public var isLoadingCampaigns: Bool = false
    @Published public var campaignError: APIError? = nil

    @Published public var isLoadingCharacters: Bool = false
    @Published public var characterError: APIError? = nil

    public init(apiService: APIService = APIService()) {
        self.markdownGenerator = MarkdownGenerator()
        self.apiService = apiService
        self.setupLLMService()
    }
    
    private func setupLLMService() {
        do {
            self.llmService = try OpenAIClient()
            print("✅ OpenAI service initialized")
        } catch {
            print("⚠️ OpenAI service not available: \(error.localizedDescription)")
        }
    }
    
    // MARK: - Campaign Management (Networked)
    public func fetchCampaigns() async {
        isLoadingCampaigns = true
        campaignError = nil
        do {
            let fetchedCampaigns = try await apiService.fetchCampaigns()
            self.campaigns = fetchedCampaigns
        } catch let error as APIError {
            self.campaignError = error
            print("❌ Error fetching campaigns: \(error.localizedDescription)")
        } catch {
            self.campaignError = APIError.custom("An unexpected error occurred: \(error.localizedDescription)")
            print("❌ Unexpected error fetching campaigns: \(error.localizedDescription)")
        }
        isLoadingCampaigns = false
    }

    public func fetchCampaign(id: UUID) async throws -> Campaign {
        return try await apiService.fetchCampaign(id: id)
    }

    public func createCampaign(title: String, initialUserPrompt: String? = nil) async throws -> Campaign {
        let dto = CampaignCreateDTO(title: title, initialUserPrompt: initialUserPrompt)
        let newCampaign = try await apiService.createCampaign(dto)
        await fetchCampaigns()
        return newCampaign
    }

    public func updateCampaign(_ campaign: Campaign) async throws {
        let dto = CampaignUpdateDTO(
            title: campaign.title, initialUserPrompt: campaign.initialUserPrompt, concept: campaign.concept,
            displayTOC: campaign.displayTOC, badgeImageURL: campaign.badgeImageURL,
            thematicImageURL: campaign.thematicImageURL, thematicImagePrompt: campaign.thematicImagePrompt,
            selectedLLMId: campaign.selectedLLMId, temperature: campaign.temperature,
            moodBoardImageURLs: campaign.moodBoardImageURLs, themePrimaryColor: campaign.themePrimaryColor,
            themeSecondaryColor: campaign.themeSecondaryColor, themeBackgroundColor: campaign.themeBackgroundColor,
            themeTextColor: campaign.themeTextColor, themeFontFamily: campaign.themeFontFamily,
            themeBackgroundImageURL: campaign.themeBackgroundImageURL,
            themeBackgroundImageOpacity: campaign.themeBackgroundImageOpacity,
            linkedCharacterIDs: campaign.linkedCharacterIDs
        )
        _ = try await apiService.updateCampaign(campaign.id, data: dto)
        await fetchCampaigns()
    }

    public func deleteCampaign(_ campaign: Campaign) async throws {
        try await apiService.deleteCampaign(id: campaign.id)
        await fetchCampaigns()
    }
    
    // MARK: - Character Management (Networked)
    public func fetchCharacters() async {
        isLoadingCharacters = true
        characterError = nil
        do {
            let fetchedCharacters = try await apiService.fetchCharacters()
            self.characters = fetchedCharacters
        } catch let error as APIError {
            self.characterError = error
            print("❌ Error fetching characters: \(error.localizedDescription)")
        } catch {
            self.characterError = APIError.custom("An unexpected error occurred while fetching characters: \(error.localizedDescription)")
            print("❌ Unexpected error fetching characters: \(error.localizedDescription)")
        }
        isLoadingCharacters = false
    }

    // Fetches a single character - useful if detail view needs fresh data
    public func fetchCharacter(id: UUID) async throws -> Character {
        return try await apiService.fetchCharacter(id: id)
    }

    public func createCharacter(name: String, description: String? = nil, appearance: String? = nil, stats: CharacterStats? = nil) async throws -> Character {
        let dto = CharacterCreateDTO(
            name: name,
            description: description,
            appearanceDescription: appearance,
            // imageURLs, notesForLLM, exportFormatPreference can be added if CharacterCreateView supports them
            stats: stats
        )
        let newCharacter = try await apiService.createCharacter(dto)
        await fetchCharacters() // Refresh the list
        return newCharacter
    }

    public func updateCharacter(_ character: Character) async throws {
        let dto = CharacterUpdateDTO(
            name: character.name,
            description: character.description,
            appearanceDescription: character.appearanceDescription,
            imageURLs: character.imageURLs,
            notesForLLM: character.notesForLLM,
            stats: character.stats,
            exportFormatPreference: character.exportFormatPreference
        )
        _ = try await apiService.updateCharacter(character.id, data: dto)
        await fetchCharacters() // Refresh the list
    }
    
    public func deleteCharacter(_ character: Character) async throws {
        try await apiService.deleteCharacter(id: character.id)
        await fetchCharacters() // Refresh the list
    }

    // MARK: - LLM Features
    public func generateText(prompt: String, completion: @escaping @Sendable (Result<String, LLMError>) -> Void) {
        guard let llmService = llmService else {
            completion(.failure(.other(message: "No LLM service available. Please set up API keys.")))
            return
        }
        llmService.generateCompletion(prompt: prompt, completionHandler: completion)
    }
    
    @available(macOS 10.15, iOS 13.0, tvOS 13.0, watchOS 6.0, *)
    public func generateText(prompt: String) async throws -> String {
        guard let llmService = llmService else {
            throw LLMError.other(message: "No LLM service available. Please set up API keys.")
        }
        return try await llmService.generateCompletion(prompt: prompt)
    }
    
    // MARK: - Utility Functions
    public func showStatus() {
        print("\n=== Campaign Crafter Status ===")
        print("Available Services: \(SecretsManager.shared.availableServices.joined(separator: ", "))")
        print("Fetched Campaigns: \(campaigns.count)")
        // ... (campaign listing logic) ...
        print("Fetched Characters: \(characters.count)")
        // ... (character listing logic) ...
        print("================================\n")
    }
    
    public func exportCampaignToHomebrewery(_ campaign: Campaign) -> String {
        let combinedText = campaign.sections.map { section in
            var text = ""
            if let title = section.title { text += "## \(title)\n\n" }
            text += section.content
            return text
        }.joined(separator: "\n\n---\n\n")
        return markdownGenerator.generateHomebreweryMarkdown(from: combinedText)
    }

    public func setAuthToken(_ token: String?) {
        apiService.updateAuthToken(token)
    }
}

// MARK: - ObservableObject Protocol Support
#if canImport(Combine)
public protocol ObservableObjectProtocol: ObservableObject {}
#else
public protocol ObservableObjectProtocol: AnyObject {}
#endif