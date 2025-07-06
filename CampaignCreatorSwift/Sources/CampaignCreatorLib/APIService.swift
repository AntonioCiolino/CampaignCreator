import Foundation

// Error enum for API related issues
enum APIError: Error, LocalizedError {
    case invalidURL
    case requestFailed(Error)
    case decodingFailed(Error)
    case encodingFailed(Error)
    case serverError(statusCode: Int, data: Data?)
    case noData
    case notAuthenticated
    case custom(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The API endpoint URL was invalid."
        case .requestFailed(let error):
            return "The network request failed: \(error.localizedDescription)"
        case .decodingFailed(let error):
            var detailedError = "Failed to decode the server response."
            if let decodingError = error as? DecodingError {
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
}

// DTOs for Campaign operations
struct CampaignCreateDTO: Codable {
    var title: String
    var initialUserPrompt: String?
    // Add other relevant fields from CampaignCreatePayload in TypeScript
}

struct CampaignUpdateDTO: Codable {
    var title: String?
    var initialUserPrompt: String?
    var concept: String?
    var displayTOC: [TOCEntry]?
    var badgeImageURL: String?
    var thematicImageURL: String?
    var thematicImagePrompt: String?
    var selectedLLMId: String?
    var temperature: Double?
    var moodBoardImageURLs: [String]?
    var themePrimaryColor: String?
    var themeSecondaryColor: String?
    var themeBackgroundColor: String?
    var themeTextColor: String?
    var themeFontFamily: String?
    var themeBackgroundImageURL: String?
    var themeBackgroundImageOpacity: Double?
    var linkedCharacterIDs: [UUID]?
}

// DTOs for Character operations
struct CharacterCreateDTO: Codable {
    var name: String
    var description: String? // Ensure this matches `characterDescription` in the Character model if that's the internal name
    var appearanceDescription: String?
    var imageURLs: [String]?
    var notesForLLM: String?
    var stats: CharacterStats? // CharacterStats is already Codable
    var exportFormatPreference: String?
    // `owner_id` is usually set by the backend based on the authenticated user
}

struct CharacterUpdateDTO: Codable {
    var name: String?
    var description: String?
    var appearanceDescription: String?
    var imageURLs: [String]?
    var notesForLLM: String?
    var stats: CharacterStats?
    var exportFormatPreference: String?
}


// Simple protocol for token management
protocol TokenManaging {
    func getToken() -> String?
    func setToken(_ token: String?)
    func clearToken()
}

class UserDefaultsTokenManager: TokenManaging {
    private let tokenKey = "AuthToken"
    func getToken() -> String? { UserDefaults.standard.string(forKey: tokenKey) }
    func setToken(_ token: String?) {
        if let token = token { UserDefaults.standard.set(token, forKey: tokenKey) }
        else { UserDefaults.standard.removeObject(forKey: tokenKey) }
    }
    func clearToken() { UserDefaults.standard.removeObject(forKey: tokenKey) }
}


class APIService {
    private let baseURLString = "http://localhost:8000/api/v1"
    private var tokenManager: TokenManaging
    private let jsonDecoder: JSONDecoder
    private let jsonEncoder: JSONEncoder

    init(tokenManager: TokenManaging = UserDefaultsTokenManager()) {
        self.tokenManager = tokenManager
        jsonDecoder = JSONDecoder()
        jsonDecoder.dateDecodingStrategy = .iso8601
        // For Character model, ensure 'description' field in JSON maps to 'characterDescription' if that's the Swift property name.
        // If they differ, a custom CodingKeys or manual decoding/encoding might be needed for Character,
        // or ensure the Swift Character model's property name matches the JSON key.
        // For now, assuming Character.swift uses 'description' for the property that maps to JSON 'description'.
        // If Character.swift uses 'characterDescription', this might need adjustment in Character's Codable conformance or here.
        // Let's assume Character struct's 'description' property is what we mean.

        jsonEncoder = JSONEncoder()
        jsonEncoder.dateEncodingStrategy = .iso8601
        jsonEncoder.outputFormatting = .prettyPrinted
    }

    func updateAuthToken(_ token: String?) {
        tokenManager.setToken(token)
    }

    private func performRequest<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil,
        requiresAuth: Bool = true
    ) async throws -> T {
        guard let url = URL(string: baseURLString + endpoint) else { throw APIError.invalidURL }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.httpBody = body
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        if requiresAuth {
            guard let token = tokenManager.getToken() else { throw APIError.notAuthenticated }
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
    func fetchCampaigns() async throws -> [Campaign] {
        try await performRequest(endpoint: "/campaigns/")
    }

    func fetchCampaign(id: UUID) async throws -> Campaign {
        try await performRequest(endpoint: "/campaigns/\(id.uuidString)/")
    }

    func createCampaign(_ campaignData: CampaignCreateDTO) async throws -> Campaign {
        let body = try jsonEncoder.encode(campaignData)
        return try await performRequest(endpoint: "/campaigns/", method: "POST", body: body)
    }

    func updateCampaign(_ campaignId: UUID, data: CampaignUpdateDTO) async throws -> Campaign {
        let body = try jsonEncoder.encode(data)
        return try await performRequest(endpoint: "/campaigns/\(campaignId.uuidString)/", method: "PATCH", body: body)
    }

    func deleteCampaign(id: UUID) async throws {
        try await performVoidRequest(endpoint: "/campaigns/\(id.uuidString)/", method: "DELETE")
    }

    // MARK: - Character Methods
    func fetchCharacters() async throws -> [Character] {
        try await performRequest(endpoint: "/characters/")
    }

    func fetchCharacter(id: UUID) async throws -> Character {
        try await performRequest(endpoint: "/characters/\(id.uuidString)/")
    }

    func createCharacter(_ characterData: CharacterCreateDTO) async throws -> Character {
        let body = try jsonEncoder.encode(characterData)
        return try await performRequest(endpoint: "/characters/", method: "POST", body: body)
    }

    func updateCharacter(_ characterId: UUID, data: CharacterUpdateDTO) async throws -> Character {
        let body = try jsonEncoder.encode(data)
        return try await performRequest(endpoint: "/characters/\(characterId.uuidString)/", method: "PATCH", body: body)
    }

    func deleteCharacter(id: UUID) async throws {
        try await performVoidRequest(endpoint: "/characters/\(id.uuidString)/", method: "DELETE")
    }

    // MARK: - Auth Methods (Placeholders)
    // func login(credentials: LoginCredentials) async throws -> AuthResponse
    // func logout() async throws
}
