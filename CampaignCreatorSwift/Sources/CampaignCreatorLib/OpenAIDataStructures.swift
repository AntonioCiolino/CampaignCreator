import Foundation

// MARK: - Request Structures

public struct OpenAIRequest: Codable {
    public let model: String
    public let messages: [OpenAIMessage]
    public let temperature: Double?
    // Add other parameters like max_tokens, top_p, etc., as needed.

    public init(model: String = "gpt-3.5-turbo", messages: [OpenAIMessage], temperature: Double? = 0.7) {
        self.model = model
        self.messages = messages
        self.temperature = temperature
    }
}

public struct OpenAIMessage: Codable {
    public let role: String // "system", "user", or "assistant"
    public let content: String
    
    public init(role: String, content: String) {
        self.role = role
        self.content = content
    }
}

// MARK: - Response Structures

public struct OpenAIResponse: Codable {
    public let id: String?
    public let object: String?
    public let created: Int?
    public let model: String?
    public let choices: [OpenAIChoice]
    public let usage: OpenAIUsage?
    public let systemFingerprint: String? // Optional, as it might not always be present

    enum CodingKeys: String, CodingKey {
        case id, object, created, model, choices, usage
        case systemFingerprint = "system_fingerprint"
    }
}

public struct OpenAIChoice: Codable {
    public let index: Int?
    public let message: OpenAIMessage
    public let finishReason: String?

    enum CodingKeys: String, CodingKey {
        case index, message
        case finishReason = "finish_reason"
    }
}

public struct OpenAIUsage: Codable {
    public let promptTokens: Int?
    public let completionTokens: Int?
    public let totalTokens: Int?

    enum CodingKeys: String, CodingKey {
        case promptTokens = "prompt_tokens"
        case completionTokens = "completion_tokens"
        case totalTokens = "total_tokens"
    }
}