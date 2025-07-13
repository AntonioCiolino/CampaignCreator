import Foundation

// Error enum for API related issues
public enum APIError: Error, LocalizedError, Sendable, Equatable {
    case invalidURL
    case requestFailed(Error)
    case decodingFailed(Error)
    case encodingFailed(Error)
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

    public static func == (lhs: APIError, rhs: APIError) -> Bool {
        switch (lhs, rhs) {
        case (.invalidURL, .invalidURL): return true
        case (.requestFailed(_), .requestFailed(_)): return true
        case (.decodingFailed(_), .decodingFailed(_)): return true
        case (.encodingFailed(_), .encodingFailed(_)): return true
        case (let .serverError(sc1, data1), let .serverError(sc2, data2)): return sc1 == sc2 && data1 == data2
        case (.noData, .noData): return true
        case (.notAuthenticated, .notAuthenticated): return true
        case (let .custom(s1), let .custom(s2)): return s1 == s2
        default: return false
        }
    }
}

public final class APIService: Sendable {
    public let baseURLString = "https://campaigncreator-api.onrender.com/api/v1"
    private let tokenManager: TokenManaging = UserDefaultsTokenManager()
    private let jsonDecoder: JSONDecoder
    private let jsonEncoder: JSONEncoder

    public init() {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .formatted(JSONDecoder.iso8601withFractionalSeconds)
        self.jsonDecoder = decoder

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = .prettyPrinted
        self.jsonEncoder = encoder
    }

    public func performRequest<T: Decodable>(
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
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.setValue("app://com.campaigncreator.app", forHTTPHeaderField: "Origin")

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
            guard let token = tokenManager.getToken() else {
                throw APIError.notAuthenticated
            }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else { throw APIError.requestFailed(URLError(.badServerResponse)) }

            if httpResponse.statusCode == 401 { throw APIError.notAuthenticated }
            guard (200...299).contains(httpResponse.statusCode) else { throw APIError.serverError(statusCode: httpResponse.statusCode, data: data) }

            if T.self == Data.self { return data as! T }
            if data.isEmpty {
                if let voidValue = () as? T { return voidValue }
                else if let optionalNil = Optional<Any>.none as? T { return optionalNil }
            }

            do {
                let decodedObject = try self.jsonDecoder.decode(T.self, from: data)
                return decodedObject
            } catch {
                throw APIError.decodingFailed(error)
            }
        } catch let error as APIError { throw error }
        catch { throw APIError.requestFailed(error) }
    }

    public func performVoidRequest(
        endpoint: String,
        method: String = "DELETE",
        body: Data? = nil,
        requiresAuth: Bool = true
    ) async throws {
        guard let url = URL(string: baseURLString + endpoint) else { throw APIError.invalidURL }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.httpBody = body
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.setValue("app://com.campaigncreator.app", forHTTPHeaderField: "Origin")
        if method != "GET" && method != "HEAD" { request.setValue("application/json", forHTTPHeaderField: "Content-Type") }

        if requiresAuth {
            guard let token = tokenManager.getToken() else { throw APIError.notAuthenticated }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else { throw APIError.requestFailed(URLError(.badServerResponse)) }
            if httpResponse.statusCode == 401 { throw APIError.notAuthenticated }
            guard (200...299).contains(httpResponse.statusCode) else { throw APIError.serverError(statusCode: httpResponse.statusCode, data: data) }
        } catch let error as APIError { throw error }
        catch { throw APIError.requestFailed(error) }
    }
}

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

public extension JSONDecoder.DateDecodingStrategy {
    static let iso8601withFractionalSeconds = custom {
        let container = try $0.singleValueContainer()
        let string = try container.decode(String.self)
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: string) {
            return date
        }
        formatter.formatOptions = [.withInternetDateTime]
        if let date = formatter.date(from: string) {
            return date
        }
        throw DecodingError.dataCorruptedError(in: container, debugDescription: "Invalid date: \(string)")
    }
}
