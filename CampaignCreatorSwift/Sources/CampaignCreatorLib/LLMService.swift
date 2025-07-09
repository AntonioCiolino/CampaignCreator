import Foundation

public enum LLMError: Error, LocalizedError, Equatable { // Added Equatable
    case apiKeyMissing
    case invalidURL
    case requestFailed(underlyingError: Error)
    case unexpectedStatusCode(statusCode: Int, responseBody: String?)
    case decodingError(underlyingError: Error)
    case noCompletionGenerated
    case other(message: String)

    public var errorDescription: String? {
        switch self {
        case .apiKeyMissing:
            return "API key is missing. Please provide it via environment variable."
        case .invalidURL:
            return "The API URL is invalid."
        case .requestFailed(let underlyingError):
            return "The network request failed: \(underlyingError.localizedDescription)"
        case .unexpectedStatusCode(let statusCode, let responseBody):
            var message = "Received an unexpected status code: \(statusCode)."
            if let body = responseBody, !body.isEmpty {
                message += " Response: \(body)"
            }
            return message
        case .decodingError(let underlyingError):
            return "Failed to decode the API response: \(underlyingError.localizedDescription)"
        case .noCompletionGenerated:
            return "The API did not return any completions."
        case .other(let message):
            return message
        }
    }

    // Equatable conformance
    public static func == (lhs: LLMError, rhs: LLMError) -> Bool {
        switch (lhs, rhs) {
        case (.apiKeyMissing, .apiKeyMissing):
            return true
        case (.invalidURL, .invalidURL):
            return true
        case (.requestFailed(let lhsError), .requestFailed(let rhsError)):
            // Comparing localizedDescription as Error itself is not Equatable
            return lhsError.localizedDescription == rhsError.localizedDescription
        case (.unexpectedStatusCode(let lhsCode, let lhsBody), .unexpectedStatusCode(let rhsCode, let rhsBody)):
            return lhsCode == rhsCode && lhsBody == rhsBody
        case (.decodingError(let lhsError), .decodingError(let rhsError)):
            return lhsError.localizedDescription == rhsError.localizedDescription
        case (.noCompletionGenerated, .noCompletionGenerated):
            return true
        case (.other(let lhsMessage), .other(let rhsMessage)):
            return lhsMessage == rhsMessage
        default:
            return false
        }
    }
}

public protocol LLMService {
    /// Generates a text completion for the given prompt.
    /// - Parameters:
    ///   - prompt: The text prompt to send to the LLM.
    ///   - completionHandler: A closure to be called with the result of the operation.
    ///     It returns a `Result` type, which is either a `String` containing the
    ///     generated completion, or an `LLMError` detailing what went wrong.
    func generateCompletion(prompt: String, completionHandler: @escaping @Sendable (Result<String, LLMError>) -> Void)
}

// MARK: - Async convenience methods
@available(macOS 10.15, iOS 13.0, tvOS 13.0, watchOS 6.0, *)
public extension LLMService {
    /// Generates a text completion for the given prompt asynchronously.
    func generateCompletion(prompt: String) async throws -> String {
        return try await withCheckedThrowingContinuation { continuation in
            generateCompletion(prompt: prompt) { result in
                continuation.resume(with: result)
            }
        }
    }
}