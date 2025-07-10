import Foundation

public struct APIChatMessageCreate: Codable, Sendable {
    public let text: String
    public let sender: String // "user" or character name for LLM

    public init(text: String, sender: String) {
        self.text = text
        self.sender = sender
    }
}

public struct APIChatMessage: Codable, Sendable, Identifiable { // Add Identifiable
    public let id: Int
    public let characterId: Int
    public let text: String
    public let sender: String
    public let timestamp: Date // Assuming ISO8601, decoder will handle

    public init(id: Int, characterId: Int, text: String, sender: String, timestamp: Date) {
        self.id = id
        self.characterId = characterId
        self.text = text
        self.sender = sender
        self.timestamp = timestamp
    }

    // CodingKeys to map character_id from snake_case if jsonDecoder isn't globally set to convertFromSnakeCase
    // However, APIService's jsonDecoder IS set to .convertFromSnakeCase, so this might not be strictly necessary
    // but doesn't hurt for clarity or if this model is decoded elsewhere without that setting.
    enum CodingKeys: String, CodingKey {
        case id
        case characterId = "character_id"
        case text
        case sender
        case timestamp
    }
}
