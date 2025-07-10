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
    public var name: String
    public var description: String?
    public var appearanceDescription: String?
    public var imageURLs: [String]?
    public var notesForLLM: String?
    public var stats: CharacterStats?
    public var exportFormatPreference: String?
    public var createdAt: Date?
    public var modifiedAt: Date?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case appearanceDescription = "appearance_description"
        case imageURLs = "image_urls"
        case notesForLLM = "notes_for_llm"
        case stats
        case exportFormatPreference = "export_format_preference"
        case createdAt = "created_at"
        case modifiedAt = "modified_at"
        // owner_id is in the JSON but not in the Swift struct, so it's not included here.
        // If it were needed in the struct, it would be: case ownerId = "owner_id"
    }

    // Custom init(from: Decoder) is removed.
    // Swift will synthesize Codable conformance using the explicit CodingKeys defined in the Character struct.
    // The CharacterStats struct also uses synthesized Codable conformance with its explicit CodingKeys.

    // Memberwise initializer - keep for non-Codable instantiation if needed, or for tests/previews
    public init(id: Int,
                name: String,
                description: String? = nil,
                appearanceDescription: String? = nil,
                imageURLs: [String]? = nil,
                notesForLLM: String? = nil,
                stats: CharacterStats? = nil,
                exportFormatPreference: String? = nil,
                createdAt: Date? = nil,
                modifiedAt: Date? = nil) {
        self.id = id
        self.name = name
        self.description = description
        self.appearanceDescription = appearanceDescription
        self.imageURLs = imageURLs
        self.notesForLLM = notesForLLM
        self.stats = stats
        self.exportFormatPreference = exportFormatPreference
        self.createdAt = createdAt
        self.modifiedAt = modifiedAt
    }

    // Convenience to update modification time
    public mutating func markAsModified() {
        self.modifiedAt = Date()
    }
}
