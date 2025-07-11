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
// It's what GET /chat returns as a list, and what's stored in the DB JSON.
public struct APIChatMessage: Codable, Sendable, Identifiable {
    public let speaker: String // "user" or "assistant" (or potentially character name if backend uses that for AI)
    public let text: String
    public let timestamp: Date // APIService's JSONDecoder handles ISO8601 string to Date

    // For Identifiable conformance in SwiftUI lists.
    // A more robust ID could be generated if needed, e.g., if timestamps aren't guaranteed unique enough
    // or if messages could be edited/deleted individually (not the current model).
    public var id: String {
        // Create a reasonably unique ID from timestamp and content hash.
        // Consider that text could be very long, hashing might be intensive.
        // For UI purposes, if the list order is stable, index-based or timestamp-based might be enough.
        return "\(timestamp.timeIntervalSince1970)-\(speaker)-\(text.prefix(50).hashValue)"
    }

    // No explicit CodingKeys needed if backend sends these field names (speaker, text, timestamp)
    // and APIService.jsonDecoder.keyDecodingStrategy = .convertFromSnakeCase is active
    // (though these are already camelCase or single word).
    // If backend sends, e.g., "speaker_role", then CodingKeys would be needed.
}

// DTO for the response from the /generate-response endpoint
public struct LLMTextResponseDTO: Codable, Sendable {
    public let text: String
    public let modelUsed: String? // Backend sends "model_used", maps due to .convertFromSnakeCase

    // If backend keys are exactly "text" and "modelUsed", no CodingKeys needed.
    // If backend sends "model_used", this will map correctly with .convertFromSnakeCase.
    enum CodingKeys: String, CodingKey {
        case text
        case modelUsed = "model_used" // Explicit mapping if needed, though convertFromSnakeCase should handle it
    }
}
