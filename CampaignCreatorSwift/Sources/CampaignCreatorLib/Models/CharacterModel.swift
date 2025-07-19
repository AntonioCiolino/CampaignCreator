import Foundation

// Corresponds to TypeScript 'CharacterStats'
public struct CharacterStats: Codable, Sendable {
    public var strength: Int?
    public var dexterity: Int?
    public var constitution: Int?
    public var intelligence: Int?
    public var wisdom: Int?
    public var charisma: Int?

    // Explicit CodingKeys for CharacterStats to be absolutely sure
    enum CodingKeys: String, CodingKey {
        case strength
        case dexterity
        case constitution
        case intelligence
        case wisdom
        case charisma
    }

    public init(strength: Int? = nil, dexterity: Int? = nil, constitution: Int? = nil,
                intelligence: Int? = nil, wisdom: Int? = nil, charisma: Int? = nil) {
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma
    }
}

// Corresponds to TypeScript 'Character'
public struct Character: Identifiable, Codable, Sendable {
    public var id: Int
    public var ownerID: Int?
    public var name: String
    public var description: String?
    public var appearanceDescription: String?
    public var imageURLs: [String]?
    public var video_clip_urls: [String]?
    public var notesForLLM: String?
    public var stats: CharacterStats?
    public var exportFormatPreference: String?
    public var createdAt: Date?
    public var modifiedAt: Date?
    public var campaignIDs: [Int]?
    public var selectedLLMId: String?
    public var temperature: Double?

    enum CodingKeys: String, CodingKey {
        case id
        case ownerID = "owner_id"
        case name
        case description
        case appearanceDescription = "appearance_description"
        case imageURLs = "image_urls"
        case video_clip_urls = "video_clip_urls"
        case notesForLLM = "notes_for_llm"
        case stats
        case exportFormatPreference = "export_format_preference"
        case createdAt = "created_at"
        case modifiedAt = "modified_at"
        case campaignIDs = "campaign_ids"
        case selectedLLMId = "selected_llm_id"
        case temperature
    }

    // Custom init(from: Decoder) is removed.
    // Swift will synthesize Codable conformance using the explicit CodingKeys defined in the Character struct.
    // The CharacterStats struct also uses synthesized Codable conformance with its explicit CodingKeys.

    // Memberwise initializer - keep for non-Codable instantiation if needed, or for tests/previews
    public init(id: Int,
                ownerID: Int? = nil,
                name: String,
                description: String? = nil,
                appearanceDescription: String? = nil,
                imageURLs: [String]? = nil,
                video_clip_urls: [String]? = nil,
                notesForLLM: String? = nil,
                stats: CharacterStats? = nil,
                exportFormatPreference: String? = nil,
                createdAt: Date? = nil,
                modifiedAt: Date? = nil,
                campaignIDs: [Int]? = nil,
                selectedLLMId: String? = nil,
                temperature: Double? = nil) {
        self.id = id
        self.ownerID = ownerID
        self.name = name
        self.description = description
        self.appearanceDescription = appearanceDescription
        self.imageURLs = imageURLs
        self.video_clip_urls = video_clip_urls
        self.notesForLLM = notesForLLM
        self.stats = stats
        self.exportFormatPreference = exportFormatPreference
        self.createdAt = createdAt
        self.modifiedAt = modifiedAt
        self.campaignIDs = campaignIDs
        self.selectedLLMId = selectedLLMId
        self.temperature = temperature
    }

    // Convenience to update modification time
    public mutating func markAsModified() {
        self.modifiedAt = Date()
    }
}
