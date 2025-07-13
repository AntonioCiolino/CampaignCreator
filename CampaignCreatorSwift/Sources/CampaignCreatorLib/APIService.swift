import Foundation
import Combine // Import Combine for ObservableObject

// Note: These structs are temporarily moved here to resolve build issues.
// Ideally, they should be in their own file within the Lib, ensured to be part of the target.

public struct AvailableLLM: Identifiable, Codable, Hashable {
    public var id: String // Prefixed ID, e.g., "openai/gpt-3.5-turbo"
    public var name: String // User-friendly name, e.g., "OpenAI GPT-3.5 Turbo"
    public var modelType: String?
    public var supportsTemperature: Bool
    public var capabilities: [String]?

    public init(id: String, name: String, modelType: String?, supportsTemperature: Bool, capabilities: [String]? = nil) {
        self.id = id
        self.name = name
        self.modelType = modelType
        self.supportsTemperature = supportsTemperature
        self.capabilities = capabilities
    }
}

public struct LLMModelsResponse: Codable {
    public var models: [AvailableLLM]

    public init(models: [AvailableLLM]) {
        self.models = models
    }
}

// Error enum for API related issues

// Error enum for API related issues
public enum APIError: Error, LocalizedError, Sendable, Equatable { // Added Equatable
    case invalidURL
    case requestFailed(Error) // Associated value Error might not be Equatable
    case decodingFailed(Error) // Associated value Error might not be Equatable
    case encodingFailed(Error) // Associated value Error might not be Equatable
    case serverError(statusCode: Int, data: Data?)
    case noData
    case notAuthenticated
    case custom(String)

    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The API endpoint URL was invalid."
        case .requestFailed(let error):
            return "The network request failed: \(error.localizedDescription)"
        case .decodingFailed(let error):
            var detailedError = "Failed to decode the server response."
            if let decodingError = error as? DecodingError {
                // ... (detailed error descriptions)
                 switch decodingError {
                 case .typeMismatch(let type, let context):
                     detailedError += " Type mismatch for type \(type) at \(context.codingPath.map { $0.stringValue }.joined(separator: ".")): \(context.debugDescription)"
                 case .valueNotFound(let type, let context):
                     detailedError += " Value not found for type \(type) at \(context.codingPath.map { $0.stringValue }.joined(separator: ".")): \(context.debugDescription)"
                 case .keyNotFound(let key, let context):
                     detailedError += " Key not found: \(key.stringValue) at \(context.codingPath.map { $0.stringValue }.joined(separator: ".")): \(context.debugDescription)"
                 case .dataCorrupted(let context):
                     detailedError += " Data corrupted at \(context.codingPath.map { $0.stringValue }.joined(separator: ".")): \(context.debugDescription)"
                 @unknown default:
                     detailedError += " Unknown decoding error: \(error.localizedDescription)"
                 }
            } else {
                detailedError += " \(error.localizedDescription)"
            }
            return detailedError
        case .encodingFailed(let error):
            return "Failed to encode the request data: \(error.localizedDescription)"
        case .serverError(let statusCode, _):
            return "Server error with status code: \(statusCode)."
        case .noData:
            return "No data received from the server."
        case .notAuthenticated:
            return "User is not authenticated or the token is invalid."
        case .custom(let message):
            return message
        }
    }

    // Manual Equatable conformance
    public static func == (lhs: APIError, rhs: APIError) -> Bool {
        switch (lhs, rhs) {
        case (.invalidURL, .invalidURL): return true
        case (.requestFailed(_), .requestFailed(_)): return true // Simplified: compare only cases, not associated errors
        case (.decodingFailed(_), .decodingFailed(_)): return true // Simplified
        case (.encodingFailed(_), .encodingFailed(_)): return true // Simplified
        case (let .serverError(sc1, data1), let .serverError(sc2, data2)): return sc1 == sc2 && data1 == data2
        case (.noData, .noData): return true
        case (.notAuthenticated, .notAuthenticated): return true
        case (let .custom(s1), let .custom(s2)): return s1 == s2
        default: return false
        }
    }
}

