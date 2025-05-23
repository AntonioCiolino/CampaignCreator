import Foundation

class OpenAIClient: LLMService {
    private let apiKey: String
    private let session: URLSession

    private static let openAIChatAPIURL = "https://api.openai.com/v1/chat/completions"
    private static let openAIImageAPIURL = "https://api.openai.com/v1/images/generations"

    init() {
        self.apiKey = Secrets.openAIAPIKey
        self.session = URLSession(configuration: .default)
    }

    func generateCompletion(prompt: String, completionHandler: @escaping (Result<String, LLMError>) -> Void) {
        if apiKey.isEmpty || apiKey == "YOUR_OPENAI_API_KEY" {
            completionHandler(.failure(.apiKeyMissing))
            return
        }

        guard let url = URL(string: Self.openAIChatAPIURL) else {
            completionHandler(.failure(.invalidURL))
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let messages = [OpenAIMessage(role: "user", content: prompt)]
        // Default temperature for original generateCompletion method
        performOpenAICompletion(prompt: prompt, temperature: 0.7, completionHandler: completionHandler)
    }

    // Centralized method for making OpenAI API calls
    private func performOpenAICompletion(prompt: String, temperature: Double?, completionHandler: @escaping (Result<String, LLMError>) -> Void) {
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
        // Use the provided temperature, or nil if not specified (OpenAI will use its default)
        let openAIRequest = OpenAIRequest(messages: messages, temperature: temperature)

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

    func generateCampaignConcept(userInput: String, completionHandler: @escaping (Result<String, LLMError>) -> Void) {
        let prompt = String(format: PromptLibrary.generateCampaignConcept, userInput)
        performOpenAICompletion(prompt: prompt, temperature: 0.4, completionHandler: completionHandler)
    }

    func generateTableOfContents(campaignText: String, completionHandler: @escaping (Result<String, LLMError>) -> Void) {
        let prompt = String(format: PromptLibrary.generateTableOfContents, campaignText)
        performOpenAICompletion(prompt: prompt, temperature: 0.13, completionHandler: completionHandler)
    }

    func generateCampaignTitles(campaignConcept: String, completionHandler: @escaping (Result<[String], LLMError>) -> Void) {
        let prompt = String(format: PromptLibrary.generateCampaignTitles, campaignConcept)
        performOpenAICompletion(prompt: prompt, temperature: 0.5) { result in
            switch result {
            case .success(let rawText):
                let titles = rawText.split(separator: "\n").map { String($0).trimmingCharacters(in: .whitespacesAndNewlines) }.filter { !$0.isEmpty && $0.count >= 3 }
                completionHandler(.success(titles))
            case .failure(let error):
                completionHandler(.failure(error))
            }
        }
    }

    func continueWritingSection(campaignText: String, tocText: String, currentChapterText: String, temperature: Double, completionHandler: @escaping (Result<String, LLMError>) -> Void) {
        let prompt = String(format: PromptLibrary.continueSection, campaignText, tocText, currentChapterText)
        performOpenAICompletion(prompt: prompt, temperature: temperature, completionHandler: completionHandler)
    }

    func generateImage(prompt: String, size: String = "256x256", completionHandler: @escaping (Result<URL, LLMError>) -> Void) {
        if apiKey.isEmpty || apiKey == "YOUR_OPENAI_API_KEY" {
            completionHandler(.failure(.apiKeyMissing))
            return
        }

        guard let url = URL(string: Self.openAIImageAPIURL) else {
            completionHandler(.failure(.invalidURL))
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let imageRequest = OpenAIImageGenerationRequest(prompt: prompt, n: 1, size: size)

        do {
            let jsonData = try JSONEncoder().encode(imageRequest)
            request.httpBody = jsonData
        } catch {
            completionHandler(.failure(.other(message: "Failed to encode image generation request body: \(error.localizedDescription)")))
            return
        }

        let task = session.dataTask(with: request) { data, response, error in
            if let error = error {
                completionHandler(.failure(.requestFailed(underlyingError: error)))
                return
            }

            guard let httpResponse = response as? HTTPURLResponse else {
                completionHandler(.failure(.other(message: "Invalid response received from image generation server.")))
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
                completionHandler(.failure(.noCompletionGenerated)) // Or more specific: .noImageDataReceived
                return
            }

            do {
                let imageResponse = try JSONDecoder().decode(OpenAIImageGenerationResponse.self, from: data)
                if let firstImageData = imageResponse.data.first, let imageUrl = firstImageData.url {
                    completionHandler(.success(imageUrl))
                } else {
                    completionHandler(.failure(.noCompletionGenerated)) // Or more specific: .noImageURLInResponse
                }
            } catch {
                completionHandler(.failure(.decodingError(underlyingError: error)))
            }
        }
        task.resume()
    }
}
