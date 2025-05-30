import Foundation

class OpenAIClient: LLMService {
    private let apiKey: String
    private let session: URLSession

    private static let openAIAPIURL = "https://api.openai.com/v1/chat/completions"

    init() {
        self.apiKey = Secrets.openAIAPIKey
        self.session = URLSession(configuration: .default)
    }

    func generateCompletion(prompt: String, completionHandler: @escaping (Result<String, LLMError>) -> Void) {
        if apiKey.isEmpty || apiKey == "YOUR_OPENAI_API_KEY" {
            completionHandler(.failure(.apiKeyMissing))
            return
        }

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
                completionHandler(.failure(.noCompletionGenerated)) // Or a more specific error like .emptyDataResponse
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
