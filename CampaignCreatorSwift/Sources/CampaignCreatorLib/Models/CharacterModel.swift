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
    public var customSections: [CustomSection]? // Added for custom sections

    public init(id: Int, // Changed from UUID to Int, removed default
                name: String,
                description: String? = nil,
                appearanceDescription: String? = nil,
                imageURLs: [String]? = nil,
                notesForLLM: String? = nil,
                stats: CharacterStats? = nil,
                exportFormatPreference: String? = nil,
                customSections: [CustomSection]? = nil, // Added
                createdAt: Date? = nil, // Changed to optional, default nil
                modifiedAt: Date? = nil) { // Changed to optional, default nil
        self.id = id
        self.name = name
        self.description = description
        self.appearanceDescription = appearanceDescription
        self.imageURLs = imageURLs
        self.notesForLLM = notesForLLM
        self.stats = stats
        self.exportFormatPreference = exportFormatPreference
        self.customSections = customSections // Added
        self.createdAt = createdAt
        self.modifiedAt = modifiedAt
    }

    // Convenience to update modification time
    public mutating func markAsModified() {
        self.modifiedAt = Date()
    }
}

// New struct for custom sections
public struct CustomSection: Identifiable, Codable, Sendable {
    public var id: UUID
    public var title: String
    public var content: String

    public init(id: UUID = UUID(), title: String, content: String) {
        self.id = id
        self.title = title
        self.content = content
    }
}
