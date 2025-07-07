import Foundation

// Corresponds to TypeScript 'TOCEntry'
public struct TOCEntry: Identifiable, Codable, Sendable {
    public var id: Int // Changed from UUID to Int
    public var title: String
    public var type: String // e.g., "Introduction", "Chapter 1", "Appendix"

    public init(id: Int, title: String, type: String) { // Changed id from UUID to Int, removed default
        self.id = id
        self.title = title
        self.type = type
    }
}

// New struct for campaign custom sections
public struct CampaignCustomSection: Identifiable, Codable, Sendable {
    public var id: UUID
    public var title: String
    public var content: String
    public var type: String? // ADDED type field
    // public var order: Int // Optional: if explicit ordering is needed beyond array order

    public init(id: UUID = UUID(), title: String, content: String, type: String? = "Generic" /*, order: Int = 0*/) { // ADDED type, default "Generic"
        self.id = id
        self.title = title
        self.content = content
        self.type = type // ADDED
        // self.order = order
    }
}

// Corresponds to TypeScript 'CampaignSection'
public struct CampaignSection: Identifiable, Codable, Sendable {
    public var id: Int // Changed from UUID to Int
    public var title: String?
    public var content: String
    public var order: Int
    // public var campaign_id: UUID // Link back to the Campaign, if sections are stored separately
    public var type: String? // e.g., "Narrative", "Location", "NPC"

    public init(id: Int, title: String? = nil, content: String, order: Int, type: String? = nil) { // Changed id from UUID to Int, removed default
        self.id = id
        self.title = title
        self.content = content
        self.order = order
        self.type = type
    }
}

// This struct will represent the Campaign. We are evolving the old 'Document' into this.
public struct Campaign: Identifiable, Codable, Sendable {
    public var id: Int // Changed from UUID to Int
    public var title: String
    public var initialUserPrompt: String?
    public var concept: String?
    public var displayTOC: [TOCEntry]? // Table of Contents
    public var sections: [CampaignSection] // Campaign sections

    // Metadata from React app's Campaign
    public var badgeImageURL: String?
    public var thematicImageURL: String?
    public var thematicImagePrompt: String?
    public var selectedLLMId: String?
    public var temperature: Double? // Changed from Int to Double for more precision
    public var moodBoardImageURLs: [String]?

    // Theme properties
    public var themePrimaryColor: String?
    public var themeSecondaryColor: String?
    public var themeBackgroundColor: String?
    public var themeTextColor: String?
    public var themeFontFamily: String?
    public var themeBackgroundImageURL: String?
    public var themeBackgroundImageOpacity: Double?

    public var fileURL: URL? // Keep if direct file association is needed for saving/loading whole campaign
    public var createdAt: Date? // Changed to optional
    public var modifiedAt: Date? // Changed to optional

    // Linking characters (IDs for now, actual Character objects can be resolved by CampaignCreator)
    public var linkedCharacterIDs: [UUID]?
    public var customSections: [CampaignCustomSection]? // <<<< ADDED

    public init(id: Int, // Changed from UUID = UUID()
                title: String = "Untitled Campaign",
                initialUserPrompt: String? = nil,
                concept: String? = nil,
                displayTOC: [TOCEntry]? = nil,
                sections: [CampaignSection] = [],
                badgeImageURL: String? = nil,
                thematicImageURL: String? = nil,
                thematicImagePrompt: String? = nil,
                selectedLLMId: String? = nil,
                temperature: Double? = 0.7,
                moodBoardImageURLs: [String]? = nil,
                themePrimaryColor: String? = nil,
                themeSecondaryColor: String? = nil,
                themeBackgroundColor: String? = nil,
                themeTextColor: String? = nil,
                themeFontFamily: String? = nil,
                themeBackgroundImageURL: String? = nil,
                themeBackgroundImageOpacity: Double? = nil,
                fileURL: URL? = nil,
                createdAt: Date? = nil, // Changed to optional, default nil
                modifiedAt: Date? = nil, // Changed to optional, default nil
                linkedCharacterIDs: [UUID]? = nil,
                customSections: [CampaignCustomSection]? = nil) { // <<<< ADDED
        self.id = id
        self.title = title
        self.initialUserPrompt = initialUserPrompt
        self.concept = concept
        self.displayTOC = displayTOC
        self.sections = sections
        self.badgeImageURL = badgeImageURL
        self.thematicImageURL = thematicImageURL
        self.thematicImagePrompt = thematicImagePrompt
        self.selectedLLMId = selectedLLMId
        self.temperature = temperature
        self.moodBoardImageURLs = moodBoardImageURLs
        self.themePrimaryColor = themePrimaryColor
        self.themeSecondaryColor = themeSecondaryColor
        self.themeBackgroundColor = themeBackgroundColor
        self.themeTextColor = themeTextColor
        self.themeFontFamily = themeFontFamily
        self.themeBackgroundImageURL = themeBackgroundImageURL
        self.themeBackgroundImageOpacity = themeBackgroundImageOpacity
        self.fileURL = fileURL
        self.createdAt = createdAt
        self.modifiedAt = modifiedAt
        self.linkedCharacterIDs = linkedCharacterIDs
        self.customSections = customSections // <<<< ADDED
    }

    // Word count can be a computed property, summing word counts of all sections
    public var wordCount: Int {
        sections.reduce(0) { $0 + $1.content.components(separatedBy: .whitespacesAndNewlines).filter { !$0.isEmpty }.count }
    }

    // Convenience to update modification time
    public mutating func markAsModified() {
        self.modifiedAt = Date()
    }

    // Placeholder for save/load logic if we treat the whole Campaign as one JSON file
    public func save(to url: URL) throws {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(self)
        try data.write(to: url, options: .atomic)
    }

    public static func load(from url: URL) throws -> Campaign {
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode(Campaign.self, from: data)
    }
}