// DTOs for Campaign operations
public struct CampaignCreateDTO: Codable, Sendable {
    public var title: String
    public var initialUserPrompt: String?
    public var customSections: [CampaignCustomSection]? // ADDED

    public init(title: String, initialUserPrompt: String? = nil, customSections: [CampaignCustomSection]? = nil) { // ADDED
        self.title = title
        self.initialUserPrompt = initialUserPrompt
        self.customSections = customSections // ADDED
    }
}

public struct CampaignUpdateDTO: Codable, Sendable {
    public var title: String?
    public var initialUserPrompt: String?
    public var concept: String?
    public var displayTOC: [TOCEntry]?
    public var badgeImageURL: String?
    public var thematicImageURL: String?
    public var thematicImagePrompt: String?
    public var selectedLLMId: String?
    public var temperature: Double?
    public var moodBoardImageURLs: [String]?
    public var themePrimaryColor: String?
    public var themeSecondaryColor: String?
    public var themeBackgroundColor: String?
    public var themeTextColor: String?
    public var themeFontFamily: String?
    public var themeBackgroundImageURL: String?
    public var themeBackgroundImageOpacity: Double?
    public var linkedCharacterIDs: [Int]? // CHANGED from [UUID]?
    public var customSections: [CampaignCustomSection]? // ADDED
    public var sections: [CampaignSection]? // ADDED for standard sections

    enum CodingKeys: String, CodingKey {
        case title
        case initialUserPrompt = "initial_user_prompt"
        case concept
        case displayTOC = "display_toc"
        case badgeImageURL = "badge_image_url"
        case thematicImageURL = "thematic_image_url"
        case thematicImagePrompt = "thematic_image_prompt"
        case selectedLLMId = "selected_llm_id"
        case temperature
        case moodBoardImageURLs = "mood_board_image_urls" // Explicitly correct snake_case
        case themePrimaryColor = "theme_primary_color"
        case themeSecondaryColor = "theme_secondary_color"
        case themeBackgroundColor = "theme_background_color"
        case themeTextColor = "theme_text_color"
        case themeFontFamily = "theme_font_family"
        case themeBackgroundImageURL = "theme_background_image_url"
        case themeBackgroundImageOpacity = "theme_background_image_opacity"
        case linkedCharacterIDs = "linked_character_ids"
        case customSections = "custom_sections"
        case sections
    }

    public init(title: String? = nil, initialUserPrompt: String? = nil, concept: String? = nil, displayTOC: [TOCEntry]? = nil, badgeImageURL: String? = nil, thematicImageURL: String? = nil, thematicImagePrompt: String? = nil, selectedLLMId: String? = nil, temperature: Double? = nil, moodBoardImageURLs: [String]? = nil, themePrimaryColor: String? = nil, themeSecondaryColor: String? = nil, themeBackgroundColor: String? = nil, themeTextColor: String? = nil, themeFontFamily: String? = nil, themeBackgroundImageURL: String? = nil, themeBackgroundImageOpacity: Double? = nil, linkedCharacterIDs: [Int]? = nil, customSections: [CampaignCustomSection]? = nil, sections: [CampaignSection]? = nil) { // CHANGED linkedCharacterIDs to [Int]?, ADDED sections
        self.title = title
        self.initialUserPrompt = initialUserPrompt
        self.concept = concept
        self.displayTOC = displayTOC
        self.badgeImageURL = badgeImageURL
        self.thematicImageURL = thematicImageURL
        self.thematicImagePrompt = thematicImagePrompt
        self.selectedLLMId = selectedLLMId
        self.temperature = temperature
        self.moodBoardImageURLs = moodBoardImageURLs
        self.themePrimaryColor = themePrimaryColor
        self.themeSecondaryColor = themeSecondaryColor
        self.themeBackgroundColor = themeBackgroundColor
        self.themeTextColor = themeTextColor
        self.themeFontFamily = themeFontFamily
        self.themeBackgroundImageURL = themeBackgroundImageURL
        self.themeBackgroundImageOpacity = themeBackgroundImageOpacity
        self.linkedCharacterIDs = linkedCharacterIDs
        self.customSections = customSections // ADDED
    }
}

