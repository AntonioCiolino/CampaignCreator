import Foundation

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

    public init(title: String, initialUserPrompt: String? = nil) {
        self.title = title
        self.initialUserPrompt = initialUserPrompt
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
    public var linkedCharacterIDs: [UUID]?

    public init(title: String? = nil, initialUserPrompt: String? = nil, concept: String? = nil, displayTOC: [TOCEntry]? = nil, badgeImageURL: String? = nil, thematicImageURL: String? = nil, thematicImagePrompt: String? = nil, selectedLLMId: String? = nil, temperature: Double? = nil, moodBoardImageURLs: [String]? = nil, themePrimaryColor: String? = nil, themeSecondaryColor: String? = nil, themeBackgroundColor: String? = nil, themeTextColor: String? = nil, themeFontFamily: String? = nil, themeBackgroundImageURL: String? = nil, themeBackgroundImageOpacity: Double? = nil, linkedCharacterIDs: [UUID]? = nil) {
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

    public init(name: String, description: String? = nil, appearanceDescription: String? = nil, imageURLs: [String]? = nil, notesForLLM: String? = nil, stats: CharacterStats? = nil, exportFormatPreference: String? = nil) {
        self.name = name
        self.description = description
        self.appearanceDescription = appearanceDescription
        self.imageURLs = imageURLs
        self.notesForLLM = notesForLLM
        self.stats = stats
        self.exportFormatPreference = exportFormatPreference
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

    public init(name: String? = nil, description: String? = nil, appearanceDescription: String? = nil, imageURLs: [String]? = nil, notesForLLM: String? = nil, stats: CharacterStats? = nil, exportFormatPreference: String? = nil) {
        self.name = name
        self.description = description
        self.appearanceDescription = appearanceDescription
        self.imageURLs = imageURLs
        self.notesForLLM = notesForLLM
        self.stats = stats
        self.exportFormatPreference = exportFormatPreference
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
    public var access_token: String
    public var token_type: String

    public init(access_token: String, token_type: String) {
        self.access_token = access_token
        self.token_type = token_type
    }
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


public final class APIService: Sendable {
    private let baseURLString = "https://campaigncreator-api.onrender.com/api/v1"
    private let tokenManager: TokenManaging
    private let jsonDecoder: JSONDecoder
    private let jsonEncoder: JSONEncoder

    public init(tokenManager: TokenManaging = UserDefaultsTokenManager()) {
        self.tokenManager = tokenManager
        jsonDecoder = JSONDecoder()
        jsonDecoder.dateDecodingStrategy = .iso8601

        jsonEncoder = JSONEncoder()
        jsonEncoder.dateEncodingStrategy = .iso8601
        jsonEncoder.outputFormatting = .prettyPrinted
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
            do {
                return try jsonDecoder.decode(T.self, from: data)
            } catch {
                print("❌ Decoding failed for type \(T.self): \(error.localizedDescription)")
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
        if method != "GET" && method != "HEAD" { request.setValue("application/json", forHTTPHeaderField: "Content-Type") }

        if requiresAuth {
            guard let token = tokenManager.getToken() else { throw APIError.notAuthenticated }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

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

    public func fetchCampaign(id: Int) async throws -> Campaign { // Changed id from UUID to Int
        try await performRequest(endpoint: "/campaigns/\(id)/") // Changed id.uuidString to id
    }

    public func createCampaign(_ campaignData: CampaignCreateDTO) async throws -> Campaign {
        let body = try jsonEncoder.encode(campaignData)
        return try await performRequest(endpoint: "/campaigns/", method: "POST", body: body)
    }

    public func updateCampaign(_ campaignId: Int, data: CampaignUpdateDTO) async throws -> Campaign { // Changed campaignId from UUID to Int
        let body = try jsonEncoder.encode(data)
        return try await performRequest(endpoint: "/campaigns/\(campaignId)/", method: "PUT", body: body) // Changed campaignId.uuidString to campaignId
    }

    public func deleteCampaign(id: Int) async throws { // Changed id from UUID to Int
        try await performVoidRequest(endpoint: "/campaigns/\(id)/", method: "DELETE") // Changed id.uuidString to id
    }

    // MARK: - Character Methods
    public func fetchCharacters() async throws -> [Character] {
        try await performRequest(endpoint: "/characters/") // Removed trailing slash
    }

    public func fetchCharacter(id: Int) async throws -> Character { // Changed id from UUID to Int
        try await performRequest(endpoint: "/characters/\(id)/") // Changed id.uuidString to id
    }

    public func createCharacter(_ characterData: CharacterCreateDTO) async throws -> Character {
        let body = try jsonEncoder.encode(characterData)
        return try await performRequest(endpoint: "/characters/", method: "POST", body: body)
    }

    public func updateCharacter(_ characterId: Int, data: CharacterUpdateDTO) async throws -> Character { // Changed characterId from UUID to Int
        let body = try jsonEncoder.encode(data)
        return try await performRequest(endpoint: "/characters/\(characterId)/", method: "PUT", body: body) // Changed characterId.uuidString to characterId
    }

    public func deleteCharacter(id: Int) async throws { // Changed id from UUID to Int
        try await performVoidRequest(endpoint: "/characters/\(id)/", method: "DELETE") // Changed id.uuidString to id
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
}
