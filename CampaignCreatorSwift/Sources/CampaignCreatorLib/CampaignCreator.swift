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

    // Auth State
    @Published public var isAuthenticated: Bool = false
    @Published public var authError: APIError? = nil
    @Published public var isLoggingIn: Bool = false
    @Published public var currentUser: User? = nil // Added currentUser

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
            await fetchCurrentUser() // Fetch user details after successful login
        } catch let error as APIError {
            authError = error
            isAuthenticated = false
            currentUser = nil
            print("❌ Login failed: \(error.localizedDescription)")
        } catch {
            authError = APIError.custom("Login failed: An unexpected error occurred. \(error.localizedDescription)")
            isAuthenticated = false
            currentUser = nil
            print("❌ Login failed with unexpected error: \(error.localizedDescription)")
        }
    }

    public func logout() {
        apiService.updateAuthToken(nil)
        isAuthenticated = false
        currentUser = nil // Clear current user
        campaigns = []
        characters = []
        print("Logged out.")
    }
    
    private func fetchCurrentUser() async {
        guard isAuthenticated else { return } // Should only be called if authenticated
        do {
            let user = try await apiService.getMe()
            self.currentUser = user
            print("✅ Fetched current user: \(user.email)")
        } catch let error as APIError {
            print("❌ Failed to fetch current user: \(error.localizedDescription)")
            // If /users/me fails (e.g. token expired), treat as logout
            if error == .notAuthenticated || error.errorDescription?.contains("401") == true { 
                logout()
            } else {
                self.authError = error // Or a different error property for user fetching
            }
        } catch {
            print("❌ Unexpected error fetching current user: \(error.localizedDescription)")
            self.authError = APIError.custom("Failed to fetch user details.")
        }
    }

    // MARK: - Campaign Management (Networked)
    public func fetchCampaigns() async {
        guard isAuthenticated else {
            campaignError = .notAuthenticated; print("⚠️ Cannot fetch campaigns: Not authenticated."); return
        }
        isLoadingCampaigns = true; campaignError = nil
        do {
            self.campaigns = try await apiService.fetchCampaigns()
        } catch let error as APIError { self.campaignError = error; print("❌ Error fetching campaigns: \(error.localizedDescription)")
        } catch { self.campaignError = APIError.custom("An unexpected error occurred: \(error.localizedDescription)"); print("❌ Unexpected error fetching campaigns: \(error.localizedDescription)")}
        isLoadingCampaigns = false
    }

    public func fetchCampaign(id: Int) async throws -> Campaign { // Changed id from UUID to Int
        guard isAuthenticated else { throw APIError.notAuthenticated }
        return try await apiService.fetchCampaign(id: id) // id is now Int
    }

    public func createCampaign(title: String, initialUserPrompt: String? = nil) async throws -> Campaign {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        let dto = CampaignCreateDTO(title: title, initialUserPrompt: initialUserPrompt)
        let newCampaign = try await apiService.createCampaign(dto)
        await fetchCampaigns()
        return newCampaign
    }

    public func updateCampaign(_ campaign: Campaign) async throws {
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
            linkedCharacterIDs: campaign.linkedCharacterIDs
        )
        _ = try await apiService.updateCampaign(campaign.id, data: dto)
        await fetchCampaigns()
    }

    public func deleteCampaign(_ campaign: Campaign) async throws {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        try await apiService.deleteCampaign(id: campaign.id)
        await fetchCampaigns()
    }
    
    // MARK: - Character Management (Networked)
    public func fetchCharacters() async {
        guard isAuthenticated else {
            characterError = .notAuthenticated; print("⚠️ Cannot fetch characters: Not authenticated."); return
        }
        isLoadingCharacters = true; characterError = nil
        do {
            self.characters = try await apiService.fetchCharacters()
        } catch let error as APIError { self.characterError = error; print("❌ Error fetching characters: \(error.localizedDescription)")
        } catch { self.characterError = APIError.custom("An unexpected error occurred while fetching characters: \(error.localizedDescription)"); print("❌ Unexpected error fetching characters: \(error.localizedDescription)")}
        isLoadingCharacters = false
    }

    public func fetchCharacter(id: UUID) async throws -> Character {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        return try await apiService.fetchCharacter(id: id)
    }

    public func createCharacter(name: String, description: String? = nil, appearance: String? = nil, stats: CharacterStats? = nil) async throws -> Character {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        let dto = CharacterCreateDTO(name: name, description: description, appearanceDescription: appearance, stats: stats)
        let newCharacter = try await apiService.createCharacter(dto)
        await fetchCharacters()
        return newCharacter
    }

    public func updateCharacter(_ character: Character) async throws {
        guard isAuthenticated else { throw APIError.notAuthenticated }
        let dto = CharacterUpdateDTO(
            name: character.name, description: character.description,
            appearanceDescription: character.appearanceDescription, imageURLs: character.imageURLs,
            notesForLLM: character.notesForLLM, stats: character.stats,
            exportFormatPreference: character.exportFormatPreference
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