// DTOs for Character operations
public struct CharacterCreateDTO: Codable, Sendable {
    public var name: String
    public var description: String?
    public var appearanceDescription: String?
    public var imageURLs: [String]?
    public var notesForLLM: String?
    public var stats: CharacterStats?
    public var exportFormatPreference: String?
    // public var customSections: [CustomSection]? // REMOVED

    enum CodingKeys: String, CodingKey {
        case name
        case description
        case appearanceDescription = "appearance_description"
        case imageURLs = "image_urls"
        case notesForLLM = "notes_for_llm"
        case stats
        case exportFormatPreference = "export_format_preference"
    }

    public init(name: String, description: String? = nil, appearanceDescription: String? = nil, imageURLs: [String]? = nil, notesForLLM: String? = nil, stats: CharacterStats? = nil, exportFormatPreference: String? = nil /*, customSections: [CustomSection]? = nil REMOVED */) {
        self.name = name
        self.description = description
        self.appearanceDescription = appearanceDescription
        self.imageURLs = imageURLs
        self.notesForLLM = notesForLLM
        self.stats = stats
        self.exportFormatPreference = exportFormatPreference
        // self.customSections = customSections // REMOVED
    }
}

public struct CharacterUpdateDTO: Codable, Sendable {
    public var name: String?
    public var description: String?
    public var appearanceDescription: String?
    public var imageURLs: [String]?
    public var notesForLLM: String?
    public var stats: CharacterStats?
    public var exportFormatPreference: String?
    // public var customSections: [CustomSection]? // REMOVED

    enum CodingKeys: String, CodingKey {
        case name
        case description
        case appearanceDescription = "appearance_description"
        case imageURLs = "image_urls"
        case notesForLLM = "notes_for_llm"
        case stats
        case exportFormatPreference = "export_format_preference"
    }

    public init(name: String? = nil, description: String? = nil, appearanceDescription: String? = nil, imageURLs: [String]? = nil, notesForLLM: String? = nil, stats: CharacterStats? = nil, exportFormatPreference: String? = nil /*, customSections: [CustomSection]? = nil REMOVED */) {
        self.name = name
        self.description = description
        self.appearanceDescription = appearanceDescription
        self.imageURLs = imageURLs
        self.notesForLLM = notesForLLM
        self.stats = stats
        self.exportFormatPreference = exportFormatPreference
        // self.customSections = customSections // REMOVED
    }
}

// DTOs for Auth operations
public struct LoginRequestDTO: Codable, Sendable {
    public var username: String
    public var password: String

    public init(username: String, password: String) {
        self.username = username
        self.password = password
    }
}

public struct LoginResponseDTO: Codable, Sendable {
    // Properties now camelCase to work with global .convertFromSnakeCase strategy
    let accessToken: String
    let tokenType: String

    // No explicit CodingKeys needed if backend sends "access_token" and "token_type"
    // and jsonDecoder.keyDecodingStrategy = .convertFromSnakeCase is set.
    // No custom init needed; memberwise initializer will be synthesized.
}


// Simple protocol for token management
public protocol TokenManaging: Sendable {
    func getToken() -> String?
    func setToken(_ token: String?)
    func clearToken()
    func hasToken() -> Bool
}

public final class UserDefaultsTokenManager: TokenManaging {
    private let tokenKey = "AuthToken"
    public func getToken() -> String? { UserDefaults.standard.string(forKey: tokenKey) }
    public func setToken(_ token: String?) {
        if let token = token { UserDefaults.standard.set(token, forKey: tokenKey) }
        else { UserDefaults.standard.removeObject(forKey: tokenKey) }
    }
    public func clearToken() { UserDefaults.standard.removeObject(forKey: tokenKey) }
    public func hasToken() -> Bool { getToken() != nil }

