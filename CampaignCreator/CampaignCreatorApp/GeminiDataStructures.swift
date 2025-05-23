import Foundation

// MARK: - Gemini API Request Structures

struct GeminiRequest: Codable {
    let contents: [GeminiRequestContent]
    // Add other parameters like generationConfig, safetySettings if needed.
}

struct GeminiRequestContent: Codable {
    let parts: [GeminiRequestContentPart]
    // let role: String? // Optional: "user" or "model", defaults to "user" if not specified for the first content.
}

struct GeminiRequestContentPart: Codable {
    let text: String
}

// MARK: - Gemini API Response Structures

struct GeminiResponse: Codable {
    let candidates: [GeminiResponseCandidate]?
    let promptFeedback: GeminiPromptFeedback?
}

struct GeminiResponseCandidate: Codable {
    let content: GeminiResponseCandidateContent?
    let finishReason: String?
    let index: Int?
    let safetyRatings: [GeminiSafetyRating]?
}

struct GeminiResponseCandidateContent: Codable {
    let parts: [GeminiResponseCandidatePart]?
    let role: String? // Typically "model"
}

struct GeminiResponseCandidatePart: Codable {
    let text: String? // Text can be optional or empty if the model outputs something else or is blocked.
}

struct GeminiPromptFeedback: Codable {
    let safetyRatings: [GeminiSafetyRating]?
    // Add blockReason if needed:
    // let blockReason: String?
    // enum CodingKeys: String, CodingKey {
    //    case blockReason
    //    case safetyRatings
    // }
}

struct GeminiSafetyRating: Codable {
    let category: String
    let probability: String // e.g., "NEGLIGIBLE", "LOW", "MEDIUM", "HIGH"
}


// Example of creating a simple Gemini request:
// let userPromptPart = GeminiRequestContentPart(text: "Explain quantum physics in simple terms.")
// let userContent = GeminiRequestContent(parts: [userPromptPart])
// let geminiRequest = GeminiRequest(contents: [userContent])
//
// To encode:
// let encoder = JSONEncoder()
// let jsonData = try? encoder.encode(geminiRequest)
//
// To decode a response:
// let decoder = JSONDecoder()
// if let data = responseData {
//     let response = try? decoder.decode(GeminiResponse.self, from: data)
//     if let completionText = response?.candidates?.first?.content?.parts?.first?.text {
//         print(completionText)
//     }
// }
