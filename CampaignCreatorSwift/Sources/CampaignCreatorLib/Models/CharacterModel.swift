import Foundation

// Corresponds to TypeScript 'CharacterStats'
public struct CharacterStats: Codable, Sendable {
    public var strength: Int?
    public var dexterity: Int?
    public var constitution: Int?
    public var intelligence: Int?
    public var wisdom: Int?
    public var charisma: Int?

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
    public var id: Int // Changed from UUID to Int
    // public var ownerId: UUID? // If we need to associate with a user someday
    public var name: String
    public var description: String?
    public var appearanceDescription: String?
    public var imageURLs: [String]?
    public var notesForLLM: String?
    public var stats: CharacterStats?
    public var exportFormatPreference: String? // e.g., "JSON", "Markdown"

    // Metadata
    public var createdAt: Date? // Changed to optional
    public var modifiedAt: Date? // Changed to optional
    // public var customSections: [CustomSection]? // REMOVED

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case appearanceDescription = "appearance_description"
        case imageURLs = "image_urls" // Explicitly map to snake_case
        case notesForLLM = "notes_for_llm"
        case stats
        case exportFormatPreference = "export_format_preference"
        case createdAt = "created_at"
        case modifiedAt = "modified_at"
    }

    // Custom init(from decoder: Decoder) for detailed logging
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(Int.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        description = try container.decodeIfPresent(String.self, forKey: .description)

        appearanceDescription = try container.decodeIfPresent(String.self, forKey: .appearanceDescription)
        print("[DECODE_DEBUG CharacterModel] Decoded appearanceDescription for ID \(id): '\(appearanceDescription ?? "nil")'")

        imageURLs = try container.decodeIfPresent([String].self, forKey: .imageURLs)

        notesForLLM = try container.decodeIfPresent(String.self, forKey: .notesForLLM)
        print("[DECODE_DEBUG CharacterModel] Decoded notesForLLM for ID \(id): '\(notesForLLM ?? "nil")'")

        stats = try container.decodeIfPresent(CharacterStats.self, forKey: .stats)
        exportFormatPreference = try container.decodeIfPresent(String.self, forKey: .exportFormatPreference)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt)
        modifiedAt = try container.decodeIfPresent(Date.self, forKey: .modifiedAt)
    }

    // Original memberwise initializer - keep for non-Codable instantiation if needed, or for tests
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

// CustomSection struct REMOVED from here (will be added to CampaignModel.swift)