    public init() {}
}


// Payload for LLM Generation Request
struct LLMGenerationRequestPayload: Encodable {
    let prompt: String
    let chatHistory: [ChatMessageData]?
    let modelIdWithPrefix: String?
    let temperature: Double?
    let maxTokens: Int?

    enum CodingKeys: String, CodingKey {
        case prompt
        case chatHistory = "chat_history"
        case modelIdWithPrefix = "model_id_with_prefix"
        case temperature
        case maxTokens = "max_tokens"
    }
}

public final class APIService: ObservableObject, Sendable { // Added ObservableObject conformance
    public let baseURLString = "https://campaigncreator-api.onrender.com/api/v1" // Made public
    private let tokenManager: TokenManaging
    // @Published properties are not strictly necessary for this service if its state doesn't change
    // or if UI doesn't need to react to its internal state changes directly.
    // However, if token changes should refresh UI, tokenManager could be @Published or methods could publish.
    private let jsonDecoder: JSONDecoder
    private let jsonEncoder: JSONEncoder

    public init(tokenManager: TokenManaging = UserDefaultsTokenManager()) {
        self.tokenManager = tokenManager

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .formatted(JSONDecoder.iso8601withFractionalSeconds)
        decoder.keyDecodingStrategy = .convertFromSnakeCase // ADDED
        self.jsonDecoder = decoder

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.keyEncodingStrategy = .convertToSnakeCase // ADDED
        encoder.outputFormatting = .prettyPrinted
        self.jsonEncoder = encoder
    }

    // Public getter for the token
    public func getToken() -> String? {
        return tokenManager.getToken()
    }

    @MainActor
    public func updateAuthToken(_ token: String?) {
        tokenManager.setToken(token)
    }

    public func hasToken() -> Bool {
        return tokenManager.getToken() != nil
    }

