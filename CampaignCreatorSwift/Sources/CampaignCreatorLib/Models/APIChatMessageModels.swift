import Foundation

// APIChatMessageCreate is likely obsolete with the new generate-response flow.
// Commenting out for now. If a specific "create single message" API is ever re-added,
// this would need to align with its payload.
/*
public struct APIChatMessageCreate: Codable, Sendable {
    public let text: String
    public let sender: String // "user" or character name for LLM

    public init(text: String, sender: String) {
        self.text = text
        self.sender = sender
    }
}
*/

// This struct now represents an entry in the conversation history JSON array.
// It's what GET /chat returns as a list.
public struct APIChatMessage: Codable, Sendable, Identifiable {
    public let speaker: String
    public let text: String
    public let timestamp: Date

    // Computed id for Identifiable conformance, NOT decoded from JSON.
    public var id: String {
        return "\(timestamp.timeIntervalSince1970)-\(speaker)-\(text.prefix(50).hashValue)"
    }
}

// DTO for the response from the /generate-response endpoint
public struct LLMTextResponseDTO: Codable, Sendable {
    public let text: String
    public let modelUsed: String?

    enum CodingKeys: String, CodingKey {
        case text
        case modelUsed = "model_used"
    }
}
