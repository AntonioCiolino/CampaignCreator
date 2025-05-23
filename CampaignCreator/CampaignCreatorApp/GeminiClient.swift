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

        let requestPart = GeminiRequestContentPart(text: prompt)
        let requestContent = GeminiRequestContent(parts: [requestPart])
        let geminiRequest = GeminiRequest(contents: [requestContent])

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
                completionHandler(.failure(.noCompletionGenerated)) // Or a more specific error like .emptyDataResponse
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
                
                // Check for safety blocks or missing candidates/parts
                if let firstCandidate = geminiResponse.candidates?.first {
                    if let firstPart = firstCandidate.content?.parts?.first, let text = firstPart.text {
                        completionHandler(.success(text))
                    } else if firstCandidate.finishReason != nil && firstCandidate.content?.parts == nil {
                        // This can happen if the content is blocked due to safety or other reasons
                        let reason = firstCandidate.finishReason ?? "Unknown reason"
                        let safetyCategories = firstCandidate.safetyRatings?.map { "\($0.category): \($0.probability)" }.joined(separator: ", ") ?? "N/A"
                        completionHandler(.failure(.noCompletionGenerated))
                        // More specific error:
                        // completionHandler(.failure(.other(message: "Content generation finished with reason: \(reason). Safety: \(safetyCategories) No text parts available.")))
                    } else {
                        completionHandler(.failure(.noCompletionGenerated))
                    }
                } else if let promptFeedback = geminiResponse.promptFeedback, promptFeedback.safetyRatings?.contains(where: { $0.probability != "NEGLIGIBLE" && $0.probability != "LOW" }) == true {
                     // Handle cases where the prompt itself might be blocked.
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
}
