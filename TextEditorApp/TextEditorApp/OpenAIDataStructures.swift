import Foundation

// MARK: - Request Structures

struct OpenAIRequest: Codable {
    let model: String
    let messages: [OpenAIMessage]
    let temperature: Double?
    // Add other parameters like max_tokens, top_p, etc., as needed.

    init(model: String = "gpt-3.5-turbo", messages: [OpenAIMessage], temperature: Double? = 0.7) {
        self.model = model
        self.messages = messages
        self.temperature = temperature
    }
}

struct OpenAIMessage: Codable {
    let role: String // "system", "user", or "assistant"
    let content: String
}

// MARK: - Response Structures

struct OpenAIResponse: Codable {
    let id: String?
    let object: String?
    let created: Int?
    let model: String?
    let choices: [OpenAIChoice]
    let usage: OpenAIUsage?
    let systemFingerprint: String? // Optional, as it might not always be present

    enum CodingKeys: String, CodingKey {
        case id, object, created, model, choices, usage
        case systemFingerprint = "system_fingerprint"
    }
}

struct OpenAIChoice: Codable {
    let index: Int?
    let message: OpenAIMessage
    let finishReason: String?

    enum CodingKeys: String, CodingKey {
        case index, message
        case finishReason = "finish_reason"
    }
}

struct OpenAIUsage: Codable {
    let promptTokens: Int?
    let completionTokens: Int?
    let totalTokens: Int?

    enum CodingKeys: String, CodingKey {
        case promptTokens = "prompt_tokens"
        case completionTokens = "completion_tokens"
        case totalTokens = "total_tokens"
    }
}

// Example of creating a simple request:
// let userMessage = OpenAIMessage(role: "user", content: "Hello, world!")
// let request = OpenAIRequest(messages: [userMessage])
//
// To encode:
// let encoder = JSONEncoder()
// let jsonData = try? encoder.encode(request)
//
// To decode a response:
// let decoder = JSONDecoder()
// let response = try? decoder.decode(OpenAIResponse.self, from: data)
// if let completionText = response?.choices.first?.message.content {
//     print(completionText)
// }