    private func performRequest<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil,
        headers: [String: String] = [:],
        requiresAuth: Bool = true
    ) async throws -> T {
        guard let url = URL(string: baseURLString + endpoint) else { throw APIError.invalidURL }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.httpBody = body
        request.cachePolicy = .reloadIgnoringLocalCacheData // Added to force reload
        request.setValue("app://com.campaigncreator.app", forHTTPHeaderField: "Origin") // Set custom Origin for iOS app

        if request.value(forHTTPHeaderField: "Content-Type") == nil {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        if request.value(forHTTPHeaderField: "Accept") == nil {
            request.setValue("application/json", forHTTPHeaderField: "Accept")
        }

        for (key, value) in headers {
            request.setValue(value, forHTTPHeaderField: key)
        }

        if requiresAuth {
            print("APIService [Auth]: Attempting to get token for endpoint '\(endpoint)'. Token currently in manager: \(tokenManager.getToken() ?? "NIL - Not Found")")
            guard let token = tokenManager.getToken() else {
                print("APIService [Auth]: No token retrieved by tokenManager for authenticated request to '\(endpoint)'. Throwing APIError.notAuthenticated.")
                throw APIError.notAuthenticated
            }
            print("APIService [Auth]: Successfully retrieved token. Using token for '\(endpoint)': Bearer \(token.prefix(20))...")
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        print("🚀 \(method) \(url)")
        if let body = body, let str = String(data: body, encoding: .utf8) { print("   Body: \(str.prefix(500))") }

        // Print Request Headers for Debugging
        print("   [REQUEST HEADERS for \(method) \(url.absoluteString)]")
        if let allHTTPHeaderFields = request.allHTTPHeaderFields {
            for (header, value) in allHTTPHeaderFields {
                print("     \(header): \(value)")
            }
        } else {
            print("     No headers found on request.")
        }
        print("   --- END HEADERS ---")

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else { throw APIError.requestFailed(URLError(.badServerResponse)) }

            print("✅ \(httpResponse.statusCode) from \(url)")
            if let str = String(data: data, encoding: .utf8) { print("   Response Data: \(str.prefix(500))") }

            if httpResponse.statusCode == 401 { throw APIError.notAuthenticated }
            guard (200...299).contains(httpResponse.statusCode) else { throw APIError.serverError(statusCode: httpResponse.statusCode, data: data) }

            if T.self == Data.self { return data as! T }
            if data.isEmpty {
                if let voidValue = () as? T { return voidValue }
                else if let optionalNil = Optional<Any>.none as? T { return optionalNil }
            }

            // Log raw data before decoding if it's for Character types
            if String(describing: T.self) == "Character" || String(describing: T.self) == "Array<Character>" || String(describing: T.self) == "Optional<Character>" {
                print("[DECODE_DEBUG APIService] Raw data for Character type before decoding: \(String(data: data, encoding: .utf8) ?? "Unable to stringify data")")
            }

            // Log raw JSON if T is Campaign
            if T.self == Campaign.self || T.self == [Campaign].self {
                print("[APIService Decode Debug - PRE] Raw JSON for Campaign(s): \(String(data: data, encoding: .utf8) ?? "Unable to stringify data")")
            }

            do {
                let decodedObject: T
                if T.self == Character.self || T.self == [Character].self {
                    // Using LOCAL JSONDecoder for Character type WITHOUT .convertFromSnakeCase strategy.
                    let localCharacterDecoder = JSONDecoder()
                    localCharacterDecoder.dateDecodingStrategy = .iso8601
                    decodedObject = try localCharacterDecoder.decode(T.self, from: data)
                } else if T.self == ImageGenerationResponse.self {
                    // Using LOCAL JSONDecoder for ImageGenerationResponse WITHOUT .convertFromSnakeCase strategy.
                    // This is to rely solely on its explicit CodingKeys, similar to Character.
                    let localImageResponseDecoder = JSONDecoder()
                    localImageResponseDecoder.dateDecodingStrategy = .iso8601 // Good practice, though not used by this specific struct
                    // No keyDecodingStrategy set, relying on CodingKeys
                    decodedObject = try localImageResponseDecoder.decode(T.self, from: data)
                } else if T.self == Campaign.self || T.self == [Campaign].self {
                    // Using LOCAL JSONDecoder for Campaign type WITHOUT .convertFromSnakeCase strategy.
                    // This allows Campaign's own CodingKeys to handle the snake_case to camelCase mapping.
                    let localCampaignDecoder = JSONDecoder()
                    localCampaignDecoder.dateDecodingStrategy = .iso8601
                    // DO NOT SET: localCampaignDecoder.keyDecodingStrategy = .convertFromSnakeCase
                    // This ensures that the keys are passed as-is (e.g. "badge_image_url") to the Campaign's decoder,
                    // which expects to find them via its CodingKeys.
                    decodedObject = try localCampaignDecoder.decode(T.self, from: data)
                }
                else {
                    // For other types, use the shared decoder with .convertFromSnakeCase.
                    decodedObject = try self.jsonDecoder.decode(T.self, from: data)
                }

                // Log specific fields if it's a Character or [Character]
                if let character = decodedObject as? Character {
                    print("[DECODE_DEBUG APIService] Decoded Character (single): ID \(character.id), notesForLLM: '\(character.notesForLLM ?? "nil")', appearance: '\(character.appearanceDescription ?? "nil")'")
                } else if let characters = decodedObject as? [Character] {
                    if let firstChar = characters.first {
                        print("[DECODE_DEBUG APIService] Decoded [Character] (first item): ID \(firstChar.id), notesForLLM: '\(firstChar.notesForLLM ?? "nil")', appearance: '\(firstChar.appearanceDescription ?? "nil")'")
                    } else {
                        print("[DECODE_DEBUG APIService] Decoded [Character]: Array is empty.")
                    }
                }

                // Log specific fields if T is Campaign
                if T.self == Campaign.self, let campaignData = decodedObject as? Campaign {
                    print("[APIService Decode Debug - POST] Decoded Campaign ID: \(campaignData.id)")
                    print("[APIService Decode Debug - POST]   badgeImageURL: \(campaignData.badgeImageURL ?? "nil")")
                    print("[APIService Decode Debug - POST]   moodBoardImageURLs: \(campaignData.moodBoardImageURLs?.joined(separator: ", ") ?? "nil")")
                } else if T.self == [Campaign].self, let campaignsArray = decodedObject as? [Campaign], let firstCampaign = campaignsArray.first {
                    print("[APIService Decode Debug - POST] Decoded [Campaign] (first item) ID: \(firstCampaign.id)")
                    print("[APIService Decode Debug - POST]   badgeImageURL: \(firstCampaign.badgeImageURL ?? "nil")")
                    print("[APIService Decode Debug - POST]   moodBoardImageURLs: \(firstCampaign.moodBoardImageURLs?.joined(separator: ", ") ?? "nil")")
                }

                return decodedObject
            } catch {
                print("❌ Decoding failed for type \(T.self): \(error.localizedDescription)")
                // It's important to log the raw data if T.self is Character or [Character] here as well,
                // because the JSONSerialization above might succeed, but the Codable decoding might fail for other reasons.
                if String(describing: T.self) == "Character" || String(describing: T.self) == "Array<Character>" {
                     print("[DECODE_DEBUG APIService] Raw data that FAILED Codable decoding for Character type: \(String(data: data, encoding: .utf8) ?? "Unable to stringify data")")
                }
                if let decodingError = error as? DecodingError {
                     switch decodingError {
                     case .typeMismatch(let type, let context):
                         print("   Type mismatch for type \(type) at \(context.codingPath.map { $0.stringValue }.joined(separator: ".")): \(context.debugDescription)")
                     case .valueNotFound(let type, let context):
                         print("   Value not found for type \(type) at \(context.codingPath.map { $0.stringValue }.joined(separator: ".")): \(context.debugDescription)")
                     case .keyNotFound(let key, let context):
                         print("   Key not found: \(key.stringValue) at \(context.codingPath.map { $0.stringValue }.joined(separator: ".")): \(context.debugDescription)")
                     case .dataCorrupted(let context):
                         print("   Data corrupted at \(context.codingPath.map { $0.stringValue }.joined(separator: ".")): \(context.debugDescription)")
                     @unknown default:
                         print("   Unknown decoding error: \(error.localizedDescription)")
                     }
                 }
                throw APIError.decodingFailed(error)
            }
        } catch let error as APIError { throw error }
        catch { print("❌ Request failed: \(error)"); throw APIError.requestFailed(error) }
    }

    private func performVoidRequest(
        endpoint: String,
        method: String = "DELETE",
        body: Data? = nil,
        requiresAuth: Bool = true
    ) async throws {
        guard let url = URL(string: baseURLString + endpoint) else { throw APIError.invalidURL }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.httpBody = body
        request.cachePolicy = .reloadIgnoringLocalCacheData // Added to force reload
        request.setValue("app://com.campaigncreator.app", forHTTPHeaderField: "Origin") // Set custom Origin for iOS app
        if method != "GET" && method != "HEAD" { request.setValue("application/json", forHTTPHeaderField: "Content-Type") }

        if requiresAuth {
            guard let token = tokenManager.getToken() else { throw APIError.notAuthenticated }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        // Print Request Headers for Debugging
        print("   [REQUEST HEADERS for \(method) \(url.absoluteString) (void)]")
        if let allHTTPHeaderFields = request.allHTTPHeaderFields {
            for (header, value) in allHTTPHeaderFields {
                print("     \(header): \(value)")
            }
        } else {
            print("     No headers found on request.")
        }
        print("   --- END HEADERS ---")

        print("🚀 \(method) \(url) (expecting no content)")
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else { throw APIError.requestFailed(URLError(.badServerResponse)) }
            print("✅ \(httpResponse.statusCode) from \(url)")
            if let str = String(data: data, encoding: .utf8) { print("   Response Data: \(str.prefix(500))") }
            if httpResponse.statusCode == 401 { throw APIError.notAuthenticated }
            guard (200...299).contains(httpResponse.statusCode) else { throw APIError.serverError(statusCode: httpResponse.statusCode, data: data) }
        } catch let error as APIError { throw error }
        catch { print("❌ Request failed: \(error)"); throw APIError.requestFailed(error) }
    }

    // MARK: - Campaign Methods
    public func fetchCampaigns() async throws -> [Campaign] {
        try await performRequest(endpoint: "/campaigns/")
    }

    public func fetchCampaign(id: Int) async throws -> Campaign {
        try await performRequest(endpoint: "/campaigns/\(id)")
    }

    public func createCampaign(_ campaignData: CampaignCreateDTO) async throws -> Campaign {
        let body = try jsonEncoder.encode(campaignData)
        return try await performRequest(endpoint: "/campaigns", method: "POST", body: body)
    }

    public func updateCampaign(_ campaignId: Int, data: CampaignUpdateDTO) async throws -> Campaign { // Changed campaignId from UUID to Int
        let body = try jsonEncoder.encode(data)
        return try await performRequest(endpoint: "/campaigns/\(campaignId)", method: "PUT", body: body) // REMOVED TRAILING SLASH
    }

    public func deleteCampaign(id: Int) async throws { // Changed id from UUID to Int
        try await performVoidRequest(endpoint: "/campaigns/\(id)", method: "DELETE") // Changed id.uuidString to id
    }

    // MARK: - Character Methods
    public func fetchCharacters() async throws -> [Character] {
        try await performRequest(endpoint: "/characters/") // ADDED TRAILING SLASH
    }

    public func fetchCharacter(id: Int) async throws -> Character {
        try await performRequest(endpoint: "/characters/\(id)")
    }

    public func createCharacter(_ characterData: CharacterCreateDTO) async throws -> Character {
        let body = try jsonEncoder.encode(characterData)
        return try await performRequest(endpoint: "/characters/", method: "POST", body: body)
    }

    public func updateCharacter(_ characterId: Int, data: CharacterUpdateDTO) async throws -> Character { // Changed characterId from UUID to Int
        let body = try jsonEncoder.encode(data)
        return try await performRequest(endpoint: "/characters/\(characterId)", method: "PUT", body: body) // Changed characterId.uuidString to characterId
    }

    public func deleteCharacter(id: Int) async throws { // Changed id from UUID to Int
        try await performVoidRequest(endpoint: "/characters/\(id)", method: "DELETE") // Changed id.uuidString to id
    }

    // MARK: - Auth Methods
    public func login(credentials: LoginRequestDTO) async throws -> LoginResponseDTO {
        var components = URLComponents()
        components.queryItems = [
            URLQueryItem(name: "username", value: credentials.username),
            URLQueryItem(name: "password", value: credentials.password)
        ]
        let bodyData = components.query?.data(using: .utf8)
        let headers = ["Content-Type": "application/x-www-form-urlencoded"]
        return try await performRequest(endpoint: "/auth/token", method: "POST", body: bodyData, headers: headers, requiresAuth: false)
    }

    // MARK: - User Methods
    public func getMe() async throws -> User {
        return try await performRequest(endpoint: "/users/me", requiresAuth: true)
    }

    // MARK: - Feature Methods
    public func fetchFeatures() async throws -> [Feature] {
        try await performRequest(endpoint: "/features/") // Assuming endpoint is /api/v1/features/
    }

    // MARK: - Campaign Custom Section Methods (New)
    public func regenerateCampaignCustomSection(campaignId: Int, sectionId: Int, payload: SectionRegeneratePayload) async throws -> CampaignCustomSection { // sectionId changed to Int
        let body = try jsonEncoder.encode(payload)
        // The endpoint needs to be confirmed. Assuming a nested structure for custom sections.
        // e.g., /api/v1/campaigns/{campaign_id}/custom_sections/{section_id}/regenerate
        // Or if custom sections are part of the main campaign update, this might be different.
        // For now, assuming a dedicated regeneration endpoint for a custom section.
        // IMPORTANT: The actual endpoint path needs to be verified with the backend API documentation.
        // Using a placeholder endpoint structure for now.
        return try await performRequest(endpoint: "/campaigns/\(campaignId)/custom_sections/\(sectionId)/regenerate", method: "POST", body: body)
    }

    // MARK: - Image Generation Methods
    public func generateImage(payload: ImageGenerationParams) async throws -> ImageGenerationResponse {
        let body = try jsonEncoder.encode(payload)
        // Endpoint from web UI is /api/v1/images/generate
        return try await performRequest(endpoint: "/images/generate", method: "POST", body: body)
    }

    // MARK: - Chat Message Methods
    // The saveChatMessage method has been removed as it's obsolete.
    // Message persistence is handled by the /generate-response endpoint.

    public func getChatHistory(characterId: Int, skip: Int? = nil, limit: Int? = nil) async throws -> [APIChatMessage] {
        var queryItems: [URLQueryItem] = []
        if let skip = skip {
            queryItems.append(URLQueryItem(name: "skip", value: String(skip)))
        }
        if let limit = limit {
            queryItems.append(URLQueryItem(name: "limit", value: String(limit)))
        }

        var endpointString = "/characters/\(characterId)/chat"
        if !queryItems.isEmpty {
            var components = URLComponents()
            components.queryItems = queryItems
            if let query = components.query {
                endpointString += "?\(query)"
            }
        }
        // performRequest handles adding the base URL
        let data: Data = try await performRequest(endpoint: endpointString, method: "GET")
        return try self.jsonDecoder.decode([APIChatMessage].self, from: data)
    }

    // New method for POST /characters/{character_id}/generate-response
    public func generateCharacterChatResponse(
        characterId: Int,
        prompt: String,
        chatHistory: [ChatMessageData]?, // ChatMessageData is {speaker: String, text: String}
        modelIdWithPrefix: String?,
        temperature: Double?,
        maxTokens: Int?
    ) async throws -> LLMTextResponseDTO { // Returns the new DTO

        // Construct the payload using the new struct
        let payload = LLMGenerationRequestPayload(
            prompt: prompt,
            chatHistory: chatHistory,
            modelIdWithPrefix: modelIdWithPrefix,
            temperature: temperature,
            maxTokens: maxTokens
        )
        // Note: 'character_notes' are now handled by the backend by combining memory_summary and base notes.
        // The client does not send character_notes directly for this endpoint anymore.

        let body = try jsonEncoder.encode(payload) // Encode the struct

        return try await performRequest(
            endpoint: "/characters/\(characterId)/generate-response",
            method: "POST",
            body: body
        )
    }

    // MARK: - LLM Methods
    public func fetchAvailableLLMs() async throws -> [AvailableLLM] {
        // The web app calls /api/v1/llm/models. baseURLString already includes /api/v1
        // The response structure is { "models": [AvailableLLM] }
        // We need to decode LLMModelsResponse first, then return its models property.
        // This endpoint requires authentication, contrary to previous comments.
        let response: LLMModelsResponse = try await performRequest(endpoint: "/llm/models", requiresAuth: true)
        return response.models
    }

    // MARK: - Memory Summary Methods
    public func getMemorySummary(characterId: Int) async throws -> String {
        let endpointString = "/characters/\(characterId)/memory-summary"
        let response: MemorySummaryDTO = try await performRequest(endpoint: endpointString, method: "GET")
        return response.memorySummary
    }

    public func clearChatHistory(characterId: Int) async throws {
        let endpointString = "/characters/\(characterId)/chat"
        try await performVoidRequest(endpoint: endpointString, method: "DELETE")
    }
}

public struct MemorySummaryDTO: Codable {
    public let memorySummary: String
}
