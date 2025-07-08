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
    @Published public var initialCharacterFetchAttempted: Bool = false
    @Published public var initialCampaignFetchAttempted: Bool = false

    // Auth State
    @Published public var isAuthenticated: Bool = false
    @Published public var authError: APIError? = nil
    @Published public var isLoggingIn: Bool = false
    @Published public var currentUser: User? = nil
    @Published public var isUserSessionValid: Bool = false // New state for session validity

    public init(apiService: APIService = APIService()) {
        self.markdownGenerator = MarkdownGenerator()
        self.apiService = apiService
        self.setupLLMService()

        self.isAuthenticated = apiService.hasToken()
        if self.isAuthenticated {
            Task {
                await fetchCurrentUser() // Fetch user if already authenticated
            }
        }
    }
    
    private func setupLLMService() {
        do {
            self.llmService = try OpenAIClient()
            print("✅ OpenAI service initialized")
        } catch {
            print("⚠️ OpenAI service not available: \(error.localizedDescription)")
        }
    }

    // MARK: - Authentication
    public func login(usernameOrEmail: String, password: String) async {
        isLoggingIn = true
        authError = nil
        defer { isLoggingIn = false }

        let credentials = LoginRequestDTO(username: usernameOrEmail, password: password)
        do {
            let loginResponse = try await apiService.login(credentials: credentials)
            apiService.updateAuthToken(loginResponse.access_token)
            isAuthenticated = true
            await fetchCurrentUser() // This will set isUserSessionValid on success
        } catch let error as APIError {
            authError = error
            isAuthenticated = false
            currentUser = nil
            isUserSessionValid = false
            print("❌ Login failed: \(error.localizedDescription)")
        } catch {
            authError = APIError.custom("Login failed: An unexpected error occurred. \(error.localizedDescription)")
            isAuthenticated = false
            currentUser = nil
            isUserSessionValid = false
            print("❌ Login failed with unexpected error: \(error.localizedDescription)")
        }
    }

    public func logout() {
        apiService.updateAuthToken(nil)
        isAuthenticated = false
        currentUser = nil
        isUserSessionValid = false // Reset session validity
        campaigns = []
        characters = []
        initialCampaignFetchAttempted = false
        initialCharacterFetchAttempted = false
        print("Logged out.")
    }
    
    private func fetchCurrentUser() async {
        guard isAuthenticated else { // Still gate by initial token presence
            isUserSessionValid = false
            return
        }
        do {
            let user = try await apiService.getMe()
            self.currentUser = user
            self.isUserSessionValid = true // Session is valid
            print("✅ Fetched current user: \(user.email)")
        } catch let error as APIError {
            print("❌ Failed to fetch current user: \(error.localizedDescription)")
            // If /users/me fails (e.g. token expired), treat as logout
            self.isUserSessionValid = false
            if error == .notAuthenticated || error.errorDescription?.contains("401") == true {
                logout() // logout() will also set isAuthenticated and isUserSessionValid to false
            } else {
                self.authError = error
            }
        } catch {
            print("❌ Unexpected error fetching current user: \(error.localizedDescription)")
            self.authError = APIError.custom("Failed to fetch user details.")
            self.isUserSessionValid = false
        }
    }

    // MARK: - Campaign Management (Networked)
    public func fetchCampaigns() async {
        guard isAuthenticated else {
            campaignError = .notAuthenticated; print("⚠️ Cannot fetch campaigns: Not authenticated."); return
        }
        isLoadingCampaigns = true; campaignError = nil
        defer {
            isLoadingCampaigns = false
            self.initialCampaignFetchAttempted = true
        }
        do {
            self.campaigns = try await apiService.fetchCampaigns()
        } catch let error as APIError {
            self.campaignError = error; print("❌ Error fetching campaigns: \(error.localizedDescription)")
            if case .notAuthenticated = error { self.logout() }
            else if case .serverError(let statusCode, _) = error, statusCode == 401 { self.logout() }
        } catch { self.campaignError = APIError.custom("An unexpected error occurred: \(error.localizedDescription)"); print("❌ Unexpected error fetching campaigns: \(error.localizedDescription)")}
    }

    public func fetchCampaign(id: Int) async throws -> Campaign { // Changed id from UUID to Int
        guard isAuthenticated else { throw APIError.notAuthenticated }
        return try await apiService.fetchCampaign(id: id) // id is now Int
    }

    public func createCampaign(title: String, initialUserPrompt: String? = nil) async throws -> Campaign {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        // Assuming new campaigns start without custom sections by default, pass nil
        let dto = CampaignCreateDTO(title: title, initialUserPrompt: initialUserPrompt, customSections: nil)
        let newCampaign = try await apiService.createCampaign(dto)
        await fetchCampaigns()
        return newCampaign
    }

    public func updateCampaign(_ campaign: Campaign) async throws -> Campaign { // MODIFIED: Added -> Campaign return type
        guard isAuthenticated else { throw APIError.notAuthenticated }
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
            linkedCharacterIDs: campaign.linkedCharacterIDs,
            customSections: campaign.customSections, // ADDED
            sections: campaign.sections // ADDED standard sections
        )
        print("[THEME_DEBUG CampaignCreator] updateCampaign: DTO being sent to API for campaign \(campaign.id):") // DEBUG LOG
        print("[THEME_DEBUG CampaignCreator]   DTO.themePrimaryColor: \(dto.themePrimaryColor ?? "nil")") // DEBUG LOG
        print("[THEME_DEBUG CampaignCreator]   DTO.themeFontFamily: \(dto.themeFontFamily ?? "nil")") // DEBUG LOG
        print("[THEME_DEBUG CampaignCreator]   DTO.themeBgImageURL: \(dto.themeBackgroundImageURL ?? "nil")") // DEBUG LOG

        let updatedCampaignFromAPI = try await apiService.updateCampaign(campaign.id, data: dto)

        // Refresh the specific campaign in the local list
        if let index = campaigns.firstIndex(where: { $0.id == campaign.id }) {
            campaigns[index] = updatedCampaignFromAPI
            let customSectionIds = updatedCampaignFromAPI.customSections?.map { $0.id } ?? [] // Keep existing custom section log
            print("[SAVE_DEBUG CampaignCreator] updateCampaign: Campaign \(campaign.id) updated. CustomSection IDs from API response: \(customSectionIds)")

            print("[THEME_DEBUG CampaignCreator] updateCampaign: Refreshed campaign \(campaign.id) from API response. Theme values:") // DEBUG LOG
            print("[THEME_DEBUG CampaignCreator]   PrimaryColor: \(updatedCampaignFromAPI.themePrimaryColor ?? "nil")") // DEBUG LOG
            print("[THEME_DEBUG CampaignCreator]   FontFamily: \(updatedCampaignFromAPI.themeFontFamily ?? "nil")") // DEBUG LOG
            print("[THEME_DEBUG CampaignCreator]   BgImageURL: \(updatedCampaignFromAPI.themeBackgroundImageURL ?? "nil")") // DEBUG LOG
        } else {
            print("[SAVE_DEBUG CampaignCreator] Updated campaign \(campaign.id) not found in list. Fetching all campaigns.")
            await fetchCampaigns() // This case might ideally also return the specific updated campaign if possible,
                                   // or the caller has to be aware that a full refresh happened.
                                   // For now, it returns the direct API response if found, otherwise this branch implies a broader update.
        }
        return updatedCampaignFromAPI // MODIFIED: Added return
    }

    public func deleteCampaign(_ campaign: Campaign) async throws {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        try await apiService.deleteCampaign(id: campaign.id)
        await fetchCampaigns()
    }

    public func regenerateCampaignCustomSection(campaignId: Int, sectionId: Int, payload: SectionRegeneratePayload) async throws -> CampaignCustomSection { // sectionId changed to Int
        guard isAuthenticated else { throw APIError.notAuthenticated }
        let updatedSection = try await apiService.regenerateCampaignCustomSection(campaignId: campaignId, sectionId: sectionId, payload: payload) // Pass Int sectionId

        // After regeneration, the campaign's overall sections (including custom ones) might need an update.
        // The backend might return just the section, or the whole campaign.
        // If it returns just the section, we need to find the campaign and update that specific section.
        // This could be complex if customSections is nested.
        // For now, let's assume the backend handles updating the campaign structure if needed,
        // and we re-fetch the specific campaign to get all changes.
        // Or, if the payload directly updates the campaign's customSections array on the backend,
        // then fetching the campaign again is the most straightforward.

        // Option 1: Re-fetch the whole campaign (simpler, might be less performant if called frequently)
        // This also assumes that `fetchCampaigns()` updates the `campaigns` array
        // and the UI will find the updated campaign.
        // However, custom sections are part of the Campaign object, so fetching the specific campaign is better.
        if let index = campaigns.firstIndex(where: { $0.id == campaignId }) {
            do {
                let refreshedCampaign = try await fetchCampaign(id: campaignId)
                campaigns[index] = refreshedCampaign
                // It's important that the UI observing this campaign updates.
                // If CampaignDetailView holds its own @State copy, that needs to be updated too.
                // This is a general SwiftUI state management challenge.
                // For now, this updates the main campaigns array.
            } catch {
                print("Error re-fetching campaign \(campaignId) after custom section regeneration: \(error)")
                // Decide if we should throw the original updatedSection or this new error.
            }
        }
        return updatedSection // Return the directly updated section for immediate UI feedback if possible.
    }

    public func generateImageForSection(prompt: String, campaignId: Int, model: ImageModelName = .dalle, size: String? = "1024x1024", quality: String? = "standard") async throws -> ImageGenerationResponse {
        guard isAuthenticated else { throw APIError.notAuthenticated }

        let params = ImageGenerationParams(
            prompt: prompt,
            model: model, // Defaulting to dall-e, could be configurable
            size: size,
            quality: quality,
            campaignId: String(campaignId) // API expects string campaign_id
        )
        return try await apiService.generateImage(payload: params)
    }
    
    // MARK: - Character Management (Networked)
    public func fetchCharacters() async {
        guard isAuthenticated else {
            characterError = .notAuthenticated; print("⚠️ Cannot fetch characters: Not authenticated."); return
        }
        isLoadingCharacters = true; characterError = nil
        defer {
            isLoadingCharacters = false
            self.initialCharacterFetchAttempted = true
        }
        do {
            self.characters = try await apiService.fetchCharacters()
        } catch let error as APIError {
            self.characterError = error; print("❌ Error fetching characters: \(error.localizedDescription)")
            if case .notAuthenticated = error { self.logout() }
            else if case .serverError(let statusCode, _) = error, statusCode == 401 { self.logout() }
        } catch { self.characterError = APIError.custom("An unexpected error occurred while fetching characters: \(error.localizedDescription)"); print("❌ Unexpected error fetching characters: \(error.localizedDescription)")}
    }

    public func fetchCharacter(id: Int) async throws -> Character { // Changed id from UUID to Int
        guard isAuthenticated else { throw APIError.notAuthenticated }
        return try await apiService.fetchCharacter(id: id) // id is now Int
    }

    public func createCharacter(
        name: String,
        description: String? = nil,
        appearance: String? = nil,
        notesForLLM: String? = nil,
        imageURLs: [String]? = nil,
        exportFormatPreference: String? = "Complex", // Default here as well for safety
        stats: CharacterStats? = nil
    ) async throws -> Character {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        let dto = CharacterCreateDTO(
            name: name,
            description: description,
            appearanceDescription: appearance,
            imageURLs: imageURLs,
            notesForLLM: notesForLLM,
            stats: stats,
            exportFormatPreference: exportFormatPreference
        )
        let newCharacter = try await apiService.createCharacter(dto)
        await fetchCharacters() // Refresh the list
        return newCharacter
    }

    public func updateCharacter(_ character: Character) async throws {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        let dto = CharacterUpdateDTO(
            name: character.name, description: character.description,
            appearanceDescription: character.appearanceDescription, imageURLs: character.imageURLs,
            notesForLLM: character.notesForLLM, stats: character.stats,
            exportFormatPreference: character.exportFormatPreference
            // customSections: character.customSections // REMOVED
        )
        _ = try await apiService.updateCharacter(character.id, data: dto)
        await fetchCharacters()
    }
    
    public func deleteCharacter(_ character: Character) async throws {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        try await apiService.deleteCharacter(id: character.id)
        await fetchCharacters()
    }

    // MARK: - LLM Features
    public func generateText(prompt: String, completion: @escaping @Sendable (Result<String, LLMError>) -> Void) {
        guard isAuthenticated else { completion(.failure(.other(message: "Not authenticated."))); return }
        guard let llmService = llmService else { completion(.failure(.other(message: "LLM not available."))); return }
        llmService.generateCompletion(prompt: prompt, completionHandler: completion)
    }
    
    @available(macOS 10.15, iOS 13.0, tvOS 13.0, watchOS 6.0, *)
    public func generateText(prompt: String) async throws -> String {
        guard isAuthenticated else { throw LLMError.other(message: "Not authenticated.") }
        guard let llmService = llmService else { throw LLMError.other(message: "LLM not available.") }
        return try await llmService.generateCompletion(prompt: prompt)
    }

    @available(macOS 10.15, iOS 13.0, tvOS 13.0, watchOS 6.0, *)
    public func generateChatResponse(character: Character, message: String, chatHistory: [ChatMessageData]) async throws -> String { // Changed to ChatMessageData
        guard isAuthenticated else { throw LLMError.other(message: "Not authenticated.") }
        guard let llmService = llmService else { throw LLMError.other(message: "LLM not available.") }

        // Construct a more detailed prompt for the LLM
        var prompt = """
        You are roleplaying as the character '\(character.name)'.
        Your known details are:
        Description: \(character.description ?? "Not specified.")
        Appearance: \(character.appearanceDescription ?? "Not specified.")
        Notes for LLM (Personality, background, motivations, etc.): \(character.notesForLLM ?? "Not specified, rely on general knowledge and the persona derived from description and appearance.")

        Current conversation context (last few messages):
        """

        // Add recent chat history to the prompt (e.g., last 5 messages)
        // The ChatMessage struct needs to be accessible here or defined in a shared scope
        // For now, assuming ChatMessage is defined in CampaignCreatorLib or accessible.
        // If not, we'll need to adjust how chatHistory is passed or defined.
        // For this example, let's assume ChatMessage.Sender and .text are available.
        // This part needs ChatMessage to be defined in CampaignCreatorLib or a DTO.
        // For now, I'll use a placeholder for history formatting.
        // TODO: Define ChatMessage in CampaignCreatorLib or pass history as [(sender: String, text: String)]

        let recentHistory = chatHistory.suffix(5) // Take last 5 messages
        for chatMsg in recentHistory {
            // Assuming ChatMessage has 'sender' (e.g., .user, .llm) and 'text'
            // And ChatMessage.Sender has a rawValue or similar string representation
            // This is a placeholder and needs ChatMessage to be defined in this scope.
            // For now, let's use a simpler string representation if ChatMessage is not directly available
            // Or assume it's passed as a simpler structure e.g. [(sender: String, text: String)]
            // If ChatMessage is from App module, we can't use it here.
            // Let's assume chatHistory is passed as [(sender: String, text: String)] for now.
            // This means CharacterChatView needs to map its ChatMessage to this format.
            // For the plan, I'll assume ChatMessage is defined in Lib.
            // If not, CharacterChatView needs to pass history as [(sender: String, text: String)]
            let senderPrefix = chatMsg.sender == .user ? "User" : character.name // LLM speaks as character
            prompt += "\n\(senderPrefix): \(chatMsg.text)"
        }

        prompt += "\n\nUser: \(message)"
        prompt += "\n\(character.name): " // Prompt LLM to respond as the character

        print("--- Sending prompt to LLM for chat response for \(character.name) ---")
        print(prompt)
        print("--------------------------------------------------------------------")

        return try await llmService.generateCompletion(prompt: prompt)
    }
    
    // MARK: - Utility Functions
    public func showStatus() {
        print("\n=== Campaign Crafter Status ===")
        print("Authenticated: \(isAuthenticated), User: \(currentUser?.email ?? "None")")
        // ... (rest of status)
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
}

// MARK: - ObservableObject Protocol Support
#if canImport(Combine)
public protocol ObservableObjectProtocol: ObservableObject {}
#else
public protocol ObservableObjectProtocol: AnyObject {}
#endif
