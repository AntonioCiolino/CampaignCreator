import Foundation

class GeminiClient: LLMService {
    private let apiKey: String
    private let session: URLSession
    private let modelName: String = "gemini-1.5-flash" // Or "gemini-pro" if preferred

    private var apiURL: URL? {
        return URL(string: "https://generativelanguage.googleapis.com/v1beta/models/\(modelName):generateContent?key=\(apiKey)")
    }

    init() {
        self.apiKey = Secrets.geminiAPIKey
        self.session = URLSession(configuration: .default)
    }

    func generateCompletion(prompt: String, completionHandler: @escaping (Result<String, LLMError>) -> Void) {
        if apiKey.isEmpty || apiKey == "YOUR_GEMINI_API_KEY" {
            completionHandler(.failure(.apiKeyMissing))
            return
        }

        guard let url = apiURL else {
            completionHandler(.failure(.invalidURL))
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Default temperature for original generateCompletion method
        performGeminiCompletion(prompt: prompt, temperature: nil, completionHandler: completionHandler)
    }

    // Centralized method for making Gemini API calls
    private func performGeminiCompletion(prompt: String, temperature: Float?, completionHandler: @escaping (Result<String, LLMError>) -> Void) {
        if apiKey.isEmpty || apiKey == "YOUR_GEMINI_API_KEY" {
            completionHandler(.failure(.apiKeyMissing))
            return
        }

        guard let url = apiURL else {
            completionHandler(.failure(.invalidURL))
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let requestPart = GeminiRequestContentPart(text: prompt)
        let requestContent = GeminiRequestContent(parts: [requestPart])
        var generationConfig: GeminiGenerationConfig? = nil
        if let temp = temperature {
            generationConfig = GeminiGenerationConfig(temperature: temp)
        }
        
        let geminiRequest = GeminiRequest(contents: [requestContent], generationConfig: generationConfig)

        do {
            let jsonData = try JSONEncoder().encode(geminiRequest)
            request.httpBody = jsonData
        } catch {
            completionHandler(.failure(.other(message: "Failed to encode Gemini request body: \(error.localizedDescription)")))
            return
        }

        let task = session.dataTask(with: request) { data, response, error in
            if let error = error {
                completionHandler(.failure(.requestFailed(underlyingError: error)))
                return
            }

            guard let httpResponse = response as? HTTPURLResponse else {
                completionHandler(.failure(.other(message: "Invalid response received from Gemini server.")))
                return
            }
            
            guard let data = data else {
                completionHandler(.failure(.noCompletionGenerated))
                return
            }

            // It's useful to log the raw response string for debugging, especially with new APIs
            // if let rawResponseString = String(data: data, encoding: .utf8) {
            //      print("Gemini Raw Response: \(rawResponseString)")
            // }


            guard (200...299).contains(httpResponse.statusCode) else {
                var responseBodyString: String? = nil
                if let data = data {
                    responseBodyString = String(data: data, encoding: .utf8)
                }
                completionHandler(.failure(.unexpectedStatusCode(statusCode: httpResponse.statusCode, responseBody: responseBodyString)))
                return
            }


            do {
                let geminiResponse = try JSONDecoder().decode(GeminiResponse.self, from: data)
                
                if let firstCandidate = geminiResponse.candidates?.first {
                    if let firstPart = firstCandidate.content?.parts?.first, let text = firstPart.text {
                        completionHandler(.success(text))
                    } else if firstCandidate.finishReason != nil && (firstCandidate.content?.parts == nil || firstCandidate.content?.parts?.isEmpty == true) {
                        let reason = firstCandidate.finishReason ?? "Unknown reason"
                        let safetyCategories = firstCandidate.safetyRatings?.map { "\($0.category): \($0.probability)" }.joined(separator: ", ") ?? "N/A"
                        completionHandler(.failure(.other(message: "Content generation finished with reason: \(reason). Safety: \(safetyCategories). No text parts available.")))
                    } else {
                        completionHandler(.failure(.noCompletionGenerated))
                    }
                } else if let promptFeedback = geminiResponse.promptFeedback, 
                          let blockReason = promptFeedback.blockReason { // Check for direct prompt block
                    let safetyCategories = promptFeedback.safetyRatings?.map { "\($0.category): \($0.probability)" }.joined(separator: ", ") ?? "N/A"
                    completionHandler(.failure(.other(message: "Prompt blocked due to reason: \(blockReason). Safety: \(safetyCategories)")))
                } else if let promptFeedback = geminiResponse.promptFeedback, promptFeedback.safetyRatings?.contains(where: { $0.probability != "NEGLIGIBLE" && $0.probability != "LOW" }) == true {
                     let safetyCategories = promptFeedback.safetyRatings?.map { "\($0.category): \($0.probability)" }.joined(separator: ", ") ?? "N/A"
                     completionHandler(.failure(.other(message: "Prompt blocked due to safety ratings. Details: \(safetyCategories)")))
                }
                else {
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
        performGeminiCompletion(prompt: prompt, temperature: 0.4, completionHandler: completionHandler)
    }

    func generateTableOfContents(campaignText: String, completionHandler: @escaping (Result<String, LLMError>) -> Void) {
        let prompt = String(format: PromptLibrary.generateTableOfContents, campaignText)
        performGeminiCompletion(prompt: prompt, temperature: 0.13, completionHandler: completionHandler)
    }

    func generateCampaignTitles(campaignConcept: String, completionHandler: @escaping (Result<[String], LLMError>) -> Void) {
        let prompt = String(format: PromptLibrary.generateCampaignTitles, campaignConcept)
        performGeminiCompletion(prompt: prompt, temperature: 0.5) { result in
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
        performGeminiCompletion(prompt: prompt, temperature: Float(temperature), completionHandler: completionHandler)
    }

    func generateImage(prompt: String, size: String, completionHandler: @escaping (Result<URL, LLMError>) -> Void) {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { // Minimal delay
            completionHandler(.failure(.other(message: "Image generation not supported by GeminiClient.")))
        }
    }
}
