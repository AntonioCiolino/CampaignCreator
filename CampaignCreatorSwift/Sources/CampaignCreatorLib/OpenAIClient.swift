import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

public class OpenAIClient: LLMService {
    private let apiKey: String
    private let session: URLSession

    private static let openAIAPIURL = "https://api.openai.com/v1/chat/completions"

    public init() throws {
        let retrievedApiKey = SecretsManager.shared.openAIAPIKey
        print("[API_KEY_DEBUG OpenAIClient] init: Attempting to initialize. Retrieved API key from SecretsManager: '\(retrievedApiKey ?? "nil")'")

        // The isValidKey check here is somewhat redundant if SecretsManager.openAIAPIKey already filters,
        // but it provides an explicit check point.
        guard let apiKey = retrievedApiKey, SecretsManager.shared.isValidKey(apiKey) else {
            print("[API_KEY_DEBUG OpenAIClient] init: API key is nil or invalid after retrieval. Throwing apiKeyMissing.")
            throw LLMError.apiKeyMissing
        }
        self.apiKey = apiKey
        print("[API_KEY_DEBUG OpenAIClient] init: Successfully initialized with valid API key.")
        self.session = URLSession(configuration: .default)
    }

    public func generateCompletion(prompt: String, completionHandler: @escaping @Sendable (Result<String, LLMError>) -> Void) {
        print("[API_KEY_DEBUG OpenAIClient] generateCompletion: Using API Key: '\(apiKey.prefix(5))...\(apiKey.suffix(4))'") // Log sanitized key
        guard let url = URL(string: Self.openAIAPIURL) else {
            completionHandler(.failure(.invalidURL))
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let messages = [OpenAIMessage(role: "user", content: prompt)]
        let openAIRequest = OpenAIRequest(messages: messages)

        do {
            let jsonData = try JSONEncoder().encode(openAIRequest)
            request.httpBody = jsonData
        } catch {
            completionHandler(.failure(.other(message: "Failed to encode request body: \(error.localizedDescription)")))
            return
        }

        let task = session.dataTask(with: request) { data, response, error in
            if let error = error {
                completionHandler(.failure(.requestFailed(underlyingError: error)))
                return
            }

            guard let httpResponse = response as? HTTPURLResponse else {
                completionHandler(.failure(.other(message: "Invalid response received from server.")))
                return
            }

            guard (200...299).contains(httpResponse.statusCode) else {
                var responseBodyString: String? = nil
                if let data = data {
                    responseBodyString = String(data: data, encoding: .utf8)
                }
                completionHandler(.failure(.unexpectedStatusCode(statusCode: httpResponse.statusCode, responseBody: responseBodyString)))
                return
            }

            guard let data = data else {
                completionHandler(.failure(.noCompletionGenerated))
                return
            }

            do {
                let openAIResponse = try JSONDecoder().decode(OpenAIResponse.self, from: data)
                if let firstChoice = openAIResponse.choices.first {
                    let completionText = firstChoice.message.content
                    completionHandler(.success(completionText))
                } else {
                    completionHandler(.failure(.noCompletionGenerated))
                }
            } catch {
                completionHandler(.failure(.decodingError(underlyingError: error)))
            }
        }
        task.resume()
    }
}