import Foundation
#if canImport(Combine)
import Combine
#endif

@MainActor
public class CampaignCreator: ObservableObjectProtocol {
    public let markdownGenerator: MarkdownGenerator
    private var llmService: LLMService?
    public let apiService: APIService // Changed from private to public
    
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

    private nonisolated var username: String?

    public var isLLMServiceAvailable: Bool {
        return llmService != nil
    }

    public init() {
        self.username = nil
        self.markdownGenerator = MarkdownGenerator()
        self.apiService = APIService(usernameProvider: { [weak self] in
            self?.username
        })
        self.setupLLMService()

        self.isAuthenticated = apiService.hasToken()
        if self.isAuthenticated {
            Task {
                await fetchCurrentUser() // Fetch user if already authenticated
            }
        }
    }
    
    // Made public to allow re-attempting setup if keys change
    public func setupLLMService() {
        print("[API_KEY_DEBUG CampaignCreator] setupLLMService: Attempting to setup LLMService.")
        // Reset to nil first in case a previous configuration existed but is now invalid
        // or to ensure a fresh attempt if keys were added.
        self.llmService = nil
        do {
            self.llmService = try OpenAIClient()
            print("✅ [API_KEY_DEBUG CampaignCreator] setupLLMService: OpenAIClient initialized successfully. llmService is now set.")
        } catch let error as LLMError where error == .apiKeyMissing {
            print("⚠️ [API_KEY_DEBUG CampaignCreator] setupLLMService: Failed to initialize OpenAIClient due to apiKeyMissing. llmService remains nil. Error: \(error.localizedDescription)")
        } catch {
            print("⚠️ [API_KEY_DEBUG CampaignCreator] setupLLMService: Failed to initialize OpenAIClient with an unexpected error. llmService remains nil. Error: \(error.localizedDescription)")
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
            apiService.updateAuthToken(loginResponse.accessToken) // MODIFIED to use camelCase
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
        username = nil
        isUserSessionValid = false // Reset session validity
        campaigns = []
        characters = []
        initialCampaignFetchAttempted = false
        initialCharacterFetchAttempted = false
        print("Logged out.")
    }
    
    public func fetchCurrentUser() async { // Changed from private to public
        guard isAuthenticated else { // Still gate by initial token presence
            isUserSessionValid = false
            return
        }
        do {
            let user = try await apiService.getMe()
            self.currentUser = user
            self.username = user.username
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

    public func refreshCampaign(id: Int) async throws -> Campaign {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        print("[CampaignCreator] Refreshing campaign with ID: \(id)")
        let fetchedCampaign = try await apiService.fetchCampaign(id: id) // This is a GET request for a single campaign
        
        // Update the campaign in the local @Published campaigns array
        if let index = campaigns.firstIndex(where: { $0.id == id }) {
            campaigns[index] = fetchedCampaign
            print("[CampaignCreator] Campaign \(id) updated in local list after refresh.")
        } else {
            // If campaign wasn't in the list (e.g., if it's a new campaign somehow not yet in the list,
            // or list was cleared), appending might make sense, or logging an error.
            // For a typical refresh of an existing item, it should be found.
            campaigns.append(fetchedCampaign)
            print("[CampaignCreator] Campaign \(id) was not in local list, appended after refresh. This might indicate an unexpected state or a need to reload the entire list.")
        }
        return fetchedCampaign // Return the fetched campaign
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

    public func generateImageForSection(prompt: String, campaignId: Int, model: ImageModelName = .defaultOpenAI, size: String? = "1024x1024", quality: String? = "standard") async throws -> ImageGenerationResponse {
        guard isAuthenticated else { throw APIError.notAuthenticated }

        let params = ImageGenerationParams(
            prompt: prompt,
            model: model.rawValue, // Defaulting to dall-e, could be configurable
            size: size,
            quality: quality,
            campaignId: campaignId // Pass Int directly
        )
        let response = try await apiService.generateImage(payload: params)

        guard let imageUrl = response.imageUrl, !imageUrl.isEmpty else {
            print("❌ [CampaignCreator] Image generation for section response successful, but imageUrl is missing or empty. Prompt used: \(response.promptUsed)")
            throw APIError.custom("Image generation for section response did not include a valid image URL.")
        }
        return response
    }

    // New public method for generic image generation
    public func generateImage(
        prompt: String,
        modelName: String, // Raw string value for ImageModelName
        size: String? = "1024x1024", // Default DALL-E 3 size
        quality: String? = "standard", // Default DALL-E quality
        associatedCampaignId: String? = nil
        // Add other params like steps, cfgScale if more models are deeply integrated here
    ) async throws -> ImageGenerationResponse {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        guard llmService != nil else { // Check if any LLM service is configured, assuming it implies image gen capability for now
            // This check might need refinement if image generation uses separate keys/services not tied to llmService
            throw LLMError.other(message: "Image generation service not available. API keys might be missing.")
        }

        guard let imageModel = ImageModelName(rawValue: modelName) else {
            throw APIError.custom("Invalid image model name provided: \(modelName)")
        }

        let params = ImageGenerationParams(
            prompt: prompt,
            model: imageModel.rawValue,
            size: size,
            quality: quality,
            // steps: nil, // Only for SD
            // cfgScale: nil, // Only for SD
            // geminiModelName: nil, // Only for Gemini
            campaignId: associatedCampaignId != nil ? Int(associatedCampaignId!) : nil
        )

        print("[CampaignCreator] Generating image with params: Prompt='\(prompt.prefix(50))...', Model='\(modelName)', Size='\(size ?? "default")', Quality='\(quality ?? "default")', CampaignID='\(associatedCampaignId ?? "nil")' (attempted Int conversion)")
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
            let fetchedChars = try await apiService.fetchCharacters()
            self.characters = fetchedChars
            // Log notes for all fetched characters (or a sample if too many)
            if let firstChar = fetchedChars.first { // Example: Log for the first character if list is not empty
                print("[CHAR_NOTES_DEBUG CampaignCreator] fetchCharacters: Fetched \(fetchedChars.count) chars. First char ID \(firstChar.id) notesForLLM: \(firstChar.notesForLLM ?? "nil")")
            } else {
                print("[CHAR_NOTES_DEBUG CampaignCreator] fetchCharacters: Fetched 0 characters.")
            }
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

    public func updateCharacter(_ character: Character) async throws -> Character { // MODIFIED: Added return type
        guard isAuthenticated else { throw APIError.notAuthenticated }
        let dto = CharacterUpdateDTO(
            name: character.name, description: character.description,
            appearanceDescription: character.appearanceDescription, imageURLs: character.imageURLs,
            notesForLLM: character.notesForLLM, stats: character.stats,
            exportFormatPreference: character.exportFormatPreference
            // customSections: character.customSections // REMOVED
        )
        print("[CHAR_DATA_DEBUG CampaignCreator] updateCharacter: Sending DTO for char ID \(character.id). DTO.notesForLLM: \(dto.notesForLLM ?? "nil"). DTO.exportFormatPreference: \(dto.exportFormatPreference ?? "nil"). DTO.imageURLs: \(dto.imageURLs ?? [])")
        let updatedCharacterFromAPI = try await apiService.updateCharacter(character.id, data: dto)
        print("[CHAR_DATA_DEBUG CampaignCreator] updateCharacter: Received updated character from API for char ID \(updatedCharacterFromAPI.id). API_notesForLLM: \(updatedCharacterFromAPI.notesForLLM ?? "nil"). API_exportFormatPreference: \(updatedCharacterFromAPI.exportFormatPreference ?? "nil"). API_imageURLs: \(updatedCharacterFromAPI.imageURLs ?? [])")

        // Update the local list immediately with the response from the API before full refresh
        // This provides a more immediate reflection of the change.
        if let index = characters.firstIndex(where: { $0.id == updatedCharacterFromAPI.id }) {
            characters[index] = updatedCharacterFromAPI
            print("[CHAR_NOTES_DEBUG CampaignCreator] updateCharacter: Updated local character list with API response for char ID \(updatedCharacterFromAPI.id). Local_notesForLLM: \(characters[index].notesForLLM ?? "nil")")
        } else {
            // If the character wasn't found, it might be a new one or list is out of sync.
            // Add it to the list. This scenario should be less common if lists are kept fresh.
            characters.append(updatedCharacterFromAPI)
            print("[CHAR_NOTES_DEBUG CampaignCreator] updateCharacter: Character ID \(updatedCharacterFromAPI.id) not found in local list, appended API response.")
        }

        // Consider if fetchCharacters() is still strictly necessary here if the primary goal is
        // to return the single updated character for immediate UI update.
        // If other parts of the app rely on the `characters` list being exhaustively fresh
        // *immediately* after any update, then keep it. Otherwise, it might be deferred
        // or handled by a background refresh mechanism.
        // For now, keeping it to maintain existing behavior, but the returned character is key.
        await fetchCharacters()
        return updatedCharacterFromAPI // MODIFIED: Added return
    }

    public func refreshCharacter(id: Int) async throws -> Character {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        print("[CHAR_DATA_DEBUG CampaignCreator] refreshCharacter: Refreshing character with ID \(id)")
        let refreshedChar = try await apiService.fetchCharacter(id: id)

        // Update in the local list
        if let index = characters.firstIndex(where: { $0.id == id }) {
            characters[index] = refreshedChar
            print("[CHAR_DATA_DEBUG CampaignCreator] refreshCharacter: Updated character ID \(id) in local list. New notes: \(refreshedChar.notesForLLM ?? "nil"), new appearance: \(refreshedChar.appearanceDescription ?? "nil")")
        } else {
            // If not in list, perhaps it's a new character somehow, or list was cleared.
            // Depending on desired behavior, could append or log. For a typical refresh, it should be in the list.
            characters.append(refreshedChar) // Or handle as an error/log if unexpected
            print("[CHAR_DATA_DEBUG CampaignCreator] refreshCharacter: Character ID \(id) not found in local list, appended. This might be unexpected.")
        }
        return refreshedChar
    }
    
    public func deleteCharacter(_ character: Character) async throws {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        try await apiService.deleteCharacter(id: character.id)
        await fetchCharacters()
    }

    public func autosaveCharacterImageURLs(characterID: Int, imageURLs: [String]) async throws {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        print("[CampaignCreator] Autosaving image URLs for character ID \(characterID): \(imageURLs)")
        let dto = CharacterUpdateDTO(imageURLs: imageURLs)
        // We call updateCharacter, which internally calls apiService.updateCharacter
        // This will also refresh the character in the local list if updateCharacter is implemented to do so,
        // or trigger a full fetchCharacters.
        // For auto-save, we might not need an immediate full list refresh if CharacterEditView's state is primary.

        // Refined approach: Direct API call for partial update of imageURLs
        let directDto = CharacterUpdateDTO(imageURLs: imageURLs)
        _ = try await apiService.updateCharacter(characterID, data: directDto)
        print("[CampaignCreator] Autosave API call for image URLs successful for character ID \(characterID).")
        // No local list refresh here to keep it lightweight; CharacterEditView has the state.
        // The Character object in CharacterEditView's state will be fully saved with all fields (including these URLs)
        // when its main 'Save' button is eventually pressed.
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
    public func generateChatResponse(
        character: Character,
        message: String, // This is the current user's prompt text
        chatHistory: [ChatMessageData]?, // This is List[{speaker, text}] from CharacterChatView
        modelIdWithPrefix: String?,
        temperature: Double?,
        maxTokens: Int?
    ) async throws -> LLMTextResponseDTO { // Changed return type to the DTO from APIService

        guard isAuthenticated else {
            // Throw an error consistent with APIService or a custom domain error
            // Using APIError.notAuthenticated for consistency with other auth checks
            throw APIError.notAuthenticated
        }
        // The direct llmService check here is less relevant now as APIService handles the call
        // to the backend, which then invokes the appropriate LLM via its own factory.
        // The primary gate is isAuthenticated for using APIService methods.

        print("[CampaignCreator] generateChatResponse: Preparing to call APIService.generateCharacterChatResponse for char ID \(character.id)")
        print("[CampaignCreator]   User Prompt: \(message.prefix(100))...")
        print("[CampaignCreator]   ChatHistory being sent (count): \(chatHistory?.count ?? 0)")
        if let history = chatHistory, !history.isEmpty {
            // Log only the last entry or a few for brevity if history is long
            for item in history.suffix(3) {
                print("[CampaignCreator]     - HistoryItem: \(item.speaker): \(item.text.prefix(50))...")
            }
        }
        // Note: The character.notesForLLM and memory_summary are now handled by the backend.
        // The client (iOS app via CampaignCreator) sends the prompt and recent chat history.
        // The backend /generate-response endpoint combines these with character notes and memory summary.

        return try await apiService.generateCharacterChatResponse(
            characterId: character.id, // Assuming your local Character model has an 'id' of type Int
            prompt: message,
            chatHistory: chatHistory, // This is [ChatMessageData] which is [{speaker, text}]
            modelIdWithPrefix: modelIdWithPrefix, // Pass through
            temperature: temperature,         // Pass through
            maxTokens: maxTokens              // Pass through
        )
    }
    
    public func getMemorySummary(characterId: Int) async throws -> String {
        guard isAuthenticated else {
            throw APIError.notAuthenticated
        }
        return try await apiService.getMemorySummary(characterId: characterId)
    }

    public func clearChatHistory(characterId: Int) async throws {
        guard isAuthenticated else {
            throw APIError.notAuthenticated
        }
        try await apiService.clearChatHistory(characterId: characterId)
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
